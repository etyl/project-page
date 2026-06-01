"""Convert a ``{figure-grid}`` directive into a row/grid of figures.

MyST renders a single ``{figure}`` natively (and honours its ``:width:``
option), but there is no built-in way to lay several figures out side by side.
This module adds a ``{figure-grid}`` directive using the same two-phase strategy
as :mod:`projecter.media` and :mod:`projecter.latex`:

* :func:`protect_figure_grids` pulls the fenced ``{figure-grid}`` blocks out of
  the markdown and leaves a placeholder (before MyST rendering).
* :func:`restore_figure_grids` swaps the rendered HTML grids back in afterwards.

A block lists one image per line, with an optional ``| caption`` per cell::

    ```{figure-grid}
    :label: fig-benchmarks
    :columns: 2
    :caption: Scaling with batch size and face count.

    static/images/benchmark_batch_size.svg | Varying batch size
    static/images/benchmark_facecount.svg | Varying face count
    ```

Options: ``:columns:`` (cells per row, default = number of cells),
``:gap:`` (CSS gap, default ``24px``), ``:label:`` (id on the wrapping figure)
and ``:caption:`` (a caption for the whole grid).
"""

from __future__ import annotations

import html
import re

# A fenced ``{figure-grid}`` directive: body holds ``:option:`` lines followed
# by one ``path | caption`` image spec per line.
_GRID_RE = re.compile(
    r"^```\{figure-grid\}[ \t]*\n(.*?)^```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)
_OPTION_RE = re.compile(r"^:([\w-]+):[ \t]*(.*?)[ \t]*$")

_PLACEHOLDER = "FIGGRIDPLACEHOLDER{}FIGGRID"


def _parse_body(body: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Split a directive body into options and ``(src, caption)`` cells."""
    options: dict[str, str] = {}
    cells: list[tuple[str, str]] = []
    in_cells = False
    for line in body.splitlines():
        stripped = line.strip()
        match = _OPTION_RE.match(line)
        if match and not in_cells:
            options[match.group(1).lower()] = match.group(2)
            continue
        if not stripped:
            in_cells = True  # blank line ends the option block
            continue
        in_cells = True
        src, sep, caption = stripped.partition("|")
        cells.append((src.strip(), caption.strip() if sep else ""))
    return options, cells


def _cell_html(src: str, caption: str) -> str:
    src_attr = html.escape(src, quote=True)
    alt = html.escape(caption) if caption else html.escape(src.rsplit("/", 1)[-1])
    cap = f"<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
    return (
        '<figure class="figure-grid-item">'
        f'<img src="{src_attr}" alt="{alt}">{cap}'
        "</figure>"
    )


def _grid_to_html(body: str) -> str:
    options, cells = _parse_body(body)
    if not cells:
        return ""
    cols = options.get("columns") or str(len(cells))
    gap = options.get("gap") or "24px"
    style = f"--figgrid-cols:{html.escape(cols, quote=True)};--figgrid-gap:{html.escape(gap, quote=True)}"
    attr = f' id="{html.escape(options["label"], quote=True)}"' if "label" in options else ""
    items = "".join(_cell_html(src, caption) for src, caption in cells)
    grid = f'<div class="figure-grid-items" style="{style}">{items}</div>'
    caption = options.get("caption", "")
    cap = (
        f'<figcaption class="figure-grid-caption">{html.escape(caption)}</figcaption>'
        if caption
        else ""
    )
    return f'<figure class="figure-grid"{attr}>{grid}{cap}</figure>'


def protect_figure_grids(text: str) -> tuple[str, list[str]]:
    """Replace ``{figure-grid}`` directives with placeholders."""
    grids: list[str] = []

    def repl(match: re.Match[str]) -> str:
        grids.append(_grid_to_html(match.group(1)))
        return f"\n\n{_PLACEHOLDER.format(len(grids) - 1)}\n\n"

    return _GRID_RE.sub(repl, text), grids


def restore_figure_grids(html_text: str, grids: list[str]) -> str:
    """Swap rendered placeholders back for their figure grids."""
    for i, grid in enumerate(grids):
        token = _PLACEHOLDER.format(i)
        html_text = html_text.replace(f"<p>{token}</p>", grid).replace(token, grid)
    return html_text
