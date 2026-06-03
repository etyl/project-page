# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e ".[dev]"   # install with dev tools (pytest, ruff, mypy)

projecter build              # build every page under the current directory
projecter build examples/    # build under a directory
projecter build page.md      # build a single file -> page.html

pytest                       # run all tests
pytest tests/test_projecter.py::test_math_underscores_not_mangled  # one test
ruff check .                 # lint (line-length 88)
mypy src                     # type-check (strict)
```

`mypy` runs in `strict` mode and `ruff`/`mypy` target an older Python than
`requires-python` (py39 vs 3.10) — keep syntax compatible with 3.9 (e.g. the
`from __future__ import annotations` at the top of every module enables the
`X | Y` / `list[...]` annotations used throughout).

## Architecture

`projecter` turns a MyST-markdown file into a single self-contained HTML page,
written **next to the source** (`page.md` → `page.html`). The flow is:

`cli` → `builder` (discover + orchestrate) → `parser` (markdown → `Page`) →
`renderer` (`Page` → HTML via Jinja).

- **`blocks.py`** — the data model. Plain dataclasses (`Page`, `Metadata`,
  `Author`, `Link`, `Section`, `Citation`, `Abstract`, `Figure`). The parser
  fills them; the template reads them. `Page.html`/`Section.html` fields hold
  **already-rendered HTML fragments**, not markdown.
- **`parser.py`** — front matter (YAML) + body (MyST) + optional BibTeX → `Page`.
  Sections are split by scanning `##`/`###` headings line-by-line
  (`split_sections`), tracking fenced code so headings inside code blocks are
  ignored, and slugifying titles into unique anchors. BibTeX is parsed with a
  lightweight regex (no `pybtex`) into `Citation` records.
- **`renderer.py`** — one Jinja environment, autoescape on, loads
  `templates/page.html.jinja`. Note: section/abstract HTML is injected via
  `| safe` in the template since it's pre-rendered.
- **`builder.py`** — `is_project_page()` is the discovery heuristic: a `.md` file
  counts if its front matter has a `title` (or `projecter:` flag). `find_pages`
  recurses; `build_file` writes the HTML sibling.

### The protect/restore pipeline (most important to understand)

`parser.myst_to_html()` is the heart of rendering. MyST/docutils would mangle
LaTeX math, LaTeX tables, and custom directives, so each of those is **pulled
out before the markdown pass and spliced back after** ("two-phase trick").
Every helper module exposes a matching `protect_*` / `restore_*` pair that
swaps spans for a unique placeholder token (e.g. `MATHJAXPLACEHOLDER0MATHJAX`):

| Module | Handles | Placeholder |
| --- | --- | --- |
| `latex.py` | `\begin{tabular}`/`{table}` → HTML tables | `LTXTABLEPLACEHOLDER` |
| `media.py` | `{video}`/`{audio}` directives (incl. YouTube embeds) | `MEDIAPLACEHOLDER` |
| `figures.py` | `{figure-grid}` directive → side-by-side figures | `FIGGRIDPLACEHOLDER` |
| `math.py` | `$...$` / `$$...$$` / `\(...\)` / `\[...\]` (left for MathJax) | `MATHJAXPLACEHOLDER` |

**Order matters** in `myst_to_html`: tables, media, and grids are protected
first; **math is protected last** so it only scans remaining prose (the others
are already extracted) and the markdown pass can't inject `<em>` into formulas.
On restore, math unwraps a `<p>placeholder</p>` so a display equation renders as
a block. When adding a new directive/syntax, follow this same pattern and make
sure tests assert the placeholder never leaks into the output.

Single `{figure}` directives are handled natively by MyST (no protect needed);
only the multi-image `{figure-grid}` is custom.

## Conventions

- Pages model academic project pages (Nerfies/NRMF-style layout); front-matter
  fields map directly onto `Metadata` (`authors`, `affiliations`, `badge`,
  `venue`, `links`, `bibliography`, `cite`/`bibtex`, `acknowledgements`).
- Several behaviours are intentionally left as `TODO` stubs to specialise
  (further section splitting into `Figure` blocks, full citation styling,
  inline citation resolution).
- `examples/index.md` is the canonical example and is used directly by the test
  suite — keep it valid and in sync when changing the page format.
