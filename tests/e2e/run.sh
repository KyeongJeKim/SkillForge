#!/usr/bin/env bash
# SkillForge end-to-end scenarios: real Claude Code sessions, judged by check.py.
# Needs the claude CLI signed in. Each full run costs Claude usage (about US$20 at the
# time of writing) and takes 10-15 minutes, because all scenarios run in parallel.
#
# Usage: tests/e2e/run.sh [scenario-name ...]      (default: every scenario)
#        SF_E2E_OUT=/some/dir tests/e2e/run.sh       (keep results somewhere specific)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="${SF_E2E_OUT:-$(mktemp -d -t skillforge-e2e-XXXX)}"
mkdir -p "$OUT/runs"

# Test a throwaway copy of the plugin so no scenario can edit the real one.
rm -rf "$OUT/plugin" && cp -r "$ROOT/plugins/skillforge" "$OUT/plugin"
find "$OUT/plugin" -name __pycache__ -prune -exec rm -rf {} +
python3 "$HERE/check.py" --hash "$OUT/plugin" > "$OUT/plugin.sha"

names=("$@")
if [ ${#names[@]} -eq 0 ]; then
  for f in "$HERE"/scenarios/*.json; do names+=("$(basename "$f" .json)"); done
fi

for n in "${names[@]}"; do
  sc="$HERE/scenarios/$n.json"
  src=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('src') or '')" "$sc")
  d="$OUT/runs/$n"; rm -rf "$d"; mkdir -p "$d"
  [ -n "$src" ] && cp -r "$HERE/fixtures/$src" "$d/examples"
  (cd "$d" && git init -q)
  python3 -I "$HERE/drive.py" "$sc" "$d" "$OUT/runs/$n.log.json" "$OUT/plugin" > "$OUT/runs/$n.stderr" 2>&1 &
done
wait
echo "Results in $OUT"
python3 "$HERE/check.py" "$OUT" "${names[@]}"
