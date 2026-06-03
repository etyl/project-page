# projecter

Generate static HTML project pages from MyST markdown — built for research
paper landing pages. Point it at a directory, and for every markdown file that
looks like a project page it renders an `.html` file **next to the source**.

Supports citations (BibTeX), equations (MathJax), and structured blocks:
metadata (title/authors/venue/links), abstract, sections, figures, and references.

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```bash
projecter build              # build every page under the current directory
projecter build examples/    # build every page under a directory
projecter build page.md      # build a single file -> page.html
```

## Page format

A page is a markdown file with YAML front matter plus a MyST body:

```markdown
---
title: "My Research Project"
authors:
  - name: Jane Doe
    affiliation: 1
venue: "Conference 2026"
abstract: |
  Supports inline math like $E = mc^2$.
bibliography: refs.bib
---

## Introduction

Display math, figures and citations go here.
```

See [examples/index.md](examples/index.md) for a complete example.

## Templates

Pages render with the modern Bulma-based layout by default. Pick a different
template per page with a `template:` front-matter key, using a short name:

```yaml
---
title: "My Research Project"
template: ml-blog
---
```

Available templates (registered in [renderer.py](src/projecter/renderer.py),
files in [src/projecter/templates/](src/projecter/templates/)):

| Name | File | Look |
| --- | --- | --- |
| `ml-page` (default) | `page.html.jinja` | Modern academic project page (Bulma, Inter, gradient hero) |
| `ml-blog` | `latex.html.jinja` | Classic LaTeX article style — Computer Modern type, single column, numbered sections, justified text |

The `template:` value may also be a raw template filename. Both templates
consume the same `Page` data (metadata, abstract, sections, figures, citations,
BibTeX), so any page can switch between them by changing one line.

## Headings and tables

* `##` renders as a section title.
* `###` renders as a titled box (panel).
* Tables can be written as markdown pipe tables **or** as LaTeX, e.g.

  ```latex
  \begin{table}
  \caption{Results.}
  \label{tab-results}
  \begin{tabular}{lcc}
  \toprule
  Method & PSNR $\uparrow$ & Time $\downarrow$ \\
  \midrule
  \textbf{Ours} & \textbf{31.4} & \textbf{1.8 min} \\
  \bottomrule
  \end{tabular}
  \end{table}
  ```

  The first row is the header; `\hline`/booktabs rules, column alignment,
  `\multicolumn`, `\textbf`/`\emph`/`\texttt`, `\caption` and `\label` are
  supported. See [latex.py](src/projecter/latex.py).

## Figures

A single figure uses the MyST `{figure}` directive. Set its size with
`:width:` (any CSS length or percentage):

````markdown
```{figure} static/images/diagram.svg
:label: fig-diagram
:width: 60%
:alt: System diagram

An optional caption.
```
````

To lay several figures out side by side, use `{figure-grid}` — one image per
line, with an optional `| caption` per cell:

````markdown
```{figure-grid}
:label: fig-benchmarks
:columns: 2
:caption: Runtime scaling with batch size and face count.

static/images/benchmark_batch_size.svg | Varying batch size
static/images/benchmark_facecount.svg | Varying face count
```
````

Options: `:columns:` (cells per row, default = number of cells), `:gap:` (CSS
gap, default `24px`), `:label:` (id on the wrapping figure) and `:caption:` (a
caption for the whole grid). The grid collapses to a single column on narrow
screens. See [figures.py](src/projecter/figures.py).

## Video and audio

Embed media with the `{video}` and `{audio}` directives anywhere in the body
(same fenced-directive syntax as `{figure}`):

````markdown
```{video} static/videos/demo.mp4
:poster: static/images/thumb.png
:width: 80%
:autoplay:
:loop:
:muted:

An optional caption rendered beneath the player.
```

```{audio} static/audio/podcast.m4a
:label: fig-podcast

AI-generated podcast (paper introduction).
```
````

Both get `controls` and a sensible MIME type inferred from the file extension.
For `{video}`, `:width:`/`:poster:` take values and `:autoplay:`/`:loop:`/
`:muted:`/`:playsinline:` are flags. `:label:` sets the `<figure>` id and the
caption is the trailing text. See [media.py](src/projecter/media.py).

`{video}` also accepts a **YouTube URL** (`watch?v=`, `youtu.be/`, `embed/` or
`shorts/`) instead of a file, and renders a responsive privacy-friendly embed:

````markdown
```{video} https://youtu.be/dQw4w9WgXcQ?t=1m30s
:width: 80%

Our video presentation.
```
````

A `t=`/`start=` offset on the URL is honoured, and `:autoplay:`/`:muted:`/
`:loop:` map to the embed's playback parameters.

## Layout

| Module | Responsibility |
| --- | --- |
| [blocks.py](src/projecter/blocks.py) | Dataclasses for the page blocks (Metadata, Abstract, Section, Figure, Citation, Page) |
| [parser.py](src/projecter/parser.py) | Markdown + front matter + BibTeX → `Page`; MyST → HTML; section splitting |
| [latex.py](src/projecter/latex.py) | LaTeX `tabular`/`table` → HTML tables |
| [math.py](src/projecter/math.py) | Protect `$...$`/`$$...$$` from the markdown pass (for MathJax) |
| [media.py](src/projecter/media.py) | `{video}`/`{audio}` directives → HTML players |
| [figures.py](src/projecter/figures.py) | `{figure-grid}` directive → side-by-side figures |
| [renderer.py](src/projecter/renderer.py) | `Page` → HTML via the Jinja template |
| [builder.py](src/projecter/builder.py) | Discover pages and write HTML siblings |
| [cli.py](src/projecter/cli.py) | `projecter build` command |
| [templates/page.html.jinja](src/projecter/templates/page.html.jinja) | Default HTML page template (modern academic layout) |
| [templates/latex.html.jinja](src/projecter/templates/latex.html.jinja) | Classic LaTeX article-style template |

Some pieces are deliberately left as stubs (marked with `TODO`) to fill in:
splitting sections further into `Figure` blocks, rendering BibTeX into a
citation style, and resolving inline citation references.

## Development

```bash
pytest        # run tests
ruff check .  # lint
mypy src      # type-check
```
