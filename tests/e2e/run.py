"""Run the SkillForge eval: trigger sweep + scenario runs + checks + rubric scores.

Usage:
  python3 tests/e2e/run.py [--mode sweep|full] [--set dev|heldout|all] [--jobs N]
                           [--out DIR] [--no-triggers] [--sample N] [scenario-name ...]

--sample N runs N dev scenarios picked by today's date (same pick all day, a different one each
day) plus every held-out scenario: the daily routine's cheaper measurement. A full dev sweep costs
about $180, a sample of 8 with the held-out set about $70.

Modes (models can still be overridden with SF_MODEL, SF_PERSONA_MODEL, SF_JUDGE_MODEL):
  sweep  cheap broad pass: SkillForge on sonnet, simulated users on haiku, judge on sonnet
  full   the real thing: SkillForge on the CLI default model, simulated users and judge on sonnet
Scores are only comparable between runs of the same mode.

Safety: every run tests a throwaway copy of the plugin (its hash is checked afterwards), each
scenario runs in its own git-initialised folder, and `git push` is blocked for the model.
Writes <out>/summary.json with pass rates, per-dimension means and the total cost.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim  # noqa: E402,F401  (import strips the host's memory settings from os.environ)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODES = {
    "sweep": {"SF_MODEL": "sonnet", "SF_PERSONA_MODEL": "haiku", "SF_JUDGE_MODEL": "sonnet"},
    "full": {"SF_PERSONA_MODEL": "sonnet", "SF_JUDGE_MODEL": "sonnet"},
}


def scenario_names(which: str) -> list[str]:
    sets = ["scenarios", "heldout"] if which == "all" else ["heldout" if which == "heldout" else "scenarios"]
    return [p.stem for s in sets for p in sorted((HERE / s).glob("*.json")) if p.name != "triggers.json"]


def load(name: str) -> dict:
    for s in ("scenarios", "heldout"):
        p = HERE / s / f"{name}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    raise SystemExit(f"unknown scenario {name}")


def run_one(name: str, out: Path, env: dict) -> None:
    sc = load(name)
    work = out / "runs" / name
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    if sc.get("src"):
        shutil.copytree(HERE / "fixtures" / sc["src"], work / "examples",
                        ignore=shutil.ignore_patterns("__pycache__", "make_*.py"))
    if sc.get("root_src"):
        shutil.copytree(HERE / "fixtures" / sc["root_src"], work, dirs_exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    with open(out / "runs" / f"{name}.stderr", "w", encoding="utf-8") as err:
        subprocess.run([sys.executable, "-I", str(HERE / "drive.py"), str(HERE / ("heldout" if (HERE / "heldout" / f"{name}.json").exists() else "scenarios") / f"{name}.json"),
                        str(work), str(out / "runs" / f"{name}.log.json"), str(out / "plugin")],
                       env=env, stdout=err, stderr=err, check=False)


def move_strays(out: Path, before: set[Path], names: list[str]) -> list[Path]:
    """Move files a test session wrote at the top of the run folder into <out>/leaked/stray."""
    stray = sorted(p for p in out.iterdir() if p not in before)
    for p in stray:
        logs = [(n, out / "runs" / f"{n}.log.json") for n in names]
        who = [n for n, log in logs if log.is_file() and p.name in log.read_text(encoding="utf-8", errors="replace")]
        dest = out / "leaked" / "stray"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest / p.name))
        print(f"STRAY: a test session wrote {p} outside its folder ({', '.join(who) or 'scenario unknown'}); "
              f"moved to {dest / p.name}")
    return stray


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=MODES, default="sweep")
    ap.add_argument("--set", choices=["dev", "heldout", "all"], default="all")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--out")
    ap.add_argument("--no-triggers", action="store_true")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()

    env = {**os.environ}
    for k, v in MODES[a.mode].items():
        env.setdefault(k, v)
    os.environ.update({k: env[k] for k in MODES[a.mode]})
    out = Path(a.out or tempfile.mkdtemp(prefix=f"skillforge-eval-{a.mode}-"))
    (out / "runs").mkdir(parents=True, exist_ok=True)
    shutil.rmtree(out / "plugin", ignore_errors=True)
    shutil.copytree(ROOT / "plugins" / "skillforge", out / "plugin", ignore=shutil.ignore_patterns("__pycache__"))
    sha = subprocess.run([sys.executable, str(HERE / "check.py"), "--hash", str(out / "plugin")],
                         capture_output=True, text=True, check=True).stdout.strip()
    (out / "plugin.sha").write_text(sha + "\n")
    names = a.names or scenario_names(a.set)
    if a.sample and not a.names:
        dev = scenario_names("dev")
        rnd = random.Random(time.strftime("%Y-%m-%d"))
        names = sorted(rnd.sample(dev, min(a.sample, len(dev)))) + scenario_names("heldout")
    print(f"mode={a.mode} models: SkillForge={env.get('SF_MODEL', 'CLI default')}, "
          f"user={env['SF_PERSONA_MODEL']}, judge={env['SF_JUDGE_MODEL']}; {len(names)} scenarios -> {out}")
    t0 = time.time()

    trig = {}
    if not a.no_triggers and not a.names:
        sets = {"dev": HERE / "triggers.json", "heldout": HERE / "heldout" / "triggers.json"}
        for s, src in sets.items():
            if a.set in (s, "all"):
                subprocess.run([sys.executable, str(HERE / "triggers.py"), str(out / "plugin"),
                                str(out / f"triggers-{s}.json"), str(src), str(a.jobs)], env=env, check=False)
                rows = json.loads((out / f"triggers-{s}.json").read_text(encoding="utf-8"))
                trig[s] = {"passed": sum(r["pass"] for r in rows), "total": len(rows),
                           "cost": round(sum(r["cost"] for r in rows), 2)}

    personal = [Path.home() / ".claude" / d for d in ("skills", "agents", "commands")]
    before = {p for d in personal if d.is_dir() for p in d.iterdir()}
    # Write/Edit outside a scenario folder is caught per scenario in check.py, but a Bash command
    # can still write by absolute path (2026-11-05: a POS run wrote <out>/chk.js). Anything new at the
    # top of the run folder is such a stray write.
    out_before = set(out.iterdir())
    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(lambda n: run_one(n, out, env), names))
    # Anything a test session left in the real ~/.claude would load in every later session: move it
    # into the run folder as evidence instead of leaving it there.
    leaked = sorted(p for d in personal if d.is_dir() for p in d.iterdir() if p not in before)
    for p in leaked:
        dest = out / "leaked" / p.parent.name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest / p.name))
        print(f"LEAK: a test session wrote {p}; moved to {dest / p.name}")
    stray = move_strays(out, out_before, names)
    rc = subprocess.run([sys.executable, str(HERE / "check.py"), str(out), *names], env=env).returncode

    results = json.loads((out / "results.json").read_text(encoding="utf-8"))
    total = sum(r["cost"] for r in results["scenarios"].values()) + sum(t["cost"] for t in trig.values())
    summary = {"mode": a.mode, "date": time.strftime("%Y-%m-%d"), "models": {k: env.get(k, "CLI default") for k in
               ("SF_MODEL", "SF_PERSONA_MODEL", "SF_JUDGE_MODEL")}, "triggers": trig,
               "scenarios": results.get("summary", {}), "plugin_untouched": results["plugin_untouched"],
               "leaked_into_home": [str(p) for p in leaked],
               "stray_writes": [str(p.name) for p in stray],
               "cost_usd": round(total, 2), "minutes": round((time.time() - t0) / 60, 1)}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    for s, t in trig.items():
        print(f"triggers [{s}] {t['passed']}/{t['total']}")
    print(f"total cost ${total:.2f}, {summary['minutes']} min. Summary: {out / 'summary.json'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
