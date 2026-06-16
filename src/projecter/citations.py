"""Resolve pandoc-style ``[@key]`` inline citations against the bibliography.

MyST's own ``{cite}`` role lives in ``sphinxcontrib-bibtex`` and needs a full
Sphinx build; this project renders with the bare docutils frontend, so inline
citations are handled here with the same two-phase strategy as
:mod:`projecter.math` and :mod:`projecter.figures`:

* :func:`protect_citations` turns each ``[@key]`` (or ``[@a; @b]``) into the
  rendered ``[<a href="#cite-key">n</a>]`` HTML and leaves a placeholder in the
  markdown (so the markdown pass can't escape the raw ``<a>``).
* :func:`restore_citations` swaps the rendered links back in afterwards.

The number ``n`` is the entry's 1-based position in the bibliography, which is
the order the ``<ol>`` of references is rendered in (see ``page.html.jinja``), so
clicking ``[3]`` jumps to the third reference. An unknown key renders as ``[?]``
so a typo is visible rather than silently dropped.
"""

from __future__ import annotations

import re

# A bracketed citation: one or more ``@key`` tokens separated by ``;``. Keys use
# the usual BibTeX character set. ``[text](url)`` / ``[^note]`` don't match (no
# leading ``@``), so normal markdown links and footnotes are left alone.
_KEY = r"[\w.:+/-]+"
_CITE_RE = re.compile(rf"\[(@{_KEY}(?:\s*;\s*@{_KEY})*)\]")

_PLACEHOLDER = "CITEPLACEHOLDER{}CITE"


def _render_group(keys: list[str], numbering: dict[str, int]) -> str:
    """Render ``[1, 2]`` for a group of keys, each number linked to its entry."""
    parts: list[str] = []
    for key in keys:
        num = numbering.get(key)
        if num is None:
            parts.append("?")  # key not in the bibliography
        else:
            parts.append(f'<a href="#cite-{key}" class="citation">{num}</a>')
    return "[" + ", ".join(parts) + "]"


def protect_citations(
    text: str, numbering: dict[str, int]
) -> tuple[str, list[str]]:
    """Replace ``[@key]`` spans with placeholders; return the rendered links."""
    spans: list[str] = []

    def repl(match: re.Match[str]) -> str:
        keys = [k.strip().lstrip("@") for k in match.group(1).split(";")]
        spans.append(_render_group(keys, numbering))
        return _PLACEHOLDER.format(len(spans) - 1)

    return _CITE_RE.sub(repl, text), spans


def restore_citations(html_text: str, spans: list[str]) -> str:
    """Swap rendered placeholders back for their citation links."""
    for i, span in enumerate(spans):
        html_text = html_text.replace(_PLACEHOLDER.format(i), span)
    return html_text
