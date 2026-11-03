"""repoxray command line: ``repoxray scan <path>``."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .analysis import find_dead_code, hotspots, summarize
from .graph import build_edges, entry_points, find_cycles, layers, orphans
from .report import build_all
from .scanner import scan_project

FORMATS = {"md": "ARCHITECTURE.md", "json": "architecture.json",
           "html": "architecture-map.html"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repoxray",
        description="X-ray any Python codebase: architecture map, import "
                    "cycles, dead code, and complexity hotspots.")
    parser.add_argument("--version", action="version",
                        version=f"repoxray {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="scan a project directory")
    scan.add_argument("path", help="project directory to scan")
    scan.add_argument("--format", choices=["md", "json", "html", "all"],
                      default="md", help="report format (default: md)")
    scan.add_argument("--output", "-o",
                      help="output file (default: stdout, or ARCHITECTURE.* "
                           "with --format all)")
    scan.add_argument("--quiet", "-q", action="store_true",
                      help="print only the report, no summary line")
    return parser


def run_scan(args: argparse.Namespace) -> int:
    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print(f"repoxray: not a directory: {args.path}", file=sys.stderr)
        return 2
    modules, counts = scan_project(root)
    edges = build_edges(modules)
    cycles = find_cycles(edges)
    entries = entry_points(modules, edges)
    orphan_list = orphans(modules, edges)
    dead = find_dead_code(modules)
    spots = hotspots(modules)
    summary = summarize(modules, edges)
    depth = layers(modules, edges)
    reports = build_all(root, modules, counts, edges, cycles, entries,
                        orphan_list, dead, spots, summary, depth)

    if args.format == "all":
        for fmt, filename in FORMATS.items():
            with open(filename, "w", encoding="utf-8") as fh:
                fh.write(reports[fmt])
            if not args.quiet:
                print(f"wrote {filename}")
    else:
        text = reports[args.format]
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(text)
            if not args.quiet:
                print(f"wrote {args.output}")
        else:
            sys.stdout.write(text)

    if not args.quiet:
        print(f"repoxray: {summary.modules} modules, {summary.total_lines} "
              f"lines, {len(cycles)} cycle(s), {len(orphan_list)} orphan(s), "
              f"{len(dead)} possibly-dead function(s), "
              f"{len(spots)} hotspot(s)", file=sys.stderr)
    return 1 if cycles else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        return run_scan(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
