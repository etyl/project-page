"""Parse a MyST markdown file into a :class:`~projecter.blocks.Page`.

The parsing strategy:

* YAML front matter holds the metadata (title, authors, abstract, bibliography).
* The markdown body is MyST, converted to an HTML fragment with ``myst-parser``
  via its docutils frontend (no Sphinx required).
* Citations and equations are kept inline; equations are rendered client-side
  by MathJax (see the template), citations resolve against the bibliography.

Most of the heavy lifting is stubbed with TODOs so you can refine the behaviour
to match your own markdown conventions.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from projecter.blocks import (
    Abstract,
    Author,
    Citation,
    Link,
    Metadata,
    Page,
    Section,
)


def _split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a ``---`` delimited YAML front matter block from the body."""
    import yaml  # myst-parser depends on PyYAML, so it is available.

    if text.startswith("---"):
        _, _, rest = text.partition("\n")
        front, sep, body = rest.partition("\n---")
        if sep:
            meta = yaml.safe_load(front) or {}
            # Drop the leading newline left after the closing delimiter.
            return meta, body.partition("\n")[2]
    return {}, text


def _parse_authors(raw: Any) -> list[Author]:
    """Build :class:`Author` objects from the front matter ``authors`` field."""
    authors: list[Author] = []
    for item in raw or []:
        if isinstance(item, str):
            authors.append(Author(name=item))
        elif isinstance(item, dict):
            affiliation = item.get("affiliation")
            authors.append(
                Author(
                    name=item.get("name", ""),
                    url=item.get("url"),
                    # Allow ``affiliation: [1, 2]`` or ``affiliation: "1,2"``.
                    affiliation=(
                        ",".join(str(a) for a in affiliation)
                        if isinstance(affiliation, list)
                        else (str(affiliation) if affiliation is not None else None)
                    ),
                    email=item.get("email"),
                )
            )
    return authors


def _parse_links(raw: Any) -> list[Link]:
    """Build :class:`Link` buttons from the front matter ``links`` field.

    Accepts a list of ``{label, url, icon}`` dicts, or a simple
    ``{label: url}`` mapping (no icons).
    """
    links: list[Link] = []
    if isinstance(raw, dict):
        return [Link(label=label, url=url) for label, url in raw.items()]
    for item in raw or []:
        if isinstance(item, dict):
            links.append(
                Link(
                    label=item.get("label", ""),
                    url=item.get("url", ""),
                    icon=item.get("icon"),
                )
            )
    return links


def myst_to_html(markdown: str) -> str:
    """Render a MyST markdown fragment to an HTML string.

    Uses the docutils frontend shipped with ``myst-parser`` so we get a
    standalone HTML body without pulling in Sphinx. LaTeX ``tabular`` / ``table``
    environments are converted to HTML tables around the markdown pass.
    """
    from docutils.core import publish_parts
    from myst_parser.docutils_ import Parser

    from projecter.figures import protect_figure_grids, restore_figure_grids
    from projecter.latex import protect_tables, restore_tables
    from projecter.math import protect_math, restore_math
    from projecter.media import protect_media, restore_media

    markdown, tables = protect_tables(markdown)
    markdown, media = protect_media(markdown)
    markdown, grids = protect_figure_grids(markdown)
    # Math last, so it only scans prose (tables/media/grids are already pulled
    # out) and the markdown pass can't mangle the LaTeX inside the delimiters.
    markdown, maths = protect_math(markdown)
    parts = publish_parts(
        source=markdown,
        parser=Parser(),
        writer="html5",
        settings_overrides={"embed_stylesheet": False, "report_level": 5},
    )
    html = restore_tables(parts["body"], tables)
    html = restore_media(html, media)
    html = restore_figure_grids(html, grids)
    return restore_math(html, maths)


def _slugify(text: str) -> str:
    """Turn a heading into a stable, URL-safe anchor label."""
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_-]+", "-", slug) or "section"


def split_sections(body: str) -> list[Section]:
    """Split a markdown body into :class:`Section` blocks by ``##``/``###``.

    Each ``##`` or ``###`` heading starts a new section; the heading line
    becomes the section title and ``level`` (2 or 3), and the lines until the
    next heading become its rendered body. Content before the first heading is
    kept as a level-0 untitled preamble. Headings inside fenced code blocks are
    ignored.
    """
    heading_re = re.compile(r"^(#{2,3})\s+(.*?)\s*#*\s*$")
    fence_re = re.compile(r"^\s*(```|~~~)")

    chunks: list[tuple[int, str, list[str]]] = [(0, "", [])]
    in_fence = False
    for line in body.splitlines():
        if fence_re.match(line):
            in_fence = not in_fence
        match = None if in_fence else heading_re.match(line)
        if match:
            chunks.append((len(match.group(1)), match.group(2), []))
        else:
            chunks[-1][2].append(line)

    sections: list[Section] = []
    used: set[str] = set()
    for level, title, lines in chunks:
        text = "\n".join(lines).strip()
        if not title and not text:
            continue  # drop an empty preamble
        label = _slugify(title) if title else "preamble"
        # Disambiguate repeated headings so anchors stay unique.
        base, n = label, 2
        while label in used:
            label = f"{base}-{n}"
            n += 1
        used.add(label)
        sections.append(
            Section(label=label, title=title, html=myst_to_html(text), level=level or 2)
        )
    return sections


