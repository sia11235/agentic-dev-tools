import subprocess

import pytest

from agentic_tools.review import diff as diff_mod
from agentic_tools.review.diff import GitError, get_diff


@pytest.fixture
def repo(tmp_path, monkeypatch):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "a.txt").write_text("one\n")
    git("add", ".")
    git("commit", "-qm", "first")
    (tmp_path / "a.txt").write_text("one\ntwo\n")
    git("commit", "-qam", "second")
    (tmp_path / "b.txt").write_text("b\n")
    git("add", ".")
    git("commit", "-qm", "third")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_commit_shows_only_that_commit(repo):
    out = get_diff(commit="HEAD~1")
    assert "+two" in out
    assert "b.txt" not in out


def test_range_two_dots(repo):
    out = get_diff(rev_range="HEAD~2..HEAD")
    assert "+two" in out and "b.txt" in out


def test_range_must_contain_dots(repo):
    with pytest.raises(GitError):
        get_diff(rev_range="HEAD~1")


def test_options_are_mutually_exclusive():
    with pytest.raises(GitError):
        get_diff(base="main", commit="abc")


def test_commit_uses_first_parent(monkeypatch):
    calls = []
    monkeypatch.setattr(diff_mod, "_run_git", lambda args: calls.append(args) or "")
    get_diff(commit="6f59e93")
    assert calls == [["diff", "6f59e93^1", "6f59e93"]]
