"""Shared fixtures for the projecter test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

# The canonical example page, also exercised by the integration tests. Keep it
# valid and in sync with the page format (see CLAUDE.md).
EXAMPLE = Path(__file__).parent.parent / "examples" / "index.md"


@pytest.fixture
def example_path() -> Path:
    """Path to the canonical example markdown page."""
    return EXAMPLE


@pytest.fixture
def write_md(tmp_path: Path):
    """Return a helper that writes markdown to a temp file and returns its path."""

    def _write(text: str, name: str = "page.md") -> Path:
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    return _write