# A `field = value` pair inside an entry, where the value is `{...}`, "...", or
# a bare token (number). The brace form allows one level of nested braces so
# things like `{M{\"u}ller}` are captured whole.
_FIELD_RE = re.compile(
    r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"([^\"]*)\"|([^,}\s]+))",
    re.DOTALL,
)

# LaTeX accent/escape sequences that survive into reference text, mapped to the
# plain Unicode character so names like ``M{\"u}ller`` render as ``Müller``.
_LATEX_ACCENTS = {
    r'\"a': "ä", r'\"o': "ö", r'\"u': "ü", r'\"A': "Ä", r'\"O': "Ö",
    r'\"U': "Ü", r"\'e": "é", r"\'a": "á", r"\'o": "ó", r"\`e": "è",
    r"\^o": "ô", r"\~n": "ñ", r"\ss": "ß", r"\&": "&",
}


def _clean_latex(value: str) -> str:
    """Strip the LaTeX braces/accents that show up in BibTeX field values."""
    for tex, char in _LATEX_ACCENTS.items():
        value = value.replace("{" + tex + "}", char).replace(tex, char)
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", value).strip()


def _parse_fields(entry: str) -> dict[str, str]:
    """Extract the ``field = value`` pairs from a single BibTeX entry body."""
    body = entry.partition(",")[2]  # drop the `@type{key` preamble
    fields: dict[str, str] = {}
    for match in _FIELD_RE.finditer(body):
        name = match.group(1).lower()
        value = match.group(2) or match.group(3) or match.group(4) or ""
        fields[name] = _clean_latex(value)
    return fields


def _format_authors(raw: str) -> str:
    """Turn a BibTeX ``and``-separated author list into ``A, B and C``."""
    names = [a.strip() for a in re.split(r"\s+and\s+", raw) if a.strip()]
    # Normalise "Last, First" to "First Last" for readability.
    flipped = []
    for name in names:
        if "," in name:
            last, _, first = name.partition(",")
            name = f"{first.strip()} {last.strip()}".strip()
        flipped.append(name)
    if len(flipped) <= 1:
        return "".join(flipped)
    return ", ".join(flipped[:-1]) + " and " + flipped[-1]


def _render_citation(fields: dict[str, str], key: str) -> str:
    """Build a human-readable reference string from parsed BibTeX fields."""
    parts: list[str] = []
    if fields.get("author"):
        parts.append(_format_authors(fields["author"]) + ".")
    if fields.get("title"):
        parts.append(f"{fields['title']}.")
    venue = fields.get("journal") or fields.get("booktitle")
    if venue:
        parts.append(f"<em>{venue}</em>,")
    if fields.get("year"):
        parts.append(f"{fields['year']}.")
    return " ".join(parts) if parts else key


def parse_bibtex(text: str) -> list[Citation]:
    """Parse a BibTeX string into :class:`Citation` records.

    Splits top-level ``@entry{...}`` blocks, keeps the raw text for download,
    and renders each entry into a plain ``Author. Title. Venue, Year.`` string
    for the references list. The field parsing is deliberately lightweight (no
    external dependency); swap in ``pybtex`` if you need full citation styles.
    """
    citations: list[Citation] = []
    for chunk in text.split("@")[1:]:
        entry = "@" + chunk.strip()
        key = ""
        if "{" in entry:
            key = entry.split("{", 1)[1].split(",", 1)[0].strip()
        fields = _parse_fields(entry)
        citations.append(
            Citation(key=key, bibtex=entry, rendered=_render_citation(fields, key))
        )
    return citations


def parse_file(path: str | Path) -> Page:
    """Read a markdown file and assemble a :class:`Page` from it."""
    path = Path(path)
    meta, body = _split_front_matter(path.read_text(encoding="utf-8"))

    affiliations = {
        str(k): str(v) for k, v in (meta.get("affiliations") or {}).items()
    }
    metadata = Metadata(
        title=meta.get("title", path.stem),
        authors=_parse_authors(meta.get("authors")),
        affiliations=affiliations,
        badge=meta.get("badge"),
        venue=meta.get("venue"),
        links=_parse_links(meta.get("links")),
        description=meta.get("description"),
        keywords=meta.get("keywords") or [],
    )

    abstract = None
    if meta.get("abstract"):
        abstract = Abstract(html=myst_to_html(str(meta["abstract"])))

    citations: list[Citation] = []
    bib = meta.get("bibliography")
    if bib:
        bib_path = (path.parent / bib).resolve()
        if bib_path.exists():
            citations = parse_bibtex(bib_path.read_text(encoding="utf-8"))

    # "Cite this work" block: an explicit `bibtex:` string, or a `cite:` path
    # to a .bib file relative to the page.
    bibtex = meta.get("bibtex")
    cite = meta.get("cite")
    if not bibtex and cite:
        cite_path = (path.parent / cite).resolve()
        if cite_path.exists():
            bibtex = cite_path.read_text(encoding="utf-8").strip()

    acknowledgements = None
    if meta.get("acknowledgements"):
        acknowledgements = myst_to_html(str(meta["acknowledgements"]))

    return Page(
        metadata=metadata,
        abstract=abstract,
        sections=split_sections(body),
        citations=citations,
        bibtex=bibtex,
        acknowledgements=acknowledgements,
        source_path=str(path),
    )
