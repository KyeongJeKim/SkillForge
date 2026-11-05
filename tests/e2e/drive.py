"""Drive one multi-turn headless Claude Code scenario and log what happened.

Usage: python3 drive.py <scenario.json> <workdir> <log.json> [plugin_dir]

scenario.json keys:
  turns        fixed prompts sent in one resumed session (the conversation with SkillForge)
  persona      instead of fixed turns: {"first": ..., "who": ..., "style": ..., "truth": [...],
               "events": {"3": "change your mind about ..."}, "max_turns": 16}. A cheap model plays
               this person and answers SkillForge until it hands over the result (see sim.py).
  fresh_turns  prompts each sent in a brand-new session in the same folder (uses what was built)
SF_MODEL picks the model under test (default: the CLI default).
The plugin under test is loaded with --plugin-dir from a throwaway copy, and `git push` is
blocked, so a scenario can never change the real SkillForge repository.
"""
from __future__ import annotations

import json
import subprocess
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim  # noqa: E402

ALLOWED = "Bash Read Write Edit Glob Grep Skill"
# Tests must not push or write into the real ~/.claude (other sessions would load what lands there).
BLOCKED = ["Bash(git push:*)", "Edit(~/.claude/**)", "Write(~/.claude/**)"]


def run_turn(prompt: str, cwd: str, plugin_dir: str | None, session: str | None = None, timeout: int = 1200) -> dict:
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "acceptEdits", "--allowedTools", ALLOWED, "--disallowedTools", *BLOCKED]
    if plugin_dir:
        cmd += ["--plugin-dir", plugin_dir]
    if os.environ.get("SF_MODEL"):
        cmd += ["--model", os.environ["SF_MODEL"]]
    if session:
        cmd += ["--resume", session]
    t0 = time.time()
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout).stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    rec = {"prompt": prompt, "skills": [], "tools": [], "text": [], "session": session, "secs": 0}
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("session_id"):
            rec["session"] = ev["session_id"]
        if ev.get("type") == "assistant":
            for c in ev["message"].get("content", []):
                if c.get("type") == "tool_use":
                    inp = c.get("input") or {}
                    if c["name"] == "Skill":
                        rec["skills"].append(inp.get("skill"))
                    rec["tools"].append(c["name"] + " " + json.dumps(inp, ensure_ascii=False)[:300])
                elif c.get("type") == "text":
                    rec["text"].append(c["text"])
        if ev.get("type") == "result":
            rec["result"] = {"subtype": ev.get("subtype"), "is_error": ev.get("is_error"),
                             "cost": ev.get("total_cost_usd")}
    rec["secs"] = round(time.time() - t0)
    return rec


def main() -> None:
    sc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    cwd, outp = sys.argv[2], Path(sys.argv[3])
    plugin_dir = sys.argv[4] if len(sys.argv) > 4 else None
    log = {"name": sc["name"], "turns": [], "fresh": []}
    session = None
    save = lambda: outp.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")  # noqa: E731
    for p in sc.get("turns", []):
        rec = run_turn(p, cwd, plugin_dir, session)
        session = rec["session"]
        log["turns"].append(rec)
        save()
    if sc.get("persona"):
        msg, history, log["persona_cost"] = sc["persona"]["first"], [], 0.0
        for _ in range(sc["persona"].get("max_turns", 16)):
            rec = run_turn(msg, cwd, plugin_dir, session)
            session = rec["session"]
            log["turns"].append(rec)
            history.append({"user": msg, "assistant": "\n".join(rec["text"])})
            save()
            if not rec.get("result") or rec["result"].get("is_error"):
                break
            reply, done, cost = sim.persona_reply(sc, history)
            log["persona_cost"] += cost
            # A cheap persona model sometimes ends while SkillForge is still asking it something;
            # a real person would answer, so keep going when it also wrote a reply.
            asking = "?" in history[-1]["assistant"][-400:]
            if not reply or (done and not asking):
                break
            if done:
                log["persona_done_overruled"] = log.get("persona_done_overruled", 0) + 1
            msg = reply
        else:
            log["max_turns_hit"] = True
        save()
    for p in sc.get("fresh_turns", []):
        log["fresh"].append(run_turn(p, cwd, plugin_dir))
        save()
    skip = {"examples", ".git", ".venv", "venv", "node_modules", "__pycache__"}
    log["files"] = sorted(str(p.relative_to(cwd)) for p in Path(cwd).rglob("*")
                          if p.is_file() and not skip & set(p.relative_to(cwd).parts))
    git = subprocess.run(["git", "log", "--oneline"], cwd=cwd, capture_output=True, text=True)
    log["commits"] = [line for line in git.stdout.splitlines() if line.strip()]
    outp.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
