"""Data model for review findings."""

from __future__ import annotations

from dataclasses import dataclass

SEVERITIES = ("blocker", "warning", "nit")


@dataclass
class Finding:
    file: str
    line: int | None
    severity: str
    category: str
    summary: str
    detail: str

    @classmethod
    def from_dict(cls, d: dict) -> "Finding":
        severity = d.get("severity", "nit")
        if severity not in SEVERITIES:
            severity = "nit"
        return cls(
            file=d.get("file", "unknown"),
            line=d.get("line"),
            severity=severity,
            category=d.get("category", "general"),
            summary=d.get("summary", ""),
            detail=d.get("detail", ""),
        )
