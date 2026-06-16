"""Tests for the ``{figure-grid}`` directive in ``figures.py``."""

from __future__ import annotations

from projecter.figures import (
    _parse_body,
    protect_figure_grids,
    restore_figure_grids,
)


def test_parse_body_options_and_cells() -> None:
    options, cells = _parse_body(
        ":columns: 2\n:caption: Two views.\n\na.png | Left\nb.png | Right\n"
    )
    assert options == {"columns": "2", "caption": "Two views."}
    assert cells == [("a.png", "Left"), ("b.png", "Right")]


def test_parse_body_cells_without_captions() -> None:
    _, cells = _parse_body("a.png\nb.png\n")
    assert cells == [("a.png", ""), ("b.png", "")]


def test_figure_grid_layout() -> None:
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


def test_figure_grid_defaults_columns_to_cell_count() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n\na.png\nb.png\nc.png\n```\n")
    assert "--figgrid-cols:3" in grids[0]


def test_figure_grid_default_gap() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n\na.png\n```\n")
    assert "--figgrid-gap:24px" in grids[0]


def test_figure_grid_custom_gap() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n:gap: 8px\n\na.png\n```\n")
    assert "--figgrid-gap:8px" in grids[0]


def test_figure_grid_alt_falls_back_to_filename() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n\ndir/photo.png\n```\n")
    assert 'alt="photo.png"' in grids[0]


def test_figure_grid_caption_used_as_alt() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n\na.png | A view\n```\n")
    assert 'alt="A view"' in grids[0]


def test_figure_grid_escapes_html_in_caption() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n\na.png | <b> & x\n```\n")
    assert "&lt;b&gt; &amp; x" in grids[0]


def test_figure_grid_empty_yields_empty_string() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n:columns: 2\n```\n")
    assert grids == [""]


def test_protect_no_grid_is_noop() -> None:
    protected, grids = protect_figure_grids("plain text\n")
    assert grids == []
    assert protected == "plain text\n"


def test_restore_unwraps_paragraph() -> None:
    _, grids = protect_figure_grids("```{figure-grid}\n\na.png\n```\n")
    out = restore_figure_grids("<p>FIGGRIDPLACEHOLDER0FIGGRID</p>", grids)
    assert out == grids[0]
    assert "FIGGRIDPLACEHOLDER" not in out
