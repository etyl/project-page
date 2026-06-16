"""End-to-end tests exercising the full protect/restore + render pipeline.

These cover ``myst_to_html`` (where the order of the protect/restore passes
matters) and a full build of the canonical example page.
"""

from __future__ import annotations

from projecter.builder import build_file
from projecter.parser import myst_to_html


def test_basic_markdown_renders() -> None:
    html = myst_to_html("# Title\n\nSome **bold** and *italic* text.\n")
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_math_underscores_not_mangled() -> None:
    md = (
        "Inline $\\hat{e}_{||}$ and $\\hat{e}_{\\perp}$ axes.\n\n"
        "$$\nJ^v \\approx \\frac{a_{||}}{b} \\quad \\frac{a_{\\perp}}{b}\n$$\n"
    )
    html = myst_to_html(md)
    # Markdown must not turn the underscores into emphasis inside the math.
    assert "<em>" not in html
    assert "$\\hat{e}_{||}$" in html
    assert "\\frac{a_{||}}{b}" in html
    assert "MATHJAXPLACEHOLDER" not in html


def test_latex_table_roundtrip_through_myst() -> None:
    md = (
        "Intro.\n\n"
        "\\begin{tabular}{lc}\n"
        "Name & Score \\\\\n\\midrule\n"
        "\\textbf{Ours} & 9.5 \\\\\n"
        "\\end{tabular}\n"
    )
    html = myst_to_html(md)
    assert 'class="latex-table"' in html
    assert "<strong>Ours</strong>" in html
    assert "LTXTABLEPLACEHOLDER" not in html


def test_audio_directive_through_myst() -> None:
    md = (
        "Intro.\n\n"
        "```{audio} static/audio/podcast.m4a\n"
        ":label: fig-podcast\n\nThe podcast.\n```\n"
    )
    html = myst_to_html(md)
    assert "<audio controls" in html
    assert 'type="audio/mp4"' in html
    assert 'id="fig-podcast"' in html
    assert "MEDIAPLACEHOLDER" not in html


def test_figure_grid_through_myst() -> None:
    md = "Intro.\n\n```{figure-grid}\n\na.png\nb.png\nc.png\n```\n"
    html = myst_to_html(md)
    assert html.count("<img") == 3
    assert "--figgrid-cols:3" in html
    assert "FIGGRIDPLACEHOLDER" not in html


def test_all_directives_coexist_in_one_body() -> None:
    # Math is protected last; the other placeholders must not collide with it.
    md = (
        "Energy $E=mc^2$ and a table:\n\n"
        "\\begin{tabular}{l}\nA \\\\\n\\end{tabular}\n\n"
        "```{audio} a.mp3\n```\n\n"
        "```{figure-grid}\n\nx.png\n```\n"
    )
    html = myst_to_html(md)
    for leak in (
        "MATHJAXPLACEHOLDER",
        "LTXTABLEPLACEHOLDER",
        "MEDIAPLACEHOLDER",
        "FIGGRIDPLACEHOLDER",
    ):
        assert leak not in html
    assert "$E=mc^2$" in html
    assert 'class="latex-table"' in html
    assert "<audio controls" in html
    assert "<img" in html


def test_build_example_page(example_path, tmp_path) -> None:
    # Build the canonical example into a temp copy and sanity-check the output.
    src = tmp_path / "index.md"
    src.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
    out = build_file(src)
    html = out.read_text(encoding="utf-8")
    assert "<title>My Research Project</title>" in html
    assert "John Doe" in html
    assert "Method" in html
    # No protect/restore placeholder should ever leak into a built page.
    for leak in ("PLACEHOLDER",):
        assert leak not in html
