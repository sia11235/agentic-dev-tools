from agentic_tools.review.findings import Finding
from agentic_tools.review.report import render_json, render_markdown, render_text


def _findings():
    return [
        Finding("a.py", 10, "blocker", "correctness", "off by one", "should be <= not <"),
        Finding("b.py", None, "nit", "clarity", "rename var", ""),
    ]


def test_render_text_empty():
    assert "No findings" in render_text([])


def test_render_text_sorts_blockers_first():
    out = render_text(_findings())
    assert out.index("BLOCKER") < out.index("NIT")


def test_render_json_roundtrip():
    import json

    out = json.loads(render_json(_findings()))
    assert out[0]["severity"] == "blocker"
    assert out[0]["file"] == "a.py"


def test_render_markdown_empty():
    assert "no findings" in render_markdown([]).lower()


def test_render_markdown_includes_summary():
    out = render_markdown(_findings())
    assert "off by one" in out
