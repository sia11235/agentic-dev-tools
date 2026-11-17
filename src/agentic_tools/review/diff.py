"""Git diff extraction for the review agent."""

from __future__ import annotations

import subprocess


class GitError(RuntimeError):
    pass


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def get_diff(
    base: str | None = None,
    staged_only: bool = False,
    commit: str | None = None,
    rev_range: str | None = None,
) -> str:
    """Return a unified diff to review.

    - commit given: just that commit's changes against its first parent
      (merge commits show what the merge brought in).
    - rev_range given: passed straight to `git diff`, e.g. `abc123..def456`
      or `origin/develop...HEAD` (three dots = since the merge-base).
    - base given: diff between the merge-base of `base` and HEAD, and the
      working tree (so it includes committed branch work plus any local
      edits) — i.e. "everything this branch would add".
    - staged_only: only `git diff --cached` (what `git commit` would record).
    - otherwise: all uncommitted changes (staged + unstaged) against HEAD.
    """
    if sum(bool(x) for x in (base, staged_only, commit, rev_range)) > 1:
        raise GitError("use only one of --base, --staged, --commit, --range")
    if commit:
        return _run_git(["diff", f"{commit}^1", commit])
    if rev_range:
        if ".." not in rev_range:
            raise GitError(f"--range must look like A..B or A...B, got {rev_range!r}")
        return _run_git(["diff", rev_range])
    if base:
        return _run_git(["diff", f"{base}...HEAD"]) + _run_git(["diff", "HEAD"])
    if staged_only:
        return _run_git(["diff", "--cached"])
    return _run_git(["diff", "HEAD"])


def repo_root() -> str:
    return _run_git(["rev-parse", "--show-toplevel"]).strip()
