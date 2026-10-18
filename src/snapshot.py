"""Create the corpus snapshot (ADR 0019, ADR 0038).

Fetches config.CORPUS_COMMIT of config.CORPUS_REPO_URL (shallow), copies every page (*.mdx) below
config.CORPUS_ROOT plus config.CORPUS_SUPPORT_FILES (navigation, provider snippet) to
data/raw/e2e_docs_snapshot/ (same relative paths) and writes docs/corpus_snapshot.txt
(versioned) with repository, commit, dates, root and a sha256 per file. The pages
must equal the navigation's pages.
"""

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from config import (
    CORPUS_COMMIT,
    CORPUS_NAV_FILE,
    CORPUS_PAGE_SUFFIX,
    CORPUS_REPO_URL,
    CORPUS_ROOT,
    CORPUS_SUPPORT_FILES,
    DATA_RAW,
    SNAPSHOT_INFO_FILE,
)
from mdx import nav_areas

CHECKSUM_LINE_RE = re.compile(r"^[0-9a-f]{64}  ")
# Byte-identical checkout on every machine: ignore the user's line-ending settings.
GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf"]


def _git(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git {' '.join(args)} failed: {e.stderr.strip()}") from e
    return result.stdout.strip()


def fetch_commit(repo_url: str, commit: str, dest: Path) -> str:
    """Check out commit of repo_url into dest (depth 1); return its committer date (ISO 8601)."""
    _git(dest, "init", "-q")
    _git(dest, "fetch", "-q", "--depth", "1", repo_url, commit)
    _git(dest, "checkout", "-q", "FETCH_HEAD")
    head = _git(dest, "rev-parse", "HEAD")
    if head != commit:
        raise RuntimeError(f"fetched {head}, expected {commit}")
    return _git(dest, "show", "-s", "--format=%cI", "HEAD")


def copy_corpus(
    src_root: Path, out_dir: Path, suffix: str, nav_file: str, support: tuple[str, ...]
) -> list[Path]:
    """Replace the contents of out_dir (except dotfiles at its top, e.g. .gitkeep) with the pages
    (*suffix below src_root) and the support files; return the copied paths relative to out_dir.

    Everything is checked before anything is copied: the support files exist and the pages equal
    the navigation's pages, so neither list can drift silently.
    """
    missing = [s for s in support if not (src_root / s).is_file()]
    if missing:
        raise FileNotFoundError(f"support files not in the checkout: {missing}")
    pages = sorted(p.relative_to(src_root).as_posix() for p in src_root.rglob(f"*{suffix}"))
    found = {p.removesuffix(suffix) for p in pages}
    listed = set(nav_areas(json.loads((src_root / nav_file).read_text(encoding="utf-8"))))
    if found != listed:
        raise ValueError(
            f"pages and navigation differ: only pages {sorted(found - listed)}, "
            f"only navigation {sorted(listed - found)}"
        )
    if out_dir.exists():
        for child in out_dir.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    copied: list[Path] = []
    for rel in [*pages, *support]:
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_root / rel, dst)
        copied.append(Path(rel))
    return sorted(copied, key=lambda p: p.as_posix())


def _checksums(lines: list[str]) -> dict[str, str]:
    """File path -> SHA-256 from the checksum lines of a snapshot record."""
    pairs = (line.split("  ", 1) for line in lines if CHECKSUM_LINE_RE.match(line))
    return {path: digest for digest, path in pairs}


def snapshot(
    repo_url: str = CORPUS_REPO_URL,
    commit: str = CORPUS_COMMIT,
    out_dir: Path = DATA_RAW,
    info_file: Path = SNAPSHOT_INFO_FILE,
    root: str = CORPUS_ROOT,
    suffix: str = CORPUS_PAGE_SUFFIX,
    nav_file: str = CORPUS_NAV_FILE,
    support: tuple[str, ...] = CORPUS_SUPPORT_FILES,
) -> int:
    """Fetch the pinned commit, copy pages and support files, then write or verify the record."""
    if shutil.which("git") is None:
        raise RuntimeError("git is required to create the snapshot")
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp)
        commit_date = fetch_commit(repo_url, commit, checkout)
        files = copy_corpus(checkout / root, out_dir, suffix, nav_file, support)
    lines = [
        f"repository: {repo_url}",
        f"commit: {commit}",
        f"commit_date: {commit_date}",
        f"snapshot_date: {date.today().isoformat()}",
        f"root: {root}",
        f"files: {len(files)}",
        "",
    ]
    lines += [
        f"{hashlib.sha256((out_dir / f).read_bytes()).hexdigest()}  {f.as_posix()}" for f in files
    ]
    if info_file.exists():
        # The versioned record is the reference: verify against it instead of rewriting it.
        recorded = info_file.read_text(encoding="utf-8").splitlines()
        if f"commit: {commit}" not in recorded or _checksums(recorded) != _checksums(lines):
            raise ValueError(
                f"fetched snapshot does not match the record {info_file}; "
                "delete the record to store a new snapshot"
            )
        return len(files)
    info_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(files)


if __name__ == "__main__":
    print(f"{snapshot()} files -> {DATA_RAW}")
