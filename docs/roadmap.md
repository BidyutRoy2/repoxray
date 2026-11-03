# Roadmap

Honest status: v0.1.0 does one thing well — Python architecture maps.
Everything below is planned, not promised, and issues drive the order.

## Next

- **JavaScript/TypeScript import scanning** — regex-based at first, so mixed
  repos get a map even if the analysis stays shallower than Python's.
- **`--exclude` flag** — user-supplied skip patterns on top of the defaults.
- **Call-graph edges in the HTML map** — function-level, not just module-level.

## Later

- **Trend view** — diff two scans and report which modules grew, which
  cycles appeared, which dead code was removed.
- **SARIF output** — so findings show up natively in GitHub code scanning.
- **Pre-commit hook** — `repoxray scan` as a local gate before push.

## Not planned

- Auto-deleting dead code. The report is a candidate list; deletion is a
  human decision, because dynamic dispatch makes static certainty
  impossible.
- Sending code to any server. repoxray stays local and dependency-free.
