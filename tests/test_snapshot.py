import hashlib
import json
import subprocess

import pytest

from mdx import nav_areas
from snapshot import snapshot

GIT_ID = ["-c", "user.name=test", "-c", "user.email=test@example.invalid"]
NAV = {
    "navigation": {
        "tabs": [
            {"tab": "Documentation", "groups": [{"group": "Start", "pages": ["index", "ci/a"]}]},
            {"tab": "Examples", "pages": ["examples"]},
        ]
    }
}
SUPPORT = ("docs.json", "snippets/p.jsx")


def git(cwd, *args):
    return subprocess.run(
        ["git", *GIT_ID, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def make_origin(tmp_path, nav=NAV, extra=None):
    repo = tmp_path / "origin"
    files = {
        "docs/index.mdx": "---\ntitle: Home\n---\n",
        "docs/ci/a.mdx": "---\ntitle: A\n---\n",
        "docs/examples.mdx": "---\ntitle: Examples\n---\n",
        "docs/docs.json": json.dumps(nav),
        "docs/snippets/p.jsx": "export const P = 1;\n",
        "docs/images/x.png": "binary",
        "README.md": "# Repo\n",
        **(extra or {}),
    }
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo.parent, "init", "-q", str(repo))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    return repo, git(repo, "rev-parse", "HEAD")


@pytest.fixture
def origin(tmp_path):
    return make_origin(tmp_path)


def run(repo, sha, out, info, **kw):
    kw = {"root": "docs", "suffix": ".mdx", "nav_file": "docs.json", "support": SUPPORT, **kw}
    return snapshot(repo.as_uri(), sha, out, info, **kw)


def test_snapshot_copies_pages_and_support_files_and_writes_checksums(origin, tmp_path):
    repo, sha = origin
    out = tmp_path / "raw"
    (out / "old").mkdir(parents=True)
    (out / "old" / "stale.mdx").write_text("old")
    (out / ".gitkeep").write_text("")
    info = tmp_path / "corpus_snapshot.txt"

    assert run(repo, sha, out, info) == 5

    copied = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    assert copied == [
        ".gitkeep",
        "ci/a.mdx",
        "docs.json",
        "examples.mdx",
        "index.mdx",
        "snippets/p.jsx",
    ]
    text = info.read_text(encoding="utf-8")
    assert f"commit: {sha}" in text and "files: 5" in text and "root: docs" in text
    digest = hashlib.sha256((out / "ci" / "a.mdx").read_bytes()).hexdigest()
    assert f"{digest}  ci/a.mdx" in text
    assert "  snippets/p.jsx" in text


def test_snapshot_rejects_a_page_missing_from_the_navigation(tmp_path):
    repo, sha = make_origin(tmp_path, extra={"docs/draft.mdx": "---\ntitle: D\n---\n"})
    out = tmp_path / "raw"
    with pytest.raises(ValueError, match=r"only pages \['draft'\]"):
        run(repo, sha, out, tmp_path / "S.txt")
    assert not out.exists()  # checked before anything is copied


def test_snapshot_rejects_a_navigation_page_without_file(tmp_path):
    nav = json.loads(json.dumps(NAV))
    nav["navigation"]["tabs"][0]["groups"][0]["pages"].append("gone")
    repo, sha = make_origin(tmp_path, nav=nav)
    with pytest.raises(ValueError, match=r"only navigation \['gone'\]"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt")


def test_snapshot_rejects_a_missing_support_file(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="snippets/missing.jsx"):
        run(
            repo,
            sha,
            tmp_path / "raw",
            tmp_path / "S.txt",
            support=("docs.json", "snippets/missing.jsx"),
        )


def test_snapshot_bytes_ignore_users_autocrlf(origin, tmp_path, monkeypatch):
    repo, sha = origin
    config = tmp_path / "gitconfig"
    config.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    out = tmp_path / "raw"

    run(repo, sha, out, tmp_path / "S.txt")

    assert (out / "index.mdx").read_bytes() == b"---\ntitle: Home\n---\n"


def test_snapshot_rejects_unknown_commit(origin, tmp_path):
    repo, _ = origin
    with pytest.raises(RuntimeError, match="git fetch"):
        run(repo, "0" * 40, tmp_path / "raw", tmp_path / "S.txt")


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
        info.read_text(encoding="utf-8").replace("ci/a.mdx", "ci/z.mdx"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="does not match the record"):
        run(repo, sha, out, info)


def test_nav_areas_maps_pages_to_groups_and_direct_tab_pages_to_the_tab():
    assert nav_areas(NAV) == {"index": "Start", "ci/a": "Start", "examples": "Examples"}


def test_nav_areas_rejects_a_page_listed_twice():
    nav = {"navigation": {"tabs": [{"tab": "T", "groups": [{"group": "G", "pages": ["a", "a"]}]}]}}
    with pytest.raises(ValueError, match="listed twice"):
        nav_areas(nav)
