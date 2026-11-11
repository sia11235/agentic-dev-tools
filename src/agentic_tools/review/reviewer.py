"""Calls Claude to review a diff and returns structured findings."""

from __future__ import annotations

import os

import anthropic

from .findings import Finding

DEFAULT_MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are a first-pass code reviewer. You review a git diff \
before a human sees it, so a human reviewer can start from a cleaner diff.

Focus on:
- correctness bugs (logic errors, off-by-one, wrong operator, unhandled edge case)
- missing or wrong error handling
- security issues (injection, secrets, unsafe deserialization, etc.)
- missing test coverage for non-trivial new logic
- unclear naming or structure that will confuse the next reader

Do not comment on:
- formatting/whitespace that a linter would catch
- style preferences with no concrete downside
- anything not actually in the diff

Only report findings you're confident about. Report nothing if the diff is clean —
an empty list is a valid and good outcome. Be concise: one or two sentences per finding."""

REPORT_FINDINGS_TOOL = {
    "name": "report_findings",
    "description": "Report the review findings for this diff.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "File path from the diff"},
                        "line": {
                            "type": ["integer", "null"],
                            "description": "Line number in the new file version, if applicable",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["blocker", "warning", "nit"],
                            "description": (
                                "blocker: must fix before merge. "
                                "warning: should fix. nit: optional improvement."
                            ),
                        },
                        "category": {
                            "type": "string",
                            "description": "e.g. correctness, security, error-handling, test-coverage, clarity",
                        },
                        "summary": {"type": "string", "description": "One-sentence statement of the issue"},
                        "detail": {"type": "string", "description": "Why it matters / how to fix, 1-2 sentences"},
                    },
                    "required": ["file", "severity", "category", "summary"],
                },
            },
        },
        "required": ["findings"],
    },
}


class ReviewError(RuntimeError):
    pass


def review_diff(diff: str, model: str = DEFAULT_MODEL) -> list[Finding]:
    if not diff.strip():
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ReviewError("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[REPORT_FINDINGS_TOOL],
        tool_choice={"type": "tool", "name": "report_findings"},
        messages=[
            {
                "role": "user",
                "content": f"Review this diff:\n\n```diff\n{diff}\n```",
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_findings":
            raw_findings = block.input.get("findings", [])
            return [Finding.from_dict(f) for f in raw_findings]

    raise ReviewError("Claude did not return a report_findings tool call")
