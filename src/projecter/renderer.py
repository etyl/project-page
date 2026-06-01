"""Render a :class:`~projecter.blocks.Page` to an HTML document with Jinja2."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from projecter.blocks import Page

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _make_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_page(page: Page, template_name: str = "page.html.jinja") -> str:
    """Render ``page`` to a complete HTML document string."""
    env = _make_environment()
    template = env.get_template(template_name)
    return template.render(page=page, meta=page.metadata)
