"""Split a unified diff into reviewable chunks.

A large diff sent in one request either blows the context window or gets a
shallow review. Instead we split by file, drop noise (lockfiles, binaries,
generated output), and pack files into chunks under a size budget. A single
file that is larger than the budget is split on hunk boundaries.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field

# Roughly 4 chars per token, so 60k chars is ~15k tokens of diff per request.
DEFAULT_MAX_CHUNK_CHARS = 60_000

DEFAULT_EXCLUDES = (
    # lockfiles
    "*.lock",
    "*-lock.json",
    "*-lock.yaml",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "Cargo.lock",
    "go.sum",
    # generated / compiled / vendored
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.pyc",
    "*/__pycache__/*",
    "__pycache__/*",
    "dist/*",
    "build/*",
    "*/migrations/meta/*",
    # binary-ish assets
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.pdf",
    "*.woff",
    "*.woff2",
)

_FILE_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)
_HUNK_HEADER = re.compile(r"^@@ ", re.MULTILINE)


@dataclass
class FileDiff:
    path: str
    text: str

    @property
    def is_binary(self) -> bool:
        head = self.text[:2000]
        return "\nBinary files " in head or "\nGIT binary patch" in head


@dataclass
class Chunk:
    files: list[FileDiff] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(f.text for f in self.files)

    @property
    def size(self) -> int:
        return sum(len(f.text) for f in self.files)

    @property
    def paths(self) -> list[str]:
        # A file split by hunks appears more than once; list it once.
        return list(dict.fromkeys(f.path for f in self.files))


def split_by_file(diff: str) -> list[FileDiff]:
    """Split a unified diff into one entry per file (header + hunks)."""
    matches = list(_FILE_HEADER.finditer(diff))
    files = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(diff)
        files.append(FileDiff(path=m.group(2), text=diff[m.start():end]))
    return files


def is_excluded(path: str, patterns: tuple[str, ...] | list[str]) -> bool:
    name = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(name, p) for p in patterns)


def _split_large_file(f: FileDiff, max_chars: int) -> list[FileDiff]:
    """Split one file's diff on hunk boundaries, repeating the file header in each piece."""
    first_hunk = _HUNK_HEADER.search(f.text)
    if not first_hunk:
        return [f]
    header = f.text[: first_hunk.start()]
    starts = [m.start() for m in _HUNK_HEADER.finditer(f.text)]
    hunks = [f.text[s:e] for s, e in zip(starts, starts[1:] + [len(f.text)])]

    pieces: list[FileDiff] = []
    current = ""
    for hunk in hunks:
        if current and len(header) + len(current) + len(hunk) > max_chars:
            pieces.append(FileDiff(f.path, header + current))
            current = ""
        # A single hunk bigger than the budget is kept whole rather than cut mid-hunk.
        current += hunk
    if current:
        pieces.append(FileDiff(f.path, header + current))
    return pieces


def chunk_diff(
    diff: str,
    max_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    excludes: tuple[str, ...] | list[str] = DEFAULT_EXCLUDES,
) -> tuple[list[Chunk], list[str]]:
    """Return (chunks to review, paths skipped).

    Files are packed in diff order so related files (same directory) tend to
    land in the same chunk.
    """
    skipped: list[str] = []
    pieces: list[FileDiff] = []
    for f in split_by_file(diff):
        if is_excluded(f.path, excludes) or f.is_binary:
            skipped.append(f.path)
            continue
        if len(f.text) > max_chars:
            pieces.extend(_split_large_file(f, max_chars))
        else:
            pieces.append(f)

    chunks: list[Chunk] = []
    current = Chunk()
    for piece in pieces:
        if current.files and current.size + len(piece.text) > max_chars:
            chunks.append(current)
            current = Chunk()
        current.files.append(piece)
    if current.files:
        chunks.append(current)
    return chunks, skipped
