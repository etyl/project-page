"""Tests for discovery and building in ``builder.py``."""

from __future__ import annotations

from projecter.builder import (
    build_all,
    build_file,
    build_paths,
    find_pages,
    is_project_page,
)


# --- is_project_page ------------------------------------------------------


def test_is_project_page_for_example(example_path) -> None:
    assert is_project_page(example_path)


def test_is_project_page_true_for_title(write_md) -> None:
    assert is_project_page(write_md('---\ntitle: "T"\n---\nbody\n'))


def test_is_project_page_true_for_flag(write_md) -> None:
    assert is_project_page(write_md("---\nprojecter: true\n---\nbody\n"))


def test_is_project_page_false_without_front_matter(write_md) -> None:
    assert not is_project_page(write_md("# Just a heading\n"))


def test_is_project_page_false_for_title_less_front_matter(write_md) -> None:
    assert not is_project_page(write_md("---\nauthor: X\n---\nbody\n"))


def test_is_project_page_false_for_missing_file(tmp_path) -> None:
    assert not is_project_page(tmp_path / "nope.md")


# --- find_pages -----------------------------------------------------------


def test_find_pages_recurses_and_filters(tmp_path, write_md) -> None:
    write_md('---\ntitle: "A"\n---\nx\n', name="a.md")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "b.md").write_text('---\ntitle: "B"\n---\ny\n', encoding="utf-8")
    (tmp_path / "ignore.md").write_text("no front matter\n", encoding="utf-8")
    pages = find_pages(tmp_path)
    names = [p.name for p in pages]
    assert names == ["a.md", "b.md"]


def test_find_pages_sorted(tmp_path) -> None:
    for name in ["z.md", "a.md", "m.md"]:
        (tmp_path / name).write_text('---\ntitle: "T"\n---\n', encoding="utf-8")
    pages = find_pages(tmp_path)
    assert pages == sorted(pages)


def test_find_pages_accepts_str_root(tmp_path, write_md) -> None:
    write_md('---\ntitle: "A"\n---\n', name="a.md")
    assert find_pages(str(tmp_path))


def test_find_pages_empty_dir(tmp_path) -> None:
    assert find_pages(tmp_path) == []


# --- build_file -----------------------------------------------------------


def test_build_file_writes_sibling_html(tmp_path) -> None:
    md = tmp_path / "page.md"
    md.write_text('---\ntitle: "T"\n---\n\n# Hello\n', encoding="utf-8")
    out = build_file(md)
    assert out == tmp_path / "page.html"
    assert out.exists()
    assert "<title>T</title>" in out.read_text(encoding="utf-8")


def test_build_file_accepts_str_path(tmp_path) -> None:
    md = tmp_path / "page.md"
    md.write_text('---\ntitle: "S"\n---\n\nbody\n', encoding="utf-8")
    out = build_file(str(md))
    assert out.read_text(encoding="utf-8")


def test_build_file_uses_selected_template(tmp_path) -> None:
    md = tmp_path / "page.md"
    md.write_text('---\ntitle: "T"\ntemplate: ml-blog\n---\n\nbody\n', encoding="utf-8")
    out = build_file(md)
    assert "<title>" in out.read_text(encoding="utf-8")


# --- build_all / build_paths ----------------------------------------------


def test_build_all_returns_outputs(tmp_path) -> None:
    (tmp_path / "a.md").write_text('---\ntitle: "A"\n---\nx\n', encoding="utf-8")
    (tmp_path / "b.md").write_text('---\ntitle: "B"\n---\ny\n', encoding="utf-8")
    outputs = build_all(tmp_path)
    assert {p.name for p in outputs} == {"a.html", "b.html"}
    assert all(p.exists() for p in outputs)


def test_build_all_empty_dir(tmp_path) -> None:
    assert build_all(tmp_path) == []


def test_build_paths_explicit_list(tmp_path) -> None:
    a = tmp_path / "a.md"
    a.write_text('---\ntitle: "A"\n---\nx\n', encoding="utf-8")
    outputs = build_paths([a])
    assert outputs == [tmp_path / "a.html"]
    assert outputs[0].exists()


def test_build_inlines_css(tmp_path) -> None:
    (tmp_path / "s.css").write_text(".mine { color: red; }", encoding="utf-8")
    a = tmp_path / "a.md"
    a.write_text('---\ntitle: "A"\ncss: s.css\n---\nx\n', encoding="utf-8")
    html = build_file(a).read_text(encoding="utf-8")
    assert ".mine { color: red; }" in html.split("</head>")[0]
