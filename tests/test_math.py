"""Tests for math span protection in ``math.py``."""

from __future__ import annotations

from projecter.math import protect_math, restore_math


def test_protect_inline_math() -> None:
    protected, spans = protect_math("Energy is $E = mc^2$ here.")
    assert "MATHJAXPLACEHOLDER" in protected
    assert spans == ["$E = mc^2$"]


def test_protect_display_math_double_dollar() -> None:
    protected, spans = protect_math("$$\na + b\n$$")
    assert spans == ["$$\na + b\n$$"]
    assert "$" not in protected


def test_protect_display_math_bracket() -> None:
    _, spans = protect_math(r"\[a + b\]")
    assert spans == [r"\[a + b\]"]


def test_protect_inline_math_paren() -> None:
    _, spans = protect_math(r"text \(x_i\) text")
    assert spans == [r"\(x_i\)"]


def test_display_matched_before_inline() -> None:
    # The `$$...$$` block must be captured whole, not as two inline `$...$`.
    _, spans = protect_math("$$ x $$")
    assert spans == ["$$ x $$"]


def test_multiple_spans_indexed() -> None:
    protected, spans = protect_math("$a$ and $b$")
    assert len(spans) == 2
    assert "MATHJAXPLACEHOLDER0MATHJAX" in protected
    assert "MATHJAXPLACEHOLDER1MATHJAX" in protected


def test_inline_does_not_cross_newline() -> None:
    # A lone `$` on separate lines is not a single inline span.
    _, spans = protect_math("cost is $5 today\nand $6 tomorrow")
    assert spans == []


def test_restore_round_trips() -> None:
    protected, spans = protect_math("Inline $x$ and block:\n\n$$\ny\n$$\n")
    restored = restore_math(protected, spans)
    assert "$x$" in restored
    assert "$$\ny\n$$" in restored
    assert "MATHJAXPLACEHOLDER" not in restored


def test_restore_unwraps_display_paragraph() -> None:
    # A placeholder alone in a <p> (as docutils would wrap a display block)
    # is unwrapped so the equation renders as a block.
    _, spans = protect_math("$$\ny\n$$")
    out = restore_math("<p>MATHJAXPLACEHOLDER0MATHJAX</p>", spans)
    assert out == "$$\ny\n$$"


def test_restore_keeps_inline_in_paragraph() -> None:
    _, spans = protect_math("$x$")
    out = restore_math("<p>cost MATHJAXPLACEHOLDER0MATHJAX here</p>", spans)
    assert out == "<p>cost $x$ here</p>"


def test_no_math_is_noop() -> None:
    protected, spans = protect_math("plain text, $ alone")
    assert spans == []
    assert protected == "plain text, $ alone"
