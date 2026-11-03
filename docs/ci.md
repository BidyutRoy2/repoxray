# repoxray in CI

Because a scan exits with code `1` when import cycles are found, it works
as a zero-config architecture gate:

```yaml
# .github/workflows/ci.yml (already included in this repo)
- name: Architecture check
  run: |
    pip install .
    repoxray scan src --format md -o ARCHITECTURE.md
```

For a stricter gate, fail on dead code or hotspots too by grepping the
JSON report:

```bash
repoxray scan src --format json -o architecture.json --quiet
python - <<'EOF'
import json, sys
data = json.load(open("architecture.json"))
if data["dead_code"]:
    print(f"{len(data['dead_code'])} possibly-dead functions — review before merging")
    sys.exit(1)
EOF
```

Recommended cadence: run the scan on every pull request, and commit a
fresh `ARCHITECTURE.md` whenever the module map changes so reviewers can
see structural diffs, not just line diffs.
