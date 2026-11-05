#!/usr/bin/env bash
# SkillForge eval (kept for old habits): forwards to run.py. See run.py --help.
#   tests/e2e/run.sh                  cheap sweep of every scenario and trigger prompt
#   tests/e2e/run.sh --mode full      the real thing, on the default model
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")" && pwd)/run.py" "$@"
