"""Command-line entry point for projecter.

Usage::

    projecter build [PATH]      # build all pages found under PATH (default: .)
    projecter build file.md     # build a single markdown file
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from projecter import __version__
from projecter.builder import build_all, build_file


def _build(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if target.is_file():
        out = build_file(target)
        print(f"built {out}")
        return 0

    outputs = build_all(target)
    if not outputs:
        print(f"no project pages found under {target}", file=sys.stderr)
        return 1
    for out in outputs:
        print(f"built {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the projecter CLI."""
    parser = argparse.ArgumentParser(prog="projecter", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="render markdown project pages to HTML")
    build.add_argument(
        "path",
        nargs="?",
        default=".",
        help="markdown file or directory to search (default: current directory)",
    )
    build.set_defaults(func=_build)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
