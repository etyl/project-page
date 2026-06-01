"""Tests for projecter."""

from pathlib import Path

import projecter
from projecter.builder import build_file, is_project_page
from projecter.parser import parse_bibtex, parse_file, split_sections

EXAMPLE = Path(__file__).parent.parent / "examples" / "index.md"


def test_version() -> None:
    assert projecter.__version__ == "0.1.0"


def test_parse_file_reads_metadata() -> None:
    page = parse_file(EXAMPLE)
    assert page.metadata.title == "My Research Project"
    assert page.metadata.authors[0].name == "Hippolyte Verninas"
    assert page.abstract is not None


def test_parse_bibtex_extracts_keys() -> None:
    citations = parse_bibtex("@article{example2026, title={X}, year={2026}}")
    assert citations[0].key == "example2026"


def test_is_project_page() -> None:
    assert is_project_page(EXAMPLE)


def test_split_sections_levels() -> None:
    body = "intro\n\n## Method\n\ntext\n\n### Sub\n\nmore\n"
    sections = split_sections(body)
    levels = [(s.level, s.title) for s in sections]
    assert levels == [(2, ""), (2, "Method"), (3, "Sub")]
    assert sections[0].label == "preamble"
    assert sections[2].label == "sub"


def test_split_sections_ignores_headings_in_code() -> None:
    body = "## Real\n\n```python\n## not a heading\n```\n"
    sections = split_sections(body)
    assert [s.title for s in sections] == ["Real"]


def test_latex_tabular_to_html() -> None:
    from projecter.latex import tabular_to_html

    html = tabular_to_html("lcc", "A & B & C \\\\ \\hline 1 & 2 & 3 \\\\")
    assert html.count("<tr>") == 2
    assert "<thead>" in html and "<th" in html
    assert "<td style=\"text-align:center\">2</td>" in html


def test_latex_table_roundtrip_through_myst() -> None:
    from projecter.parser import myst_to_html

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
    # The placeholder must not leak into the output.
    assert "LTXTABLEPLACEHOLDER" not in html


def test_media_directives_to_players() -> None:
    from projecter.media import protect_media

    md = (
        "```{video} static/videos/demo.mp4\n"
        ":width: 80%\n:poster: thumb.png\n:autoplay:\n:loop:\n"
        "\nA demo clip.\n```\n"
    )
    protected, blocks = protect_media(md)
    assert "MEDIAPLACEHOLDER" in protected
    html = blocks[0]
    assert "<video" in html and 'class="media-video"' in html
    assert 'type="video/mp4"' in html
    assert "width:80%" in html and 'poster="thumb.png"' in html
    assert " autoplay" in html and " loop" in html
    assert "<figcaption>A demo clip.</figcaption>" in html


def test_video_youtube_embed() -> None:
    from projecter.media import protect_media

    md = (
        "```{video} https://youtu.be/dQw4w9WgXcQ?t=1m30s\n"
        ":muted:\n\nA clip.\n```\n"
    )
    _, blocks = protect_media(md)
    html = blocks[0]
    assert "<iframe" in html and "<video" not in html
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in html
    assert "start=90" in html and "mute=1" in html
    assert "<figcaption>A clip.</figcaption>" in html


def test_video_static_file_stays_video() -> None:
    from projecter.media import protect_media

    _, blocks = protect_media("```{video} static/v.mp4\n```\n")
    assert "<video" in blocks[0] and "<iframe" not in blocks[0]
    assert 'type="video/mp4"' in blocks[0]


def test_audio_directive_through_myst() -> None:
    from projecter.parser import myst_to_html

    md = (
        "Intro.\n\n"
        "```{audio} static/audio/podcast.m4a\n"
        ":label: fig-podcast\n\nThe podcast.\n```\n"
    )
    html = myst_to_html(md)
    assert "<audio controls" in html
    assert 'type="audio/mp4"' in html
    assert 'id="fig-podcast"' in html
    # The placeholder must not leak into the output.
    assert "MEDIAPLACEHOLDER" not in html


def test_figure_grid_layout() -> None:
    from projecter.figures import protect_figure_grids

    md = (
        "```{figure-grid}\n"
        ":label: fig-pair\n:columns: 2\n:caption: Two views.\n\n"
        "a.png | Left\nb.png | Right\n```\n"
    )
    protected, grids = protect_figure_grids(md)
    assert "FIGGRIDPLACEHOLDER" in protected
    html = grids[0]
    assert html.count('class="figure-grid-item"') == 2
    assert "--figgrid-cols:2" in html
    assert 'id="fig-pair"' in html
    assert "<figcaption>Left</figcaption>" in html
    assert 'class="figure-grid-caption">Two views.' in html


def test_figure_grid_through_myst() -> None:
    from projecter.parser import myst_to_html

    md = "Intro.\n\n```{figure-grid}\n\na.png\nb.png\nc.png\n```\n"
    html = myst_to_html(md)
    assert html.count("<img") == 3
    # No columns given: defaults to one column per cell.
    assert "--figgrid-cols:3" in html
    assert "FIGGRIDPLACEHOLDER" not in html


def test_math_underscores_not_mangled() -> None:
    from projecter.parser import myst_to_html

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


def test_build_file_writes_html(tmp_path: Path) -> None:
    md = tmp_path / "page.md"
    md.write_text('---\ntitle: "T"\n---\n\n# Hello\n', encoding="utf-8")
    out = build_file(md)
    assert out == tmp_path / "page.html"
    assert "<title>T</title>" in out.read_text(encoding="utf-8")
