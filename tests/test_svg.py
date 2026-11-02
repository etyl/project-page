"""Tests for SVG inlining in ``svg.py``."""

from __future__ import annotations

from pathlib import Path

from projecter.svg import inline_svgs

SVG = (
    '<?xml version="1.0"?>\n<svg width="100pt" height="50pt" viewBox="0 0 100 50">'
    '<clipPath id="c"><rect/></clipPath><g clip-path="url(#c)"><text>Hi</text></g>'
    '<use xlink:href="#c"/><a href="#elsewhere"/></svg>'
)


def test_inline_svgs(tmp_path: Path) -> None:
    (tmp_path / "a.svg").write_text(SVG)
    html = '<img src="a.svg" alt="A"><img src="a.svg"><img src="missing.svg">'
    out = inline_svgs(html, tmp_path)
    assert "<?xml" not in out and "<text>Hi</text>" in out
    # Ids are prefixed per inlined SVG so the two copies don't collide.
    assert 'id="svg1-c"' in out and 'url(#svg1-c)' in out and 'href="#svg1-c"' in out
    assert 'id="svg2-c"' in out
    # References to ids outside the SVG are left alone.
    assert 'href="#elsewhere"' in out
    assert 'width="100pt"' not in out and "max-width:100pt" in out
    assert 'aria-label="A"' in out
    assert '<img src="missing.svg">' in out
