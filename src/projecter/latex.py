"""Convert LaTeX ``tabular`` / ``table`` environments into HTML tables.

MathJax only renders math-mode constructs, so full ``tabular`` markup (column
specs, ``\\hline``, ``\\multicolumn``, booktabs rules, ...) has to be turned
into real HTML ourselves. The first row is treated as the header.

Usage is two-phase so the conversion survives the markdown pass:

* :func:`protect_tables` pulls the LaTeX environments out of the markdown and
  leaves a plain-text placeholder in their place (before MyST rendering).
* :func:`restore_tables` swaps the rendered HTML tables back in afterwards.
"""

from __future__ import annotations

import re

# `\begin{table}...\end{table}` (optionally starred) wrapping a tabular, and a
# bare `\begin{tabular}{spec}...\end{tabular}`.
_TABLE_RE = re.compile(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", re.DOTALL)
_TABULAR_RE = re.compile(
    r"\\begin\{tabular\}\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}(.*?)\\end\{tabular\}",
    re.DOTALL,
)
_CAPTION_RE = re.compile(r"\\caption\{(.*?)\}", re.DOTALL)
_LABEL_RE = re.compile(r"\\label\{(.*?)\}")

_PLACEHOLDER = "LTXTABLEPLACEHOLDER{}LTX"

_ALIGN = {"l": "left", "c": "center", "r": "right"}
_RULES = ("\\hline", "\\toprule", "\\midrule", "\\bottomrule")


def _parse_aligns(spec: str) -> list[str]:
    """Map a column spec like ``|l|cc|r`` to per-column CSS alignments."""
    spec = re.sub(r"@\{[^}]*\}", "", spec)  # drop @{...} inter-column material
    spec = re.sub(r"[pmb]\{[^}]*\}", "l", spec)  # p/m/b{width} -> left aligned
    spec = spec.replace("|", "")
    return [_ALIGN[ch] for ch in spec if ch in _ALIGN]


def _format_cell(cell: str) -> str:
    """Convert the common inline LaTeX text commands inside a cell to HTML."""
    cell = cell.strip()
    cell = re.sub(r"\\textbf\{([^{}]*)\}", r"<strong>\1</strong>", cell)
    cell = re.sub(r"\\(?:textit|emph)\{([^{}]*)\}", r"<em>\1</em>", cell)
    cell = re.sub(r"\\texttt\{([^{}]*)\}", r"<code>\1</code>", cell)
    # Unescape the LaTeX escapes that survive into text.
    cell = cell.replace(r"\&", "&amp;").replace(r"\%", "%").replace(r"\_", "_")
    return cell.strip()


def _split_cells(row: str) -> list[str]:
    """Split a row on unescaped ``&``."""
    return re.split(r"(?<!\\)&", row)


def _render_row(row: str, aligns: list[str], header: bool) -> str:
    tag = "th" if header else "td"
    cells_html: list[str] = []
    for i, raw in enumerate(_split_cells(row)):
        raw = raw.strip()
        span = ""
        align = aligns[i] if i < len(aligns) else "left"
        mc = re.match(r"\\multicolumn\{(\d+)\}\{([^}]*)\}\{(.*)\}$", raw, re.DOTALL)
        if mc:
            span = f' colspan="{mc.group(1)}"'
            align = next((_ALIGN[c] for c in mc.group(2) if c in _ALIGN), align)
            raw = mc.group(3)
        cells_html.append(
            f'<{tag} style="text-align:{align}"{span}>{_format_cell(raw)}</{tag}>'
        )
    return "<tr>" + "".join(cells_html) + "</tr>"


def tabular_to_html(spec: str, body: str) -> str:
    """Convert the inside of a ``tabular`` environment to ``<table>`` HTML."""
    aligns = _parse_aligns(spec)
    for rule in _RULES:
        body = body.replace(rule, "")
    body = re.sub(r"\\cline\{[^}]*\}", "", body)

    rows = [r.strip() for r in re.split(r"\\\\(?:\[[^\]]*\])?", body)]
    rows = [r for r in rows if r]
    if not rows:
        return ""

    head = _render_row(rows[0], aligns, header=True)
    body_rows = "".join(_render_row(r, aligns, header=False) for r in rows[1:])
    return (
        '<table class="latex-table">'
        f"<thead>{head}</thead><tbody>{body_rows}</tbody></table>"
    )


def _env_to_html(env: str) -> str:
    """Convert a full matched environment (table or bare tabular) to HTML."""
    inner = _TABULAR_RE.search(env)
    if not inner:
        return ""
    table_html = tabular_to_html(inner.group(1), inner.group(2))

    caption = _CAPTION_RE.search(env)
    label = _LABEL_RE.search(env)
    if caption or label:
        attr = f' id="{label.group(1)}"' if label else ""
        cap = f"<figcaption>{_format_cell(caption.group(1))}</figcaption>" if caption else ""
        return f'<figure class="latex-table-figure"{attr}>{table_html}{cap}</figure>'
    return table_html


def protect_tables(text: str) -> tuple[str, list[str]]:
    """Replace LaTeX table environments with placeholders; return their HTML."""
    tables: list[str] = []

    def repl(match: re.Match[str]) -> str:
        tables.append(_env_to_html(match.group(0)))
        return f"\n\n{_PLACEHOLDER.format(len(tables) - 1)}\n\n"

    # `table` first so its inner `tabular` isn't matched twice.
    text = _TABLE_RE.sub(repl, text)
    text = _TABULAR_RE.sub(repl, text)
    return text, tables


def restore_tables(html: str, tables: list[str]) -> str:
    """Swap rendered placeholders back for their HTML tables."""
    for i, table in enumerate(tables):
        token = _PLACEHOLDER.format(i)
        html = html.replace(f"<p>{token}</p>", table).replace(token, table)
    return html
