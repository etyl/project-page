"""Tests for ``[@key]`` inline citation handling in ``citations.py``."""

from __future__ import annotations

from projecter.citations import protect_citations, restore_citations
from projecter.parser import parse_file

NUMBERING = {"smith2020": 1, "doe2021": 2}


def test_protect_single_citation() -> None:
    protected, spans = protect_citations("See [@smith2020] for details.", NUMBERING)
    assert "CITEPLACEHOLDER0CITE" in protected
    assert spans == ['[<a href="#cite-smith2020" class="citation">1</a>]']


def test_number_matches_bibliography_position() -> None:
    # The second entry renders as [2], so it lines up with the <ol> of refs.
    _, spans = protect_citations("[@doe2021]", NUMBERING)
    assert ">2</a>" in spans[0]
    assert 'href="#cite-doe2021"' in spans[0]


def test_grouped_citations_share_one_bracket() -> None:
    _, spans = protect_citations("[@smith2020; @doe2021]", NUMBERING)
    assert spans[0].startswith("[")
    assert spans[0].endswith("]")
    assert ">1</a>, " in spans[0]
    assert ">2</a>" in spans[0]


def test_unknown_key_renders_question_mark() -> None:
    _, spans = protect_citations("[@missing]", NUMBERING)
    assert spans == ["[?]"]


def test_multiple_citations_indexed() -> None:
    protected, spans = protect_citations("[@smith2020] and [@doe2021]", NUMBERING)
    assert len(spans) == 2
    assert "CITEPLACEHOLDER0CITE" in protected
    assert "CITEPLACEHOLDER1CITE" in protected


def test_markdown_links_are_left_alone() -> None:
    # `[text](url)` and `[^note]` have no leading `@`, so they don't match.
    text = "A [link](http://x) and a [^note]."
    protected, spans = protect_citations(text, NUMBERING)
    assert spans == []
    assert protected == text


def test_no_citation_is_noop() -> None:
    protected, spans = protect_citations("plain text", NUMBERING)
    assert spans == []
    assert protected == "plain text"


def test_restore_round_trips() -> None:
    protected, spans = protect_citations("See [@smith2020].", NUMBERING)
    restored = restore_citations(protected, spans)
    assert restored == 'See [<a href="#cite-smith2020" class="citation">1</a>].'
    assert "CITEPLACEHOLDER" not in restored


def test_restore_keeps_link_inside_paragraph() -> None:
    _, spans = protect_citations("[@smith2020]", NUMBERING)
    out = restore_citations("<p>text CITEPLACEHOLDER0CITE here</p>", spans)
    assert out == (
        '<p>text [<a href="#cite-smith2020" class="citation">1</a>] here</p>'
    )


# --- end-to-end through the parser ---------------------------------------


def test_parse_file_resolves_inline_citations(write_md, tmp_path) -> None:
    (tmp_path / "refs.bib").write_text(
        "@article{ref1, title={A}, year={2020}}\n"
        "@article{ref2, title={B}, year={2021}}\n",
        encoding="utf-8",
    )
    path = write_md(
        "---\ntitle: T\nbibliography: refs.bib\n---\n\n"
        "We build on [@ref2] and [@ref1].\n"
    )
    section = parse_file(path).sections[0]
    assert '<a href="#cite-ref2" class="citation">2</a>' in section.html
    assert '<a href="#cite-ref1" class="citation">1</a>' in section.html
    assert "CITEPLACEHOLDER" not in section.html


def test_inline_citations_left_literal_without_bibliography(write_md) -> None:
    # No bibliography -> nothing to resolve against, so the span is not turned
    # into a link (it passes through the markdown unchanged, bar HTML escaping).
    html = parse_file(write_md("---\ntitle: T\n---\n\nSee [@ref1].\n")).sections[0].html
    assert "#cite-ref1" not in html
    assert "CITEPLACEHOLDER" not in html
