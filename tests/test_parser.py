"""Tests for front matter, sections and BibTeX parsing in ``parser.py``."""

from __future__ import annotations

from projecter.parser import (
    _clean_latex,
    _format_authors,
    _parse_authors,
    _parse_links,
    _slugify,
    _split_front_matter,
    parse_bibtex,
    parse_file,
    split_sections,
)


# --- front matter ---------------------------------------------------------


def test_split_front_matter_extracts_yaml_and_body() -> None:
    meta, body = _split_front_matter('---\ntitle: "T"\nx: 1\n---\n\nBody text\n')
    assert meta == {"title": "T", "x": 1}
    assert body == "\nBody text\n"


def test_split_front_matter_no_front_matter() -> None:
    meta, body = _split_front_matter("# Just a heading\n\ntext")
    assert meta == {}
    assert body == "# Just a heading\n\ntext"


def test_split_front_matter_empty_block() -> None:
    meta, body = _split_front_matter("---\n---\nbody")
    assert meta == {}
    assert "body" in body


def test_split_front_matter_unterminated_is_left_alone() -> None:
    # An opening `---` with no closing delimiter should not be treated as YAML.
    text = "---\ntitle: T\nno closing fence"
    meta, body = _split_front_matter(text)
    assert meta == {}
    assert body == text


# --- authors --------------------------------------------------------------


def test_parse_authors_from_strings() -> None:
    authors = _parse_authors(["Alice", "Bob"])
    assert [a.name for a in authors] == ["Alice", "Bob"]
    assert authors[0].affiliation is None


def test_parse_authors_from_dicts() -> None:
    authors = _parse_authors(
        [{"name": "Alice", "url": "u", "affiliation": 1, "email": "a@x.com"}]
    )
    assert authors[0].url == "u"
    assert authors[0].affiliation == "1"
    assert authors[0].email == "a@x.com"


def test_parse_authors_affiliation_list_is_joined() -> None:
    authors = _parse_authors([{"name": "A", "affiliation": [1, 2]}])
    assert authors[0].affiliation == "1,2"


def test_parse_authors_none_yields_empty() -> None:
    assert _parse_authors(None) == []


def test_parse_authors_ignores_unknown_types() -> None:
    # A bare int is neither a str nor a dict and should be skipped.
    assert _parse_authors([42, "Real"]) == _parse_authors(["Real"])


# --- links ----------------------------------------------------------------


def test_parse_links_from_list_of_dicts() -> None:
    links = _parse_links([{"label": "Paper", "url": "u", "icon": "fa"}])
    assert links[0].label == "Paper"
    assert links[0].icon == "fa"


def test_parse_links_from_mapping_has_no_icons() -> None:
    links = _parse_links({"Paper": "u1", "Code": "u2"})
    assert {(link.label, link.url) for link in links} == {
        ("Paper", "u1"),
        ("Code", "u2"),
    }
    assert all(link.icon is None for link in links)


def test_parse_links_none_yields_empty() -> None:
    assert _parse_links(None) == []


# --- slugify --------------------------------------------------------------


def test_slugify_lowercases_and_dashes() -> None:
    assert _slugify("Hello World") == "hello-world"


def test_slugify_strips_punctuation() -> None:
    assert _slugify("Method & Results!") == "method-results"


def test_slugify_collapses_underscores_and_spaces() -> None:
    assert _slugify("a_b   c") == "a-b-c"


def test_slugify_empty_falls_back() -> None:
    assert _slugify("!!!") == "section"


# --- split_sections -------------------------------------------------------


def test_split_sections_levels_and_labels() -> None:
    body = "intro\n\n## Method\n\ntext\n\n### Sub\n\nmore\n"
    sections = split_sections(body)
    assert [(s.level, s.title) for s in sections] == [
        (2, ""),
        (2, "Method"),
        (3, "Sub"),
    ]
    assert sections[0].label == "preamble"
    assert sections[2].label == "sub"


def test_split_sections_ignores_headings_in_code() -> None:
    body = "## Real\n\n```python\n## not a heading\n```\n"
    sections = split_sections(body)
    assert [s.title for s in sections] == ["Real"]


def test_split_sections_ignores_headings_in_tilde_fence() -> None:
    body = "## Real\n\n~~~\n## not a heading\n~~~\n"
    assert [s.title for s in split_sections(body)] == ["Real"]


def test_split_sections_disambiguates_duplicate_titles() -> None:
    body = "## Results\n\na\n\n## Results\n\nb\n\n## Results\n\nc\n"
    labels = [s.label for s in split_sections(body)]
    assert labels == ["results", "results-2", "results-3"]


def test_split_sections_drops_empty_preamble() -> None:
    sections = split_sections("## Only\n\ntext\n")
    assert [s.title for s in sections] == ["Only"]


def test_split_sections_strips_trailing_hashes() -> None:
    sections = split_sections("## Title ##\n\nbody\n")
    assert sections[0].title == "Title"


def test_split_sections_renders_body_to_html() -> None:
    sections = split_sections("## H\n\n**bold** text\n")
    assert "<strong>bold</strong>" in sections[0].html


# --- BibTeX ---------------------------------------------------------------


