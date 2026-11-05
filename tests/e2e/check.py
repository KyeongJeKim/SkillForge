"""Judge finished SkillForge scenario runs against each scenario's "expect" block.

Usage: python3 check.py <out-dir> [scenario-name ...]   -> PASS/FAIL per scenario, exit 1 on any failure
       python3 check.py --hash <dir>                   -> print a content hash of a folder

Every scenario is also checked for: no git commits nobody asked for, the plugin copy left
untouched, no turn ending in an error, and no odd honorifics.

"expect" keys (all optional):
  skills_all / skills_any   SkillForge skills that must all / at least one run in the main turns
  no_skillforge             no skillforge:* skill may run at all
  skill_dirs                at least N generated .claude/skills/*/SKILL.md, each passing forge_validate
  fresh_uses_generated      each fresh session invokes a generated (non-SkillForge) skill
  fresh_writes_file         each fresh turn writes a file
  files_any                 for each fragment, some produced file path contains it
  validate_plugins          every generated plugin passes forge_validate
  validate_mcp              at least one generated server.py, each passing forge_validate
  text_all                  words that must appear in the main turns' replies
  no_files                  nothing may be written
  max_questions             the last reply asks at most N numbered questions
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATE = HERE.parents[1] / "plugins" / "skillforge" / "scripts" / "forge_validate.py"
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "examples"}


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def validate(kind: str, path: Path) -> tuple[bool, str]:
    out = subprocess.run([sys.executable, str(VALIDATE), kind, str(path)], capture_output=True, text=True)
    lines = [line for line in out.stdout.splitlines() if line.strip()]
    errors = [line for line in lines if "error" in line.lower() and "0 errors" not in line]
    return out.returncode == 0, (errors[0] if errors else (lines[-1] if lines else ""))


def wrote_file(tools: list[str]) -> bool:
    return any(t.startswith(("Write ", "Edit ")) or (t.startswith("Bash ") and (">" in t or "tee " in t))
               for t in tools)


def judge(sc: dict, out: Path) -> list[str]:
    name, ex = sc["name"], sc.get("expect", {})
    log_path, work = out / "runs" / f"{name}.log.json", out / "runs" / name
    if not log_path.exists():
        return ["no log (scenario did not run)"]
    log = json.loads(log_path.read_text(encoding="utf-8"))
    why = []
    if "files" not in log:
        why.append("run did not finish")
    turns, fresh = log.get("turns", []), log.get("fresh", [])
    skills = [s for t in turns for s in t["skills"] if s]
    all_skills = skills + [s for t in fresh for s in t["skills"] if s]
    text = "\n".join(x for t in turns for x in t["text"])
    files = log.get("files", [])
    if log.get("commits"):
        why.append(f"made {len(log['commits'])} git commit(s) nobody asked for")
    if "대표님" in text + "\n".join(x for t in fresh for x in t["text"]):
        why.append("used an odd honorific (대표님)")
    if any((t.get("result") or {}).get("is_error") for t in turns + fresh):
        why.append("a turn ended in an error")
    if any(t.get("result") is None for t in turns + fresh):
        why.append("a turn never finished (timeout?)")
    for s in ex.get("skills_all", []):
        if s not in skills:
            why.append(f"{s} did not run")
    if ex.get("skills_any") and not set(ex["skills_any"]) & set(skills):
        why.append(f"none of {ex['skills_any']} ran")
    if ex.get("no_skillforge") and any(s.startswith("skillforge:") for s in all_skills):
        why.append(f"SkillForge started on a request it should leave alone: {all_skills}")
    if "skill_dirs" in ex:
        dirs = sorted({p.parent for p in work.glob(".claude/skills/*/SKILL.md")})
        if len(dirs) < ex["skill_dirs"]:
            why.append(f"expected {ex['skill_dirs']} generated skill(s), found {len(dirs)}")
        for d in dirs:
            ok, msg = validate("skill", d)
            if not ok:
                why.append(f"generated skill {d.name} fails validation: {msg}")
    if ex.get("fresh_uses_generated"):
        for t in fresh:
            if not [s for s in t["skills"] if s and not s.startswith("skillforge:")]:
                why.append(f"fresh session did not use the generated skill: {t['prompt'][:40]}")
    if ex.get("fresh_writes_file"):
        for t in fresh:
            if not wrote_file(t["tools"]):
                why.append(f"fresh turn wrote no file: {t['prompt'][:40]}")
    for frag in ex.get("files_any", []):
        if not any(frag in f for f in files):
            why.append(f"no produced file matching {frag}")
    if ex.get("validate_plugins"):
        plugs = sorted({p.parent.parent for p in work.rglob(".claude-plugin/plugin.json")
                        if not SKIP & set(p.relative_to(work).parts)})
        if not plugs:
            why.append("no plugin generated")
        for p in plugs:
            ok, msg = validate("plugin", p)
            if not ok:
                why.append(f"plugin {p.name} fails validation: {msg}")
    if ex.get("validate_mcp"):
        servers = sorted({p.parent for p in work.rglob("server.py") if not SKIP & set(p.relative_to(work).parts)})
        if not servers:
            why.append("no MCP server generated")
        for s in servers:
            ok, msg = validate("mcp", s)
            if not ok:
                why.append(f"MCP server {s.relative_to(work)} fails validation: {msg}")
    for w in ex.get("text_all", []):
        if w not in text:
            why.append(f"replies never mention {w}")
    if ex.get("no_files") and files:
        why.append(f"wrote files: {files[:5]}")
    if "max_questions" in ex and turns and turns[-1]["text"]:
        q = len(re.findall(r"^\s*\d+\.\s", turns[-1]["text"][-1], re.M))
        if q > ex["max_questions"]:
            why.append(f"asked {q} numbered questions (max {ex['max_questions']})")
    return why


def main() -> int:
    if sys.argv[1] == "--hash":
        print(tree_hash(Path(sys.argv[2])))
        return 0
    out = Path(sys.argv[1])
    names = sys.argv[2:] or [p.stem for p in sorted((HERE / "scenarios").glob("*.json"))]
    failed = 0
    sha = out / "plugin.sha"
    if sha.exists() and sha.read_text().strip() != tree_hash(out / "plugin"):
        print("FAIL plugin copy: a scenario edited SkillForge's own files")
        failed += 1
    for n in names:
        sc = json.loads((HERE / "scenarios" / f"{n}.json").read_text(encoding="utf-8"))
        why = judge(sc, out)
        log_path = out / "runs" / f"{n}.log.json"
        cost = secs = 0
        if log_path.exists():
            log = json.loads(log_path.read_text(encoding="utf-8"))
            for t in log.get("turns", []) + log.get("fresh", []):
                cost += (t.get("result") or {}).get("cost") or 0
                secs += t.get("secs", 0)
        failed += bool(why)
        print(f"{'FAIL' if why else 'PASS'} {n}  (${cost:.2f}, {secs}s)" + "".join(f"\n     - {w}" for w in why))
    print(f"\n{failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
