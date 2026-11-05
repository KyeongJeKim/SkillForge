---
name: forge-harness
description: "Designs and generates a Claude harness: an orchestrating skill that runs a multi-step workflow, subagents with focused roles, and hooks that run automatic checks, with human approval points, shipped as a plugin and validated. Use after forge-intake has a confirmed spec of type harness, or when the person wants a whole process run in stages with roles and checks, e.g. 초안 쓰고 검토까지 자동으로 해 줘, 작성자랑 검토자 나눠서 돌리고 싶어, set up a workflow with a reviewer. If the need is still vague, start forge-intake instead."
---

# Forge a Harness

A harness is the workflow around the model: who does each step, what is checked automatically,
and where a person approves. Build it from three pieces, shipped as one plugin:

| Piece | File | Purpose |
| --- | --- | --- |
| Orchestrating skill | `skills/<workflow>/SKILL.md` | Starts from natural language and runs the stages in order |
| Subagents | `agents/<role>.md` | Focused roles (drafter, reviewer, tester) with limited tools |
| Hooks | `hooks/hooks.json` + `scripts/` | Deterministic checks on events (e.g. after a file is written) |

## Inputs

A confirmed `forge-spec.md` with type harness: stages, roles, automatic checks, approval points,
success criteria. This one spec covers the skill and the plugin you create below; don't ask the
person to confirm separate specs for them.

**Before you build:** if this conversation has no confirmed `forge-spec.md` (the person said yes to a
played-back summary), start `skillforge:forge-intake` first, even when the request looks complete.
It can be short when the examples answer most questions, but it still confirms what they settle,
asks about the hard parts and plays back the summary before anything is built.

## Steps

1. **Draw the workflow** as a numbered list of stages; for each, the actor (main session, a
   subagent, a hook, or the person) and its output. Show it in five lines or fewer and confirm.
2. **Plugin skeleton** as in `skillforge:forge-plugin` (layout, `plugin.json`, `marketplace.json`).
3. **Subagents:** for each role copy [templates/agent.template.md](templates/agent.template.md) to
   `agents/<role>.md` and fill every `{{SF: ...}}` blank. Required frontmatter: `name` (no `:`) and
   `description`. Give each agent only the `tools` it needs; a reviewer needs `Read, Grep, Glob`.
   Once installed, a plugin agent is addressed as `<plugin-name>:<role>`.
4. **Hooks:** copy [templates/hooks.template.json](templates/hooks.template.json) to `hooks/hooks.json`
   **and** [templates/check_required_sections.py](templates/check_required_sections.py) to
   `scripts/check_required_sections.py` (the validator fails if a referenced script is missing).
   Set `TARGET_GLOBS` and `REQUIRED_SECTIONS` from the team's style guide, in the team's language
   (e.g. `["*명세*.md"]`, `["개요", "기능 상세", "예외 처리"]`). Hooks warn (exit code 2 shows the
   message to Claude) rather than block, unless the spec says to block.
5. **Orchestrating skill** (follow `skillforge:forge-skill` steps 2 to 9): list the stages, say which
   subagent handles each stage, and write every approval point as "stop and ask the person".
   Give the reviewer subagent the spec's 품질 기준 and 금지·승인 as its checklist, and the
   writer the 예외 처리 cases, so the checks are the team's real ones, not generic advice.
6. **Validate** and fix until clean:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" marketplace <repo>
   claude plugin validate <repo>/plugins/<plugin-name>   # if the claude CLI is available
   ```

7. **Run each hook script once** on a passing and a failing sample file and show the result:

   ```bash
   echo '{"tool_input":{"file_path":"<sample.md>"}}' | python3 scripts/check_required_sections.py; echo "exit $?"
   ```

8. **Test locally** as in `skillforge:forge-plugin` step 8.

## Hand-over (in the person's language, short)

The stages and who does each, the automatic checks, the approval points, that validation and the
local install passed, and what's left for them.

## Rules

- A person approves anything that sends, publishes, deletes or spends.
- Hooks never print or store secrets.
- Plugin subagents ignore `hooks`, `mcpServers` and `permissionMode` in their frontmatter.
- Don't delete files unless the person asks. Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.
