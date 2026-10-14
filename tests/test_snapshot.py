import hashlib
import subprocess

import pytest

from snapshot import snapshot

GIT_ID = ["-c", "user.name=test", "-c", "user.email=test@example.invalid"]
AREAS = ("api", "guide", "style-guide")
EXCLUDED = ("api/index.md", "api/options-state.md")


def git(cwd, *args):
    return subprocess.run(
        ["git", *GIT_ID, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def origin(tmp_path):
    repo = tmp_path / "origin"
    for rel, text in {
        "src/api/x.md": "# X {#x}\n",
        "src/api/index.md": "# Index {#index}\n",
        "src/api/options-state.md": "# Opt {#opt}\n",
        "src/guide/a.md": "# A {#a}\n",
        "src/guide/sub/b.md": "# B {#b}\n",
        "src/guide/img.png": "binary",
        "src/style-guide/s.md": "# S {#s}\n",
        "src/tutorial/t.md": "# T {#t}\n",
    }.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo.parent, "init", "-q", str(repo))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    return repo, git(repo, "rev-parse", "HEAD")


def run(repo, sha, out, info, **kw):
    kw = {"areas": AREAS, "excluded": EXCLUDED, **kw}
    return snapshot(repo.as_uri(), sha, out, info, **kw)


def test_snapshot_copies_areas_minus_exclusions_and_writes_checksums(origin, tmp_path):
    repo, sha = origin
    out = tmp_path / "raw"
    (out / "guide").mkdir(parents=True)
    (out / ".gitkeep").write_text("")
    (out / "guide" / "stale.md").write_text("old")
    info = out / "SNAPSHOT.txt"

    assert run(repo, sha, out, info) == 4

    copied = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.md"))
    assert copied == ["api/x.md", "guide/a.md", "guide/sub/b.md", "style-guide/s.md"]
    assert (out / ".gitkeep").exists()
    text = info.read_text(encoding="utf-8")
    assert f"commit: {sha}" in text and "files: 4" in text
    assert "areas: api, guide, style-guide" in text
    assert "excluded: api/index.md, api/options-state.md" in text
    digest = hashlib.sha256((out / "guide" / "a.md").read_bytes()).hexdigest()
    assert f"{digest}  guide/a.md" in text


def test_snapshot_rejects_an_exclusion_missing_at_the_commit(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="excluded files not in the checkout"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt", excluded=("api/typo.md",))


def test_snapshot_rejects_an_exclusion_outside_the_areas(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(ValueError, match="outside the areas"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt", excluded=("tutorial/t.md",))


def test_snapshot_rejects_a_missing_area(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="src/missing"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt", areas=("missing",), excluded=())


def test_snapshot_bytes_ignore_users_autocrlf(origin, tmp_path, monkeypatch):
    repo, sha = origin
    config = tmp_path / "gitconfig"
    config.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    out = tmp_path / "raw"

    run(repo, sha, out, out / "SNAPSHOT.txt")

    assert (out / "guide" / "a.md").read_bytes() == b"# A {#a}\n"


def test_snapshot_rejects_unknown_commit(origin, tmp_path):
    repo, _ = origin
    with pytest.raises(RuntimeError, match="git fetch"):
        run(repo, "0" * 40, tmp_path / "raw", tmp_path / "SNAPSHOT.txt")


def test_snapshot_keeps_an_existing_matching_record(origin, tmp_path):
    repo, sha = origin
    out, info = tmp_path / "raw", tmp_path / "corpus_snapshot.txt"
    run(repo, sha, out, info)
    recorded = info.read_text(encoding="utf-8").replace(
        "snapshot_date: ", "snapshot_date: 2000-01-01 # "
    )
    info.write_text(recorded, encoding="utf-8")

    run(repo, sha, out, info)

    assert info.read_text(encoding="utf-8") == recorded


def test_snapshot_rejects_files_that_differ_from_the_record(origin, tmp_path):
    repo, sha = origin
    out, info = tmp_path / "raw", tmp_path / "corpus_snapshot.txt"
    run(repo, sha, out, info)
    info.write_text(
        info.read_text(encoding="utf-8").replace("guide/a.md", "guide/z.md"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="does not match the record"):
        run(repo, sha, out, info)
