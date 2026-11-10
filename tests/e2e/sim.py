"""Model helpers for the SkillForge eval: a simulated user (persona) and an LLM judge.

Both call the claude CLI with no tools, no session persistence and a JSON schema, so each
call is cheap, stateless and cannot touch files. Models come from environment variables:
  SF_PERSONA_MODEL  model playing the user           (default: haiku)
  SF_JUDGE_MODEL    model scoring results with rubric (default: sonnet)
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUBRIC = HERE / "rubric.md"
DIMENSIONS = ["interview", "truth_capture", "format_fidelity", "usability", "output_quality", "robustness"]


def isolate_from_host_memory(environ: dict) -> list[str]:
    """Remove the host session's memory settings from environ (in place); return what was removed.

    A test session that inherits them reads the host's shared team memory (2026-11-06: an
    inventory scenario asked "is this the MD team's inventory-stock plugin from the team record?")
    and its post-turn memory pass writes the simulated user's made-up project back into that
    memory, where later test runs and real sessions read it as fact. Every claude call the eval
    makes must start without them.
    """
    removed = sorted(k for k in environ if "MEMORY" in k.upper() and k != "CLAUDE_CODE_DISABLE_AUTO_MEMORY")
    for k in removed:
        del environ[k]
    environ["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    return removed


isolate_from_host_memory(os.environ)  # every script that runs a test session imports this module


def _claude_json(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".claude.json"


def user_mcp_servers(home: Path | None = None) -> set[str]:
    """Names of MCP servers registered for every session of this user (`claude mcp add -s user`)."""
    try:
        return set((json.loads(_claude_json(home).read_text(encoding="utf-8")).get("mcpServers") or {}))
    except (OSError, ValueError):
        return set()


def remove_user_mcp_servers(keep: set[str], home: Path | None = None) -> list[str]:
    """Unregister user-scope MCP servers that are not in `keep`; return the names removed.

    forge-mcp registers servers with `claude mcp add -s user`, which is right for a real user but in
    the eval it lands in the host's ~/.claude.json and loads in every later test session (2026-11-10:
    a POS MCP from one held-out run made the next run answer "it already exists" and skip the
    interview). The eval calls this after each scenario and at the end of a run.
    """
    path = _claude_json(home)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    servers = data.get("mcpServers") or {}
    extra = sorted(k for k in servers if k not in keep)
    if extra:
        data["mcpServers"] = {k: v for k, v in servers.items() if k in keep}
        tmp = path.with_name(path.name + ".sf-tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.chmod(tmp, path.stat().st_mode & 0o777)  # the file holds account settings: keep it private
        os.replace(tmp, path)
    return extra


def claude_json(prompt: str, system: str, schema: dict, model: str, timeout: int = 600) -> tuple[dict | None, float]:
    """One stateless model call returning (structured output or None, cost in USD)."""
    # The prompt goes in on stdin: a judge prompt can pass the 128 KB limit on one argument.
    cmd = ["claude", "-p", "--model", model, "--tools", "", "--no-session-persistence",
           "--system-prompt", system, "--output-format", "json", "--json-schema", json.dumps(schema)]
    with tempfile.TemporaryDirectory() as empty:  # no project files, no CLAUDE.md
        try:
            out = subprocess.run(cmd, cwd=empty, input=prompt, capture_output=True, text=True,
                                 timeout=timeout).stdout
        except subprocess.TimeoutExpired:
            return None, 0.0
    try:
        data = json.loads(out)
    except ValueError:
        return None, 0.0
    return data.get("structured_output"), float(data.get("total_cost_usd") or 0)


# ------------------------------------------------------------------ simulated user

PERSONA_SYSTEM = """You role-play one real person talking to SkillForge, a Claude Code plugin that interviews
people and then builds Claude skills and tools for them. You are testing whether its interview gets
to the truth, so behave exactly like this person, not like a helpful tester.

Who you are: {persona}

How you behave: {style}

Facts that are true for you (your hidden truth). Reveal a fact only when SkillForge asks about that
topic, or when the person you play would naturally mention it. Never list them all at once. If
SkillForge proposes or plays back something that contradicts a fact, correct it.
{truth}

Rules:
- Write in Korean, the way this person types in a chat: usually one to three short sentences.
- Don't write code, commands or file paths unless this person would.
- Example files: {examples}
- If SkillForge asks for a file or folder you don't have, say you don't have it; never invent paths.
- If SkillForge plays back a summary that matches your facts and asks to build, say yes.
- If SkillForge asks you to approve a commit or push, say no.
- Never say you are simulated, an AI or a tester.
- done = true only when SkillForge has finished and handed over the result and is not asking you
  anything, or clearly cannot continue. Otherwise done = false and reply with your next message.
- You cannot leave this chat to check or fetch something. If SkillForge has said it will wait for
  something you would bring later and asks you nothing else, the person would leave and come back
  another day: done = true. Don't keep saying you'll send it later.
