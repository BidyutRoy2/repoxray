<div align="center">

# 🗺️ repoxray

**X-ray any Python codebase in seconds: architecture map, import cycles, dead code, and complexity hotspots — zero dependencies.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen)](tests/test_repoxray.py)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](pyproject.toml)

[Quickstart](#quickstart) · [What it finds](#what-it-finds) · [Example output](#example-output) · [FAQ](#faq)

</div>

---

## Why repoxray?

You inherit a repo — or you hand one to an AI agent — and the first question is always the same: **where do I even start?** Reading files one by one takes hours. Generic linters tell you about style, not structure.

repoxray answers the structural questions in one command:

| Question | repoxray's answer |
|---|---|
| Where do I start reading? | Entry points — modules nothing else imports |
| What depends on what? | A module map with import edges, plus an HTML graph |
| What will break if I refactor? | Import cycles, drawn in red |
| What can I delete? | Functions never called anywhere in the project |
| What is risky to touch? | Complexity hotspots (branch count ≥ 5) |

**Zero dependencies. No network. No account. Your code never leaves your machine.**

## Quickstart

```bash
pip install repoxray
repoxray scan ./my-project
```

That prints `ARCHITECTURE.md` to stdout. For all three formats at once:

```bash
repoxray scan ./my-project --format all
# writes ARCHITECTURE.md, architecture.json, architecture-map.html
```

Or without installing, straight from source:

```bash
git clone https://github.com/BidyutRoy2/repoxray
cd repoxray
PYTHONPATH=src python3 -m repoxray scan /path/to/project --format all
```

### Options

| Flag | What it does |
|---|---|
| `--format md \| json \| html \| all` | Report format (default: `md`) |
| `--output, -o FILE` | Write to a file instead of stdout |
| `--quiet, -q` | Suppress the summary line on stderr |
| `--version` | Print the version |

Exit codes: `0` = clean scan, `1` = import cycles found (report still written), `2` = bad path.

## What it finds

### 1. Entry points — "start here"

Modules nothing else imports, plus any module with an `if __name__ == "__main__"` guard. These are the front doors of the codebase: CLIs, scripts, app factories.

### 2. Module map

Every module, its line count, what it imports, and what imports it — as a Markdown table, JSON, and a dark-mode-aware HTML graph where entry points sit on the left and shared foundations on the right.

### 3. Import cycles ⚠️

Cycles make modules untestable in isolation. repoxray lists each cycle once (`a → b → a`) and draws those edges in red in the HTML map. Fix by extracting the shared piece into a lower-level module.

### 4. Possibly dead code

Top-level functions never called anywhere in the project. Dunder methods, `main`, test functions, and common framework hooks are never flagged. **Caveat, stated in every report:** dynamically-dispatched calls (`getattr`, plugin registries) can cause false positives — verify before deleting.

### 5. Complexity hotspots

Functions with branch complexity ≥ 5 (one per `if`/`for`/`while`/`except`/`with`, plus boolean operators). These are the functions most likely to hide bugs and most worth a test.

## Example output

Scanning the bundled demo project (`examples/demo-project/`):

```
repoxray: 5 modules, 55 lines, 0 cycle(s), 1 orphan(s),
2 possibly-dead function(s), 1 hotspot(s)
```

```markdown
## Start here (entry points)
- `main` — `main.py` (15 lines)

## Orphan modules
- `orphan` — nothing imports it, it imports nothing internal

## Possibly dead code
- `core.engine.unused_engine_helper` (line 29)

## Complexity hotspots (complexity ≥ 5)
- `core.engine.check_result` — complexity 8
```

Full sample reports live in [`examples/ARCHITECTURE.md`](examples/ARCHITECTURE.md), [`examples/architecture.json`](examples/architecture.json), and the interactive map in [`preview/index.html`](preview/index.html) — open it in a browser, it respects your dark mode.

## repoxray vs. alternatives

| Tool | What it tells you | repoxray's difference |
|---|---|---|
| `pyflakes` / `ruff` | Unused imports, style | Per-file lint, no architecture view |
| `pydeps` | Import graph image | Needs Graphviz, no dead code / hotspots / reports |
| `vulture` | Dead code | Dead code only, no map or cycles |
| Manual reading | Everything, slowly | repoxray does the first pass in seconds |
| **repoxray** | **Map + cycles + dead code + hotspots** | **One command, three report formats, zero deps** |

## How it works

1. **Scan** — walks the tree (skipping `.git`, virtualenvs, `__pycache__`, `node_modules`), parses each `.py` file with `ast`.
2. **Resolve** — relative imports (`from .utils import x`) and absolute imports are resolved against the scanned modules; stdlib/third-party imports are recorded separately, never drawn as internal edges.
3. **Analyse** — graph algorithms find cycles, entry points, orphans, and layers; call collection finds dead code; branch counting finds hotspots.
4. **Report** — Markdown for humans, JSON for agents and CI, HTML for the visual map.

Limitations, stated honestly: Python only (other files are counted, not analysed); dynamic imports (`importlib`, `getattr` calls) are invisible to static analysis; a file with a syntax error is reported, not crashed on.

## FAQ

**Does repoxray send my code anywhere?**
No. It runs locally, has zero dependencies, and makes no network calls.

**Can I use it in CI?**
Yes — exit code `1` when cycles are found makes it a natural gate. See [docs/ci.md](docs/ci.md).

**Why Python only?**
Static analysis quality beats language breadth. A shallow multi-language scan would produce a prettier but less trustworthy map. JS/TS support is on the roadmap if there is demand — see [docs/roadmap.md](docs/roadmap.md).

**Is the dead-code report safe to auto-delete from?**
No — and repoxray never deletes anything. Treat the list as candidates, verify dynamic dispatch first, then delete by hand.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and feature ideas welcome via [Issues](https://github.com/BidyutRoy2/repoxray/issues).

## License

MIT — see [LICENSE](LICENSE).
