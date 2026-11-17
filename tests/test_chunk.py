from agentic_tools.review.chunk import chunk_diff, is_excluded, split_by_file


def _file(path: str, hunks: int = 1, hunk_lines: int = 3) -> str:
    out = f"diff --git a/{path} b/{path}\nindex 111..222 100644\n--- a/{path}\n+++ b/{path}\n"
    for h in range(hunks):
        out += f"@@ -{h * 10 + 1},1 +{h * 10 + 1},{hunk_lines} @@\n"
        out += "".join(f"+line {h}-{i}\n" for i in range(hunk_lines))
    return out


def test_split_by_file_keeps_each_file_whole():
    diff = _file("a.py") + _file("b/c.ts", hunks=2)
    files = split_by_file(diff)
    assert [f.path for f in files] == ["a.py", "b/c.ts"]
    assert "".join(f.text for f in files) == diff


def test_default_excludes_skip_lockfiles_and_pycache():
    diff = _file("bun.lock") + _file("scripts/__pycache__/x.cpython-310.pyc") + _file("app.ts")
    chunks, skipped = chunk_diff(diff)
    assert skipped == ["bun.lock", "scripts/__pycache__/x.cpython-310.pyc"]
    assert [c.paths for c in chunks] == [["app.ts"]]


def test_binary_files_are_skipped():
    binary = (
        "diff --git a/img.webp b/img.webp\nnew file mode 100644\nindex 0..1\n"
        "Binary files /dev/null and b/img.webp differ\n"
    )
    chunks, skipped = chunk_diff(binary + _file("a.py"))
    assert skipped == ["img.webp"]
    assert chunks[0].paths == ["a.py"]


def test_custom_exclude_matches_directory_glob():
    assert is_excluded("drizzle/migrations/0003.sql", ["drizzle/*"])
    assert not is_excluded("lib/db/schema.ts", ["drizzle/*"])


def test_files_are_packed_under_budget():
    files = [_file(f"f{i}.py", hunk_lines=20) for i in range(10)]
    size = len(files[0])
    chunks, _ = chunk_diff("".join(files), max_chars=size * 3)
    assert len(chunks) == 4  # 3 + 3 + 3 + 1
    assert all(c.size <= size * 3 for c in chunks)
    assert sum(len(c.paths) for c in chunks) == 10


def test_oversized_file_is_split_on_hunks_with_header_repeated():
    big = _file("big.ts", hunks=6, hunk_lines=30)
    chunks, _ = chunk_diff(big, max_chars=len(big) // 3)
    assert len(chunks) > 1
    for c in chunks:
        assert c.text.startswith("diff --git a/big.ts b/big.ts")
        assert c.paths == ["big.ts"]
    # no hunk lost
    joined = "".join(c.text for c in chunks)
    assert joined.count("@@ -") == 6
