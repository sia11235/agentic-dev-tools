from __future__ import annotations

import sys

import click
from dotenv import find_dotenv, load_dotenv

from .review.diff import GitError, get_diff
from .review.report import render_json, render_markdown, render_text
from .review.reviewer import DEFAULT_MODEL, ReviewError, review_diff

load_dotenv(find_dotenv(usecwd=True))


@click.group()
def main() -> None:
    """Agentic dev tools."""


@main.command()
@click.option("--base", default=None, help="Base branch to diff against (e.g. main). Defaults to local changes only.")
@click.option("--staged", is_flag=True, help="Only review staged changes.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
)
@click.option("--model", default=DEFAULT_MODEL, show_default=True)
@click.option(
    "--fail-on",
    type=click.Choice(["blocker", "warning", "nit", "never"]),
    default="blocker",
    show_default=True,
    help="Exit non-zero if a finding at or above this severity is found.",
)
def review(base: str | None, staged: bool, output_format: str, model: str, fail_on: str) -> None:
    """Review the current diff with Claude before you open a PR."""
    try:
        diff = get_diff(base=base, staged_only=staged)
    except GitError as e:
        click.echo(f"git error: {e}", err=True)
        sys.exit(2)

    if not diff.strip():
        click.echo("No changes to review.")
        return

    try:
        findings = review_diff(diff, model=model)
    except ReviewError as e:
        click.echo(f"review error: {e}", err=True)
        sys.exit(2)

    renderers = {"text": render_text, "json": render_json, "markdown": render_markdown}
    click.echo(renderers[output_format](findings))

    if fail_on == "never":
        return
    severity_rank = {"blocker": 0, "warning": 1, "nit": 2}
    threshold = severity_rank[fail_on]
    if any(severity_rank.get(f.severity, 99) <= threshold for f in findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
