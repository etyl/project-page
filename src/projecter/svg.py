"""Inline local ``<img src="*.svg">`` as ``<svg>`` elements.

An SVG loaded through ``<img>`` is rasterised as an opaque image: its text can't
be selected or searched. Inlining keeps it a vector graphic in the page DOM.
Runs on the final HTML, so it covers MyST figures and ``{figure-grid}`` alike.

Each inlined SVG gets its ids prefixed (``svgN-``), since tools like matplotlib
reuse the same ids (``patch_1``, clip paths, ...) across files and they would
otherwise collide once several SVGs share one document.
"""

from __future__ import annotations

import re
from pathlib import Path

_IMG_RE = re.compile(r'<img\b[^>]*\bsrc="([^"]+\.svg)"[^>]*>', re.IGNORECASE)
_ALT_RE = re.compile(r'\balt="([^"]*)"')
_ID_RE = re.compile(r'\bid="([^"]+)"')
_REF_RE = re.compile(r'(url\(#|href="#)([^)"]+)')
_ROOT_RE = re.compile(r"<svg\b[^>]*>")
_SIZE_RE = re.compile(r'\s(width|height)="([^"]*)"')


def _inline(svg: str, prefix: str, alt: str) -> str:
    svg = svg[svg.index("<svg"):]  # drop the XML prolog / doctype
    ids = set(_ID_RE.findall(svg))
    svg = _ID_RE.sub(lambda m: f'id="{prefix}{m.group(1)}"', svg)
    svg = _REF_RE.sub(
        lambda m: m.group(1) + prefix + m.group(2) if m.group(2) in ids else m.group(0),
        svg,
    )
    root = _ROOT_RE.match(svg).group(0)
    new_root = root[:-1]
    if "viewBox" in root:
        # Scale with the column like an <img>, but never past the natural width.
        width = dict(_SIZE_RE.findall(root)).get("width")
        new_root = _SIZE_RE.sub("", new_root)
        max_w = f"max-width:{width};" if width else ""
        new_root += f' style="display:block;margin:0 auto;width:100%;height:auto;{max_w}"'
    new_root += f' role="img" aria-label="{alt}">'
    return new_root + svg[len(root):]


def inline_svgs(html_text: str, base: Path) -> str:
    """Replace ``<img>`` tags pointing at local SVG files with the SVG itself."""
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        src = match.group(1)
        path = base / src
        if "://" in src or not path.is_file():
            return match.group(0)
        count += 1
        alt = _ALT_RE.search(match.group(0))
        return _inline(
            path.read_text(encoding="utf-8"), f"svg{count}-", alt.group(1) if alt else ""
        )

    return _IMG_RE.sub(repl, html_text)
