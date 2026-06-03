"""Render a :class:`~projecter.blocks.Page` to an HTML document with Jinja2."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from projecter.blocks import Page

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Short, author-facing names mapped to their Jinja template files. A page can
# select one with a ``template:`` front-matter key; the value may be a short
# name from this map or a raw template filename.
TEMPLATES = {
    "ml-page": "page.html.jinja",  # modern academic project page (default)
    "ml-blog": "latex.html.jinja",  # classic LaTeX article style
}

DEFAULT_TEMPLATE = "ml-page"


def _make_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def resolve_template(name: str) -> str:
    """Resolve a short template name (or raw filename) to a template file."""
    return TEMPLATES.get(name, name)


def render_page(page: Page, template_name: str = DEFAULT_TEMPLATE) -> str:
    """Render ``page`` to a complete HTML document string.

    ``template_name`` accepts a short name from :data:`TEMPLATES`
    (e.g. ``"ml-blog"``) or a raw template filename.
    """
    env = _make_environment()
    template = env.get_template(resolve_template(template_name))
    return template.render(page=page, meta=page.metadata)
