"""Protect LaTeX math spans from the markdown pass.

Math is rendered client-side by MathJax (see the template), so the ``$...$`` /
``$$...$$`` delimiters need to survive into the output verbatim. Left to the
markdown processor, characters inside the math — underscores, asterisks — are
treated as formatting and ``<em>`` tags get injected *into* the math, which
breaks MathJax (e.g. ``\\hat{e}_{||} ... \\hat{e}_{\\perp}`` becomes an emphasis
span). We pull the math out before rendering and splice it back afterwards, the
same two-phase trick used in :mod:`projecter.latex` and :mod:`projecter.media`.
"""

from __future__ import annotations

import re

_PLACEHOLDER = "MATHJAXPLACEHOLDER{}MATHJAX"

# Display delimiters are matched before inline ones so ``$$`` / ``\[`` are not
# half-consumed by the ``$`` / ``\(`` patterns. Each pattern captures the whole
# span (delimiters included) so it can be restored verbatim.
_PATTERNS = (
    re.compile(r"\$\$.+?\$\$", re.DOTALL),
    re.compile(r"\\\[.+?\\\]", re.DOTALL),
    re.compile(r"\\\(.+?\\\)", re.DOTALL),
    # Inline ``$...$``: single line, and not the start of a ``$$`` block.
    re.compile(r"\$(?!\$)[^\n]+?\$"),
)


def protect_math(text: str) -> tuple[str, list[str]]:
    """Replace LaTeX math spans with placeholders; return the raw spans."""
    spans: list[str] = []

    def repl(match: re.Match[str]) -> str:
        spans.append(match.group(0))
        return _PLACEHOLDER.format(len(spans) - 1)

    for pattern in _PATTERNS:
        text = pattern.sub(repl, text)
    return text, spans


def restore_math(html: str, spans: list[str]) -> str:
    """Swap rendered placeholders back for their original math spans."""
    for i, span in enumerate(spans):
        token = _PLACEHOLDER.format(i)
        # A display span alone in a paragraph is unwrapped so it renders as a
        # block; an inline span is spliced straight back into its paragraph.
        html = html.replace(f"<p>{token}</p>", span).replace(token, span)
    return html
