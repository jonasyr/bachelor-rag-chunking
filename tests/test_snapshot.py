import hashlib
import subprocess

import pytest

from snapshot import snapshot

GIT_ID = ["-c", "user.name=test", "-c", "user.email=test@example.invalid"]


def git(cwd, *args):
    return subprocess.run(
        ["git", *GIT_ID, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def origin(tmp_path):
    repo = tmp_path / "origin"
    for rel, text in {
        "src/guide/a.md": "# A {#a}\n",
        "src/guide/sub/b.md": "# B {#b}\n",
        "src/guide/img.png": "binary",
        "src/other.md": "# Other {#other}\n",
    }.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo.parent, "init", "-q", str(repo))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    return repo, git(repo, "rev-parse", "HEAD")


def test_snapshot_copies_guide_markdown_and_writes_checksums(origin, tmp_path):
    repo, sha = origin
    out = tmp_path / "raw"
    (out / "guide").mkdir(parents=True)
    (out / ".gitkeep").write_text("")
    (out / "guide" / "stale.md").write_text("old")
    info = out / "SNAPSHOT.txt"

    assert snapshot(repo.as_uri(), sha, "src/guide", out, info) == 2

    copied = sorted(
        p.relative_to(out).as_posix() for p in (out / "guide").rglob("*") if p.is_file()
    )
    assert copied == [
        "guide/a.md",
        "guide/sub/b.md",
    ]
    assert (out / ".gitkeep").exists()
    text = info.read_text(encoding="utf-8")
    assert f"commit: {sha}" in text
    assert "files: 2" in text
    digest = hashlib.sha256((out / "guide" / "a.md").read_bytes()).hexdigest()
    assert f"{digest}  guide/a.md" in text


def test_snapshot_bytes_ignore_users_autocrlf(origin, tmp_path, monkeypatch):
    repo, sha = origin
    config = tmp_path / "gitconfig"
    config.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    out = tmp_path / "raw"

    snapshot(repo.as_uri(), sha, "src/guide", out, out / "SNAPSHOT.txt")

    assert (out / "guide" / "a.md").read_bytes() == b"# A {#a}\n"


def test_snapshot_rejects_unknown_commit(origin, tmp_path):
    repo, _ = origin
    with pytest.raises(RuntimeError, match="git fetch"):
        snapshot(repo.as_uri(), "0" * 40, "src/guide", tmp_path / "raw", tmp_path / "SNAPSHOT.txt")


def test_snapshot_rejects_missing_subdir(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="docs/missing"):
        snapshot(repo.as_uri(), sha, "docs/missing", tmp_path / "raw", tmp_path / "SNAPSHOT.txt")
