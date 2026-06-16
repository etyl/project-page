"""Tests for the command-line entry point in ``cli.py``."""

from __future__ import annotations

import pytest

from projecter.cli import main


def test_build_single_file(tmp_path, capsys) -> None:
    md = tmp_path / "page.md"
    md.write_text('---\ntitle: "T"\n---\n\nbody\n', encoding="utf-8")
    rc = main(["build", str(md)])
    assert rc == 0
    assert (tmp_path / "page.html").exists()
    assert "built" in capsys.readouterr().out


def test_build_directory(tmp_path, capsys) -> None:
    (tmp_path / "a.md").write_text('---\ntitle: "A"\n---\nx\n', encoding="utf-8")
    (tmp_path / "b.md").write_text('---\ntitle: "B"\n---\ny\n', encoding="utf-8")
    rc = main(["build", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("built") == 2


def test_build_directory_with_no_pages_returns_1(tmp_path, capsys) -> None:
    rc = main(["build", str(tmp_path)])
    assert rc == 1
    assert "no project pages found" in capsys.readouterr().err


def test_build_defaults_to_cwd(tmp_path, monkeypatch, capsys) -> None:
    (tmp_path / "a.md").write_text('---\ntitle: "A"\n---\nx\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = main(["build"])
    assert rc == 0
    assert "built" in capsys.readouterr().out


def test_missing_command_errors() -> None:
    # argparse exits with code 2 when the required subcommand is missing.
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_version_flag(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
