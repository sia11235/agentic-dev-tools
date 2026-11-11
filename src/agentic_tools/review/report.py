"""Render findings for terminal, JSON, or markdown (e.g. a PR comment)."""

from __future__ import annotations

import json

from .findings import Finding

SEVERITY_ORDER = {"blocker": 0, "warning": 1, "nit": 2}
SEVERITY_COLOR = {"blocker": "\033[31m", "warning": "\033[33m", "nit": "\033[36m"}
RESET = "\033[0m"


def _sorted(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.file, f.line or 0))


def render_text(findings: list[Finding]) -> str:
    if not findings:
        return "No findings. Diff looks clean.\n"

    lines = []
    for f in _sorted(findings):
        color = SEVERITY_COLOR.get(f.severity, "")
        location = f"{f.file}:{f.line}" if f.line else f.file
        lines.append(f"{color}[{f.severity.upper()}]{RESET} {location} ({f.category})")
        lines.append(f"  {f.summary}")
        if f.detail:
            lines.append(f"  {f.detail}")
        lines.append("")
    counts = {sev: sum(1 for f in findings if f.severity == sev) for sev in SEVERITY_ORDER}
    lines.append(
        f"{len(findings)} finding(s): "
        f"{counts.get('blocker', 0)} blocker, {counts.get('warning', 0)} warning, {counts.get('nit', 0)} nit"
    )
    return "\n".join(lines)


def render_json(findings: list[Finding]) -> str:
    return json.dumps([f.__dict__ for f in _sorted(findings)], indent=2)


def render_markdown(findings: list[Finding]) -> str:
    if not findings:
        return "**agentic-tools review:** no findings — diff looks clean."

    lines = ["**agentic-tools review:**", ""]
    for f in _sorted(findings):
        location = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
        lines.append(f"- **[{f.severity}]** {location} ({f.category}): {f.summary}")
        if f.detail:
            lines.append(f"  {f.detail}")
    return "\n".join(lines)
