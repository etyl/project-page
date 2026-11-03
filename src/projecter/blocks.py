"""Building blocks that make up a project page.

These dataclasses model the structured content of a page. The parser fills
them from the markdown front matter and body; the renderer turns them into
HTML using a layout modelled on the Nerfies / NRMF academic project page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Author:
    """A single author entry from the page metadata.

    ``affiliation`` is the superscript marker(s) shown after the name, e.g.
    ``"1"`` or ``"1,2"``; it indexes into :attr:`Metadata.affiliations`.
    """

    name: str
    url: Optional[str] = None
    affiliation: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Link:
    """A header button (Paper, Code, arXiv, Video, ...).

    ``icon`` is a Font Awesome / Academicons class, e.g. ``"fas fa-file-pdf"``,
    ``"fab fa-github"`` or ``"ai ai-arxiv"``.
    """

    label: str
    url: str
    icon: Optional[str] = None


@dataclass
class Metadata:
    """Top-level page metadata, typically read from the YAML front matter."""

    title: str
    authors: list[Author] = field(default_factory=list)
    # Superscript marker -> institution name, e.g. {"1": "Imperial College London"}.
    affiliations: dict[str, str] = field(default_factory=dict)
    # Highlight badge shown above the authors, e.g. "CVPR 2026 Highlight".
    badge: Optional[str] = None
    venue: Optional[str] = None
    links: list[Link] = field(default_factory=list)
    # Used for the social/meta tags in <head>.
    description: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    # Template to render with: a short name (e.g. "ml-page", "ml-blog") from
    # ``renderer.TEMPLATES``, or a raw template filename.
    template: str = "ml-page"


@dataclass
class Abstract:
    """The abstract block. ``html`` holds the rendered abstract body."""

    html: str


@dataclass
class Figure:
    """A figure with an image, caption and stable reference label."""

    src: str
    label: str
    caption_html: str = ""
    alt: str = ""


@dataclass
class Section:
    """A content section. ``html`` is the rendered MyST body of the section.

    The body may already contain images/equations produced by MyST, so a
    section is rendered as a single panel in the template.
    """

    label: str
    title: str
    html: str
    level: int = 2


@dataclass
class Citation:
    """A bibliography entry parsed from a BibTeX record."""

    key: str
    # The raw bibtex entry, kept so it can be offered for download/copy.
    bibtex: str
    # A pre-rendered human-readable reference string, filled by the parser.
    rendered: str = ""


@dataclass
class Page:
    """A fully assembled project page, ready to be rendered to HTML."""

    metadata: Metadata
    abstract: Optional[Abstract] = None
    sections: list[Section] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    # The "cite this work" BibTeX shown in the copy-able card.
    bibtex: Optional[str] = None
    # Rendered HTML for the acknowledgements section.
    acknowledgements: Optional[str] = None
    # Extra CSS from the `css:` front-matter key, inlined into <head>.
    css: Optional[str] = None
    # Path the page was parsed from, used to decide where to write the HTML.
    source_path: Optional[str] = None
