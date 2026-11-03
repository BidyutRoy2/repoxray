# Usage guide

## Install

```bash
pip install repoxray
```

Requires Python 3.10+. There are no third-party dependencies, so the
install is instant and the tool works fully offline.

## Scan a project

```bash
# Markdown report to stdout
repoxray scan ./my-project

# All three formats, written next to your shell's working directory
repoxray scan ./my-project --format all

# JSON only, into a file (great for piping into other tools)
repoxray scan ./my-project --format json -o architecture.json
```

## Reading the report

1. **Start with entry points.** Open those files first; they tell you what
   the project *does*.
2. **Check cycles before refactoring.** A cycle means two modules cannot be
   understood or tested independently. Break it by moving the shared code
   into a third, lower-level module.
3. **Treat dead code as candidates, not verdicts.** If a function is reached
   through `getattr`, a plugin registry, or a framework hook, repoxray
   cannot see the call. Verify, then delete.
4. **Test the hotspots first.** A function with complexity 8 has at least 8
   paths through it; that is where bugs hide and where a test pays most.

## What is skipped

`.git`, `__pycache__`, virtualenvs (`.venv`, `venv`, `env`), `node_modules`,
`dist`, `build`, and `setup.py` packaging shims. Everything else ending in
`.py` is parsed; other files are counted in the summary but not analysed.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Clean scan |
| 1 | Import cycles found (the report is still complete) |
| 2 | The path is not a directory |
