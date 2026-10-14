"""Create the corpus snapshot (ADR 0019, ADR 0025).

Fetches config.VUE_DOCS_COMMIT of config.VUE_DOCS_REPO_URL (shallow), copies every Markdown file
of config.VUE_DOCS_AREAS below config.VUE_DOCS_ROOT, minus config.VUE_DOCS_EXCLUDED, to
data/raw/vue_docs_snapshot/<area>/ and writes docs/corpus_snapshot.txt (versioned) with
repository, commit, dates, areas, exclusions and a sha256 per file.
"""

import hashlib
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from config import (
    DATA_RAW,
    SNAPSHOT_INFO_FILE,
    VUE_DOCS_AREAS,
    VUE_DOCS_COMMIT,
    VUE_DOCS_EXCLUDED,
    VUE_DOCS_REPO_URL,
    VUE_DOCS_ROOT,
)

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


def copy_markdown(
    src_root: Path, out_dir: Path, areas: tuple[str, ...], excluded: tuple[str, ...]
) -> list[Path]:
    """Replace out_dir/<area> with the *.md files below src_root/<area>, minus `excluded`
    (paths relative to src_root); return the copied paths relative to out_dir.

    Everything is checked before anything is copied: every exclusion must lie in an area, exist
    in the checkout and remove exactly one Markdown file, so the list cannot rot silently.
    """
    outside = [e for e in excluded if e.split("/", 1)[0] not in areas]
    if outside:
        raise ValueError(f"excluded files outside the areas {list(areas)}: {outside}")
    missing = [e for e in excluded if not (src_root / e).is_file()]
    if missing:
        raise FileNotFoundError(f"excluded files not in the checkout: {missing}")
    selected: dict[str, list[Path]] = {}
    matched: set[str] = set()
    for area in areas:
        src_dir = src_root / area
        if not src_dir.is_dir():
            raise FileNotFoundError(f"{src_dir} not found in the checkout")
        files = []
        for p in sorted(src_dir.rglob("*.md")):
            rel = p.relative_to(src_root).as_posix()
            if rel in excluded:
                matched.add(rel)
            else:
                files.append(p)
        if not files:
            raise FileNotFoundError(f"no Markdown files below {src_dir}")
        selected[area] = files
    unmatched = [e for e in excluded if e not in matched]
    if unmatched:
        raise ValueError(f"exclusions that match no Markdown file: {unmatched}")
    copied: list[Path] = []
    for area, files in selected.items():
        target = out_dir / area
        if target.exists():
            shutil.rmtree(target)
        for src in files:
            dst = out_dir / src.relative_to(src_root)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst.relative_to(out_dir))
    return sorted(copied, key=lambda p: p.as_posix())


def _checksums(lines: list[str]) -> dict[str, str]:
    """File path -> SHA-256 from the checksum lines of a snapshot record."""
    pairs = (line.split("  ", 1) for line in lines if CHECKSUM_LINE_RE.match(line))
    return {path: digest for digest, path in pairs}


def snapshot(
    repo_url: str = VUE_DOCS_REPO_URL,
    commit: str = VUE_DOCS_COMMIT,
    out_dir: Path = DATA_RAW,
    info_file: Path = SNAPSHOT_INFO_FILE,
    root: str = VUE_DOCS_ROOT,
    areas: tuple[str, ...] = VUE_DOCS_AREAS,
    excluded: tuple[str, ...] = VUE_DOCS_EXCLUDED,
) -> int:
    """Fetch the pinned commit, copy the Markdown files of the areas, then write or verify the
    record."""
    if shutil.which("git") is None:
        raise RuntimeError("git is required to create the snapshot")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp)
        commit_date = fetch_commit(repo_url, commit, checkout)
        files = copy_markdown(checkout / root, out_dir, areas, excluded)
    lines = [
        f"repository: {repo_url}",
        f"commit: {commit}",
        f"commit_date: {commit_date}",
        f"snapshot_date: {date.today().isoformat()}",
        f"areas: {', '.join(areas)}",
        f"excluded: {', '.join(excluded)}",
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
