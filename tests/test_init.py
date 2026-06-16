"""Tests for the package's public API surface (``projecter/__init__.py``)."""

from __future__ import annotations

import projecter


def test_version() -> None:
    assert projecter.__version__ == "0.1.0"


def test_public_dataclasses_are_exported() -> None:
    # Everything advertised in __all__ should be importable from the top level.
    for name in projecter.__all__:
        assert hasattr(projecter, name), f"{name} missing from projecter"


def test_all_lists_every_block() -> None:
    expected = {
        "Abstract",
        "Author",
        "Citation",
        "Figure",
        "Link",
        "Metadata",
        "Page",
        "Section",
        "__version__",
    }
    assert set(projecter.__all__) == expected