"""

PERSONA_SCHEMA = {"type": "object", "properties": {"reply": {"type": "string"}, "done": {"type": "boolean"}},
                  "required": ["reply", "done"]}


def persona_reply(sc: dict, history: list[dict], model: str | None = None) -> tuple[str | None, bool, float]:
    """Next user message for a persona scenario, given [{"user": ..., "assistant": ...}, ...]."""
    p = sc["persona"]
    examples = ("they are in the examples folder of the work folder; say so if asked." if sc.get("src")
                else "you have none to give. Your folder holds only what is already there.")
    system = PERSONA_SYSTEM.format(persona=p["who"], style=p.get("style", "Answer plainly."), examples=examples,
                                   truth="\n".join(f"- {t}" for t in p.get("truth", [])) or "- (none)")
    convo = []
    for i, h in enumerate(history, 1):
        convo.append(f"[You, message {i}]\n{h['user']}\n\n[SkillForge]\n{h['assistant'][-6000:] or '(no text)'}")
    k = len(history) + 1
    events = p.get("events", {})
    extra = f"\n\nFor this message (number {k}), also do this: {events[str(k)]}" if str(k) in events else ""
    prompt = ("The conversation so far:\n\n" + "\n\n".join(convo)
              + f"\n\nWrite your message number {k} as this person.{extra}")
    out, cost = claude_json(prompt, system, PERSONA_SCHEMA, model or os.environ.get("SF_PERSONA_MODEL", "haiku"))
    if not out:
        return None, True, cost
    return out.get("reply", "").strip(), bool(out.get("done")), cost


# ------------------------------------------------------------------ judge

JUDGE_SYSTEM = """You are a strict reviewer scoring one SkillForge test run against a rubric. SkillForge is a
Claude Code plugin that interviews non-developer teammates and builds Claude skills and tools for
them. Score what the run actually produced, not what it promised. Be specific in weaknesses: name
the file and the problem. Use null for a dimension that does not apply to this scenario.
If the scenario expected something to be built and nothing usable was built, score format_fidelity,
usability and output_quality 0 (not null). Weaknesses go in order of importance, most important first.

{rubric}
"""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {"type": "object", "properties": {d: {"type": ["integer", "null"], "minimum": 0, "maximum": 5}
                                                   for d in DIMENSIONS},
                   "required": DIMENSIONS},
        "truth": {"type": "array", "items": {"type": "object", "properties": {
            "fact": {"type": "string"}, "captured": {"type": "boolean"}}, "required": ["fact", "captured"]}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["scores", "truth", "weaknesses", "summary"],
}

TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".html", ".csv", ".yaml", ".yml", ".sh"}
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__"}


def _files_section(work: Path, budget: int) -> str:
    parts, used = [], 0
    files = sorted(p for p in work.rglob("*") if p.is_file() and not SKIP & set(p.relative_to(work).parts)
                   and "examples" not in p.relative_to(work).parts[:1])
    # SKILL.md and style guides first: they are the artifact; trial outputs after.
    files.sort(key=lambda p: (p.name != "SKILL.md", "style-guide" not in p.name and "design-format" not in p.name,
                              str(p)))
    for p in files:
        rel = p.relative_to(work)
        if p.suffix.lower() not in TEXT_SUFFIXES:
            parts.append(f"=== {rel} (binary, {p.stat().st_size} bytes)")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        room = max(0, min(12000, budget - used))
        if room == 0:
            parts.append(f"=== {rel} (not shown, budget reached)")
            continue
        parts.append(f"=== {rel}\n{text[:room]}" + ("\n[...truncated]" if len(text) > room else ""))
        used += min(len(text), room)
    return "\n\n".join(parts) or "(no files produced)"


def _examples_section(work: Path, budget: int = 15000) -> str:
    ex = work / "examples"
    if not ex.exists():
        return "(no examples given)"
    names = sorted(str(p.relative_to(ex)) for p in ex.rglob("*") if p.is_file())
    shown, used = [], 0
    for p in sorted(ex.rglob("*.md"))[:4]:
        t = p.read_text(encoding="utf-8", errors="replace")[:4000]
        if used + len(t) > budget:
            break
        shown.append(f"--- examples/{p.relative_to(ex)}\n{t}")
        used += len(t)
    return "Files: " + ", ".join(names) + ("\n\n" + "\n\n".join(shown) if shown else "")


def judge_run(sc: dict, log: dict, work: Path, model: str | None = None) -> tuple[dict | None, float]:
    turns = []
    for t in log.get("turns", []):
        turns.append(f"[User]\n{t['prompt']}\n\n[SkillForge] (skills used: {', '.join(s for s in t['skills'] if s) or 'none'})\n"
                     + "\n".join(t["text"])[-5000:])
    fresh = []
    for t in log.get("fresh", []):
        fresh.append(f"[User, new session]\n{t['prompt']}\n\n[Claude] (skills used: {', '.join(s for s in t['skills'] if s) or 'none'})\n"
                     + "\n".join(t["text"])[-3000:])
    truth = (sc.get("persona") or {}).get("truth") or sc.get("truth") or []
    prompt = (
        f"Scenario: {sc['name']}\nWhat this scenario tests: {sc.get('about', '')}\n"
        f"Machine-checked expectations (skills that should run, things that should be built): "
        f"{json.dumps(sc.get('expect', {}), ensure_ascii=False)}\n"
        f"Persona: {(sc.get('persona') or {}).get('who', '(fixed script)')}\n"
        f"Persona behaviour: {(sc.get('persona') or {}).get('style', '')}\n\n"
        "Hidden truth the interview should have uncovered (judge each as captured or not in the final "
        "artifact or spec):\n" + ("\n".join(f"- {t}" for t in truth) or "- (none)") + "\n\n"
        "Extra checks for this scenario:\n" + ("\n".join(f"- {c}" for c in sc.get("judge_notes", [])) or "- (none)")
        + "\n\n## Team examples given to SkillForge\n" + _examples_section(work)
        + "\n\n## Conversation\n" + "\n\n".join(turns)
        + "\n\n## Later use of the result (fresh sessions)\n" + ("\n\n".join(fresh) or "(none)")
        + "\n\n## Files in the work folder after the run\n" + _files_section(work, 90000)
    )
    system = JUDGE_SYSTEM.format(rubric=RUBRIC.read_text(encoding="utf-8"))
    return claude_json(prompt, system, JUDGE_SCHEMA, model or os.environ.get("SF_JUDGE_MODEL", "sonnet"), timeout=900)
