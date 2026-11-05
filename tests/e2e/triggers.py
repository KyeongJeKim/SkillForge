"""Trigger sweep: does SkillForge start on the requests it should, and stay out of the rest?

Usage: python3 triggers.py <plugin_dir> <out.json> <triggers.json> [jobs]

Each prompt runs once, single-turn (--max-turns 3), in an empty folder. A prompt passes when the
first SkillForge skill it starts is in its "expect" list, or it starts none and "none" is listed.
SF_MODEL picks the model under test.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def one(item: dict, plugin_dir: str) -> dict:
    cmd = ["claude", "-p", item["prompt"], "--output-format", "stream-json", "--verbose", "--max-turns", "3",
           "--permission-mode", "default", "--allowedTools", "Read Glob Grep Skill",
           "--disallowedTools", "Bash Write Edit", "--plugin-dir", plugin_dir, "--no-session-persistence"]
    if os.environ.get("SF_MODEL"):
        cmd += ["--model", os.environ["SF_MODEL"]]
    skills, cost = [], 0.0
    with tempfile.TemporaryDirectory() as cwd:
        try:
            out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300).stdout
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for c in ev["message"].get("content", []):
                if c.get("type") == "tool_use" and c["name"] == "Skill":
                    skills.append((c.get("input") or {}).get("skill"))
        if ev.get("type") == "result":
            cost = float(ev.get("total_cost_usd") or 0)
    forge = [s for s in skills if s and s.startswith("skillforge:")]
    first = forge[0] if forge else "none"
    return {"prompt": item["prompt"], "expect": item["expect"], "got": first, "skills": skills,
            "pass": first in item["expect"], "cost": cost}


def main() -> int:
    plugin_dir, out, src = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    jobs = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    items = json.loads(src.read_text(encoding="utf-8"))
    with ThreadPoolExecutor(jobs) as ex:
        results = list(ex.map(lambda it: one(it, plugin_dir), items))
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(r["pass"] for r in results)
    for r in results:
        if not r["pass"]:
            print(f"  MISS {r['prompt'][:50]}  expected {r['expect']}, got {r['got']}")
    print(f"triggers {src.parent.name}/{src.name}: {n}/{len(results)} "
          f"(${sum(r['cost'] for r in results):.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
