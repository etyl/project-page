"""Tests for LaTeX table conversion in ``latex.py``."""

from __future__ import annotations

from projecter.latex import (
    _parse_aligns,
    protect_tables,
    restore_tables,
    tabular_to_html,
)


def test_parse_aligns_basic() -> None:
    assert _parse_aligns("lcr") == ["left", "center", "right"]


def test_parse_aligns_drops_rules_and_inter_column() -> None:
    assert _parse_aligns("|l|c|") == ["left", "center"]
    assert _parse_aligns("l@{ }c") == ["left", "center"]


def test_parse_aligns_paragraph_columns_become_left() -> None:
    assert _parse_aligns("p{3cm}c") == ["left", "center"]


def test_tabular_to_html_header_and_body() -> None:
    html = tabular_to_html("lcc", "A & B & C \\\\ \\hline 1 & 2 & 3 \\\\")
    assert html.count("<tr>") == 2
    assert "<thead>" in html and "<th" in html
    assert '<td style="text-align:center">2</td>' in html


def test_tabular_to_html_applies_alignments() -> None:
    html = tabular_to_html("lcr", "a & b & c \\\\ 1 & 2 & 3 \\\\")
    assert 'style="text-align:left">1' in html
    assert 'style="text-align:center">2' in html
    assert 'style="text-align:right">3' in html


def test_tabular_to_html_extra_columns_default_left() -> None:
    # More cells than the column spec declares -> default alignment is left.
    html = tabular_to_html("l", "a & b \\\\")
    assert 'style="text-align:left">b' in html


def test_tabular_to_html_formats_inline_commands() -> None:
    html = tabular_to_html("l", r"\textbf{Bold} \\ \textit{It} \\ \texttt{Mono} \\")
    assert "<strong>Bold</strong>" in html
    assert "<em>It</em>" in html
    assert "<code>Mono</code>" in html


def test_tabular_to_html_strips_booktabs_rules() -> None:
    html = tabular_to_html("ll", "a & b \\\\ \\toprule \\midrule c & d \\\\ \\bottomrule")
    assert "toprule" not in html and "midrule" not in html
    assert "<td" in html


def test_tabular_to_html_multicolumn_spans_and_aligns() -> None:
    html = tabular_to_html("ll", r"\multicolumn{2}{c}{Spanned} \\ a & b \\")
    assert 'colspan="2"' in html
    assert "text-align:center" in html
    assert ">Spanned</th>" in html


def test_tabular_to_html_does_not_split_escaped_ampersand() -> None:
    # The escaped `\&` must stay in a single cell, not split the row in two.
    html = tabular_to_html("l", r"Tom \& Jerry \\")
    assert html.count("<th ") == 1
    assert "Tom &amp; Jerry" in html


def test_tabular_to_html_empty_body() -> None:
    assert tabular_to_html("l", "") == ""


def test_protect_tables_bare_tabular() -> None:
    md = "\\begin{tabular}{lc}\nA & B \\\\\n\\end{tabular}\n"
    protected, tables = protect_tables(md)
    assert "LTXTABLEPLACEHOLDER" in protected
    assert len(tables) == 1
    assert 'class="latex-table"' in tables[0]


def test_protect_tables_table_environment_with_caption_and_label() -> None:
    md = (
        "\\begin{table}\n\\caption{My caption}\n\\label{tab:x}\n"
        "\\begin{tabular}{l}\nA \\\\\n\\end{tabular}\n\\end{table}\n"
    )
    _, tables = protect_tables(md)
    assert 'class="latex-table-figure"' in tables[0]
    assert 'id="tab:x"' in tables[0]
    assert "<figcaption>My caption</figcaption>" in tables[0]


def test_protect_tables_does_not_double_count_inner_tabular() -> None:
    # A `table` wrapping a `tabular` must produce exactly one HTML table.
    md = (
        "\\begin{table}\n\\begin{tabular}{l}\nA \\\\\n\\end{tabular}\n\\end{table}\n"
    )
    _, tables = protect_tables(md)
    assert len(tables) == 1


def test_restore_tables_unwraps_paragraph() -> None:
    protected, tables = protect_tables(
        "\\begin{tabular}{l}\nA \\\\\n\\end{tabular}\n"
    )
    token = protected.strip()
    html = restore_tables(f"<p>{token}</p>", tables)
    assert html == tables[0]
    assert "LTXTABLEPLACEHOLDER" not in html


def test_restore_tables_inline_token() -> None:
    _, tables = protect_tables("\\begin{tabular}{l}\nA \\\\\n\\end{tabular}\n")
    out = restore_tables("LTXTABLEPLACEHOLDER0LTX", tables)
    assert out == tables[0]
