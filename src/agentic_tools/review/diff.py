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


def get_diff(base: str | None = None, staged_only: bool = False) -> str:
    """Return a unified diff to review.

    - base given: diff between the merge-base of `base` and HEAD, and the
      working tree (so it includes committed branch work plus any local
      edits) — i.e. "everything this branch would add".
    - staged_only: only `git diff --cached` (what `git commit` would record).
    - otherwise: all uncommitted changes (staged + unstaged) against HEAD.
    """
    if base:
        return _run_git(["diff", f"{base}...HEAD"]) + _run_git(["diff", "HEAD"])
    if staged_only:
        return _run_git(["diff", "--cached"])
    return _run_git(["diff", "HEAD"])


def repo_root() -> str:
    return _run_git(["rev-parse", "--show-toplevel"]).strip()
