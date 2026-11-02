"""Discover project-page markdown files and build their HTML siblings."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from projecter.parser import _split_front_matter, parse_file
from projecter.renderer import render_page
from projecter.svg import inline_svgs


def is_project_page(path: Path) -> bool:
    """Return True if a markdown file looks like a project page.

    Heuristic: it has YAML front matter declaring a ``title``. Adjust this to
    whatever marks a page in your project (e.g. a ``projecter: true`` flag).
    """
    try:
        meta, _ = _split_front_matter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return False
    return bool(meta.get("title")) or bool(meta.get("projecter"))


def find_pages(root: str | Path, pattern: str = "*.md") -> list[Path]:
    """Recursively find markdown files under ``root`` that are project pages."""
    root = Path(root)
    return sorted(p for p in root.rglob(pattern) if is_project_page(p))


def build_file(path: str | Path) -> Path:
    """Build a single markdown file into an HTML file in the same directory."""
    path = Path(path)
    page = parse_file(path)
    html = inline_svgs(render_page(page, page.metadata.template), path.parent)
    out_path = path.with_suffix(".html")
    out_path.write_text(html, encoding="utf-8")
    return out_path


def build_all(root: str | Path) -> list[Path]:
    """Build every project page found under ``root``. Returns output paths."""
    outputs: list[Path] = []
    for md in find_pages(root):
        outputs.append(build_file(md))
    return outputs


def build_paths(paths: Iterable[str | Path]) -> list[Path]:
    """Build an explicit list of markdown files."""
    return [build_file(p) for p in paths]
