# Contributing to repoxray

Thanks for helping! repoxray is small on purpose — zero dependencies, one
clear job — so contributions that keep it that way are the most welcome.

## How to contribute

1. Fork the repo and create a branch from `main`.
2. Add or update tests in `tests/` for any behaviour change.
3. Run the test suite: `PYTHONPATH=src python3 -m unittest discover -s tests`
4. Open a pull request describing what changed and why.

## Ground rules

- **No new third-party dependencies.** The zero-dependency promise is a
  feature: it is why repoxray runs anywhere and never phones home.
- **Python 3.10+**, standard library only, 88-column style (ruff config in
  `pyproject.toml`).
- **No auto-deletion.** repoxray reports candidates; it must never delete
  or rewrite a user's code.
- **Honest reports.** If the analysis cannot know something (dynamic
  imports, `getattr` calls), say so in the report instead of guessing.

## Reporting bugs

Open an issue with: the repoxray version, the Python version, a minimal
project layout that reproduces the problem, and the expected vs. actual
output. A failing test case is the best bug report of all.
