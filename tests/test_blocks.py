"""Tests for the dataclass data model in ``projecter/blocks.py``."""

from __future__ import annotations

from projecter.blocks import (
    Abstract,
    Author,
    Citation,
    Figure,
    Link,
    Metadata,
    Page,
    Section,
)


def test_author_defaults() -> None:
    author = Author(name="Ada Lovelace")
    assert author.name == "Ada Lovelace"
    assert author.url is None
    assert author.affiliation is None
    assert author.email is None


def test_link_requires_label_and_url() -> None:
    link = Link(label="Paper", url="https://example.com")
    assert link.icon is None


def test_metadata_defaults_are_independent() -> None:
    # The mutable defaults must not be shared between instances.
    a = Metadata(title="A")
    b = Metadata(title="B")
    a.authors.append(Author(name="x"))
    a.affiliations["1"] = "Uni"
    a.links.append(Link(label="l", url="u"))
    a.keywords.append("k")
    assert b.authors == []
    assert b.affiliations == {}
    assert b.links == []
    assert b.keywords == []


def test_metadata_default_template() -> None:
    assert Metadata(title="T").template == "ml-page"


def test_citation_defaults_rendered_empty() -> None:
    citation = Citation(key="k", bibtex="@misc{k}")
    assert citation.rendered == ""


def test_figure_defaults() -> None:
    figure = Figure(src="a.png", label="fig-a")
    assert figure.caption_html == ""
    assert figure.alt == ""


def test_section_default_level() -> None:
    assert Section(label="l", title="T", html="<p>x</p>").level == 2


def test_page_defaults_are_independent() -> None:
    meta = Metadata(title="T")
    a = Page(metadata=meta)
    b = Page(metadata=meta)
    a.sections.append(Section(label="l", title="T", html=""))
    a.citations.append(Citation(key="k", bibtex=""))
    assert b.sections == []
    assert b.citations == []
    assert b.abstract is None
    assert b.bibtex is None
    assert b.acknowledgements is None
    assert b.source_path is None


def test_abstract_holds_html() -> None:
    assert Abstract(html="<p>hi</p>").html == "<p>hi</p>"
