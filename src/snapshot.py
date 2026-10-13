"""Create the corpus snapshot (ADR 0019).

Fetches config.VUE_DOCS_COMMIT of config.VUE_DOCS_REPO_URL (shallow), replaces
data/raw/vue_docs_snapshot/guide/ with every Markdown file below config.VUE_DOCS_SUBDIR and
writes docs/corpus_snapshot.txt (versioned) with repository, commit, dates and a sha256 per file.
"""

import hashlib
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from config import (
    DATA_RAW,
    SNAPSHOT_INFO_FILE,
    SNAPSHOT_SUBDIR,
    VUE_DOCS_COMMIT,
    VUE_DOCS_REPO_URL,
    VUE_DOCS_SUBDIR,
)

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


def copy_markdown(src_dir: Path, out_dir: Path) -> list[Path]:
    """Replace out_dir/guide with the *.md files below src_dir; return paths relative to out_dir."""
    if not src_dir.is_dir():
        raise FileNotFoundError(f"{src_dir} not found in the checkout")
    target = out_dir / SNAPSHOT_SUBDIR
    if target.exists():
        shutil.rmtree(target)
    copied = []
    for src in sorted(src_dir.rglob("*.md")):
        dst = target / src.relative_to(src_dir)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst.relative_to(out_dir))
    if not copied:
        raise FileNotFoundError(f"no Markdown files below {src_dir}")
    return copied


def snapshot(
    repo_url: str = VUE_DOCS_REPO_URL,
    commit: str = VUE_DOCS_COMMIT,
    subdir: str = VUE_DOCS_SUBDIR,
    out_dir: Path = DATA_RAW,
    info_file: Path = SNAPSHOT_INFO_FILE,
) -> int:
    """Fetch the pinned commit, copy its Markdown files, write the record; return the file count."""
    if shutil.which("git") is None:
        raise RuntimeError("git is required to create the snapshot")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp)
        commit_date = fetch_commit(repo_url, commit, checkout)
        files = copy_markdown(checkout / subdir, out_dir)
    lines = [
        f"repository: {repo_url}",
        f"commit: {commit}",
        f"commit_date: {commit_date}",
        f"snapshot_date: {date.today().isoformat()}",
        f"files: {len(files)}",
        "",
    ]
    lines += [
        f"{hashlib.sha256((out_dir / f).read_bytes()).hexdigest()}  {f.as_posix()}" for f in files
    ]
    info_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(files)


if __name__ == "__main__":
    print(f"{snapshot()} files -> {DATA_RAW / SNAPSHOT_SUBDIR}")
