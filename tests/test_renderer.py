"""Tests for the Jinja rendering layer in ``renderer.py``."""

from __future__ import annotations

import pytest

from projecter.blocks import Abstract, Author, Link, Metadata, Page, Section
from projecter.renderer import TEMPLATES, render_page, resolve_template


def _page(**meta_kwargs) -> Page:
    meta_kwargs.setdefault("title", "My Title")
    meta = Metadata(**meta_kwargs)
    return Page(
        metadata=meta,
        abstract=Abstract(html="<p>The abstract.</p>"),
        sections=[Section(label="intro", title="Intro", html="<p>Body.</p>")],
    )


def test_resolve_short_names() -> None:
    assert resolve_template("ml-page") == "page.html.jinja"
    assert resolve_template("ml-blog") == "latex.html.jinja"


def test_resolve_passthrough_for_raw_filename() -> None:
    assert resolve_template("custom.html.jinja") == "custom.html.jinja"


def test_render_page_includes_title() -> None:
    html = render_page(_page())
    assert "<title>My Title</title>" in html
    assert html.lstrip().lower().startswith("<!doctype html")


def test_render_page_includes_section_and_abstract() -> None:
    html = render_page(_page())
    assert "The abstract." in html
    assert "Body." in html


def test_render_page_does_not_escape_title() -> None:
    # NOTE: the env asks for `select_autoescape(["html", "xml"])`, but the
    # templates are named ``*.html.jinja`` so the ``.jinja`` suffix means
    # autoescaping never kicks in — metadata is rendered verbatim. This test
    # pins that (surprising) behaviour; flip it if autoescaping is fixed.
    html = render_page(_page(title="A < B & C"))
    assert "A < B & C" in html


def test_render_page_pre_rendered_html_is_safe() -> None:
    # Section/abstract HTML is injected via `| safe`, so tags survive verbatim.
    page = _page()
    page.sections[0].html = "<em>kept</em>"
    assert "<em>kept</em>" in render_page(page)


def test_render_page_every_template_renders() -> None:
    for name in TEMPLATES:
        html = render_page(_page(), name)
        assert "My Title" in html
        assert html.strip()


def test_render_page_with_links_and_authors() -> None:
    page = _page(
        authors=[Author(name="Ada", url="https://ada.example")],
        links=[Link(label="Paper", url="https://example.com/p.pdf")],
    )
    html = render_page(page)
    assert "Ada" in html


def test_render_page_unknown_template_raises() -> None:
    from jinja2 import TemplateNotFound

    with pytest.raises(TemplateNotFound):
        render_page(_page(), "does-not-exist.jinja")
