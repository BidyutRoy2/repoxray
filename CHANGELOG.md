# Changelog

All notable changes to repoxray will be documented here. The format is
based on Keep a Changelog, and the project adheres to Semantic Versioning.

## [0.1.0] — 2026-11-03

### Added

- `repoxray scan` CLI with `--format md | json | html | all`, `--output`,
  and `--quiet` flags.
- Architecture map: entry points, module table, import edges.
- Import cycle detection, with red edges in the HTML map.
- Orphan module detection (excluding empty `__init__.py` files).
- Dead-code detection for top-level functions, with documented
  false-positive caveats for dynamic dispatch.
- Complexity hotspots (branch count ≥ 5).
- Three report formats: `ARCHITECTURE.md`, `architecture.json`,
  dark-mode-aware `architecture-map.html`.
- Exit codes: 0 clean, 1 cycles found, 2 bad path.
- Zero third-party dependencies; Python 3.10+.
- Full test suite (15 tests) covering scanner, graph, analysis, reports,
  and the CLI, plus a demo project under `examples/`.
