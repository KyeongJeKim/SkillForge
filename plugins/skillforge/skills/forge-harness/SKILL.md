---
name: forge-harness
description: Designs and generates a Claude harness, the working setup for a multi-step job (subagents with roles, hooks that run automatic checks, and an orchestrating skill with human approval points), shipped as a plugin and validated. Use when a confirmed SkillForge spec has type harness, or someone wants a whole process automated with roles and checks, e.g. "set up a workflow with a reviewer", "automate this process with checks", "하네스 만들어 줘", "여러 단계를 자동으로 돌리고 싶어".
---

# Forge a Harness

A harness is the workflow around the model: who does each step, what is checked
automatically, and where a person approves. Build it from three pieces:

| Piece | File | Purpose |
| --- | --- | --- |
| Orchestrating skill | `skills/<workflow>/SKILL.md` | Triggers from natural language and runs the stages in order |
| Subagents | `agents/<role>.md` | Focused roles (drafter, reviewer, tester) with limited tools |
| Hooks | `hooks/hooks.json` + `scripts/` | Deterministic checks that run on events (e.g. after a file is written) |

## Inputs

A confirmed `forge-spec.md` with `Type: harness`: the stages, each role, the automatic checks,
the approval points and the success criteria.

## Steps

1. **Draw the workflow** as a numbered list of stages. For each stage name the actor
   (main session, a subagent, a hook, or the person) and its output. Show it to the person
   and confirm before generating files.
2. **Subagents:** for each role, copy [templates/agent.template.md](templates/agent.template.md)
   to `agents/<role>.md`. Required frontmatter: `name` (no `:`) and `description` (when to
   delegate). Give each agent only the `tools` it needs; a reviewer usually needs only
   `Read, Grep, Glob`.
3. **Hooks:** copy [templates/hooks.json](templates/hooks.json) to `hooks/hooks.json` and the
   check script [templates/check_required_sections.py](templates/check_required_sections.py)
   to `scripts/`. The file wraps events in a top-level `"hooks"` key; common events are
   `PostToolUse` (matcher such as `Write|Edit`), `PreToolUse`, `UserPromptSubmit`, `Stop` and
   `SessionStart`. Reference scripts with `${CLAUDE_PLUGIN_ROOT}`. Keep hooks fast and
   deterministic, and make them warn rather than block unless the spec says to block.
4. **Orchestrating skill:** write `skills/<workflow>/SKILL.md` (use `forge-skill`) that lists
   the stages, says which subagent to delegate each stage to, and states every approval point
   as "stop and ask the person".
5. **Package as a plugin** with `forge-plugin` so the team installs it in one step.
6. **Validate:**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" plugin <plugin-dir>
   claude plugin validate <plugin-dir>   # if the claude CLI is available
   ```

   Also run each hook script once on a sample input and show the output.

## Hand-over

Tell the person: the stages and who does each, the automatic checks, the approval points,
how to install it, and what was validated.

## Rules

- A person approves anything that sends, publishes, deletes or spends.
- Hooks never print or store secrets.
- Plugin subagents ignore `hooks`, `mcpServers` and `permissionMode` in their frontmatter, so
  put those at the plugin level instead.