def test_parse_bibtex_extracts_key() -> None:
    citations = parse_bibtex("@article{example2026, title={X}, year={2026}}")
    assert citations[0].key == "example2026"
    assert citations[0].bibtex.startswith("@article{example2026")


def test_parse_bibtex_renders_reference_string() -> None:
    bib = (
        "@inproceedings{doe2026,\n"
        "  author = {Doe, Jane and Smith, John},\n"
        "  title = {A Great Paper},\n"
        "  booktitle = {CVPR},\n"
        "  year = {2026}\n"
        "}\n"
    )
    citation = parse_bibtex(bib)[0]
    assert "Jane Doe and John Smith" in citation.rendered
    assert "A Great Paper." in citation.rendered
    assert "<em>CVPR</em>" in citation.rendered
    assert "2026." in citation.rendered


def test_parse_bibtex_multiple_entries() -> None:
    bib = "@article{a, year={2020}}\n@misc{b, year={2021}}\n"
    citations = parse_bibtex(bib)
    assert [c.key for c in citations] == ["a", "b"]


def test_parse_bibtex_empty_string() -> None:
    assert parse_bibtex("") == []


def test_parse_bibtex_prefers_journal_over_booktitle() -> None:
    bib = "@article{a, journal={Nature}, booktitle={Ignored}, year={2020}}"
    assert "<em>Nature</em>" in parse_bibtex(bib)[0].rendered


def test_parse_bibtex_falls_back_to_key_without_fields() -> None:
    # With a key but no recognised fields, the rendered string is just the key.
    assert parse_bibtex("@misc{onlykey,}")[0].rendered == "onlykey"


def test_clean_latex_resolves_accents() -> None:
    assert _clean_latex(r"M{\"u}ller") == "Müller"
    assert _clean_latex(r"Caf\'e") == "Café"


def test_clean_latex_strips_braces_and_collapses_whitespace() -> None:
    assert _clean_latex("{Deep   Learning}") == "Deep Learning"


def test_format_authors_single() -> None:
    assert _format_authors("Jane Doe") == "Jane Doe"


def test_format_authors_flips_last_first() -> None:
    assert _format_authors("Doe, Jane") == "Jane Doe"


def test_format_authors_three_uses_and() -> None:
    out = _format_authors("A and B and C")
    assert out == "A, B and C"


def test_format_authors_empty() -> None:
    assert _format_authors("") == ""


# --- parse_file -----------------------------------------------------------


def test_parse_file_reads_metadata(example_path) -> None:
    page = parse_file(example_path)
    assert page.metadata.title == "My Research Project"
    assert page.metadata.authors[0].name == "John Doe"
    assert page.metadata.affiliations == {"1": "Example University"}
    assert page.abstract is not None
    assert page.metadata.keywords == ["example", "projecter", "research"]


def test_parse_file_links_parsed(example_path) -> None:
    page = parse_file(example_path)
    labels = [link.label for link in page.metadata.links]
    assert labels == ["Paper", "Code"]


def test_parse_file_sections(example_path) -> None:
    page = parse_file(example_path)
    titles = [s.title for s in page.sections]
    # Only `##`/`###` start sections; the leading `# Introduction` H1 is not a
    # split point and stays in the untitled preamble.
    assert "Method" in titles
    assert "Details" in titles
    assert page.sections[0].title == ""
    assert page.source_path == str(example_path)


def test_parse_file_title_defaults_to_stem(write_md) -> None:
    path = write_md("---\nprojecter: true\n---\n\nbody\n", name="my-page.md")
    page = parse_file(path)
    assert page.metadata.title == "my-page"


def test_parse_file_inline_bibtex(write_md) -> None:
    path = write_md('---\ntitle: T\nbibtex: "@misc{x}"\n---\n\nbody\n')
    assert parse_file(path).bibtex == "@misc{x}"


def test_parse_file_cite_path_read(write_md, tmp_path) -> None:
    (tmp_path / "cite.bib").write_text("@misc{citekey}\n", encoding="utf-8")
    path = write_md("---\ntitle: T\ncite: cite.bib\n---\n\nbody\n")
    assert parse_file(path).bibtex == "@misc{citekey}"


def test_parse_file_bibliography_loaded(write_md, tmp_path) -> None:
    (tmp_path / "refs.bib").write_text(
        "@article{ref1, title={A}, year={2020}}\n", encoding="utf-8"
    )
    path = write_md("---\ntitle: T\nbibliography: refs.bib\n---\n\nbody\n")
    citations = parse_file(path).citations
    assert [c.key for c in citations] == ["ref1"]


def test_parse_file_missing_bibliography_is_ignored(write_md) -> None:
    path = write_md("---\ntitle: T\nbibliography: nope.bib\n---\n\nbody\n")
    assert parse_file(path).citations == []


def test_parse_file_acknowledgements_rendered(write_md) -> None:
    path = write_md(
        "---\ntitle: T\nacknowledgements: Thanks to **everyone**.\n---\n\nbody\n"
    )
    page = parse_file(path)
    assert page.acknowledgements is not None
    assert "<strong>everyone</strong>" in page.acknowledgements
