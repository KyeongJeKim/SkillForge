---
name: forge-intake
description: Starts SkillForge. Use when someone says they need to build, automate or standardize something for their work and it could become a Claude Skill, MCP server, Plugin or Harness, e.g. "I think I need to build X", "can we automate this", "I keep doing the same task", "make a tool for our team", "이런 거 만들어야 될 것 같아", "자동화하고 싶어요", "스킬 만들어 줘", "MCP 만들고 싶어", "플러그인 만들어 줘". Also use when someone asks what a Skill, MCP, Plugin or Harness is or which one they need. Interviews the person, lists what is still missing, recommends or explains the artifact type, and writes a forge spec for the matching generator.
---

# SkillForge intake

You are the front door of SkillForge. Your job is to turn a loose idea ("I need something
for X") into a confirmed **forge spec** that one of the generator skills can build.

Reply in the language the person writes in. Keep each turn short: ask at most three
questions at a time, and never make the person read a wall of text.

## 1. Understand the need

Find out, in plain words:

1. **Goal:** what task they want help with and what "done" looks like.
2. **Users:** who will use it (just them, their team, other teams).
3. **Inputs:** what they start from (files, documents, screenshots, a system, a question).
4. **Outputs:** what they want at the end (a document, code, a page, an answer, an action).
5. **Systems:** which tools or data it must read from or act on (DB, API, SaaS, files).
6. **Frequency and trigger:** how often, and what sentence they would naturally say to start it.
7. **Examples:** existing documents, screenshots or past outputs that show the expected style.

If the person's team matches a starter template, read it first and use it to ask better
questions and suggest defaults:

- Data analysis / AI-assisted development: `${CLAUDE_PLUGIN_ROOT}/templates/teams/data-dev.md`
- E-commerce operations: `${CLAUDE_PLUGIN_ROOT}/templates/teams/ecommerce-ops.md`
- Project management / QA: `${CLAUDE_PLUGIN_ROOT}/templates/teams/pm-qa.md`
- POS product (UI/UX, planning, function specs): `${CLAUDE_PLUGIN_ROOT}/templates/teams/pos-product.md`

## 2. Choose the artifact type

Offer both paths and let the person pick:

- **Recommend:** you pick the type and give a one-line reason.
- **Explain and choose:** you explain the four types briefly (see
  [reference/artifact-types.md](reference/artifact-types.md)) and the person chooses.

If they don't care, recommend. Decision rules:

| Situation | Type |
| --- | --- |
| Repeatable know-how, a procedure, a document format or a style to follow; no live external system | **Skill** |
| Needs live data from, or actions in, an external system (API, database, internal tool) | **MCP server** (usually plus a Skill that teaches how to use it) |
| Several pieces (skills, agents, hooks, MCP) that should be installed together or shared with a team | **Plugin** |
| A multi-step workflow with roles, automatic checks or guardrails (subagents, hooks, an orchestrating skill) | **Harness** |

When two fit, prefer the simplest one that meets the goal (Skill < MCP < Plugin < Harness).
Say which you chose and why in one sentence.

If the task depends on the team's existing documents or screens, plan to run
`learn-doc-conventions` or `learn-design-system` first so the result follows the team's format.

## 3. Report what is missing

Before building, show a short checklist of what you have and what is still missing for the
chosen type. Required items per type:

- **Skill:** name, one-sentence purpose, trigger phrases, step-by-step procedure, output
  format, examples or a style guide if the output must match a format.
- **MCP server:** system to connect, operations needed (read vs write), auth method (env var
  name only, never the secret itself), language (Python default), where it will run.
- **Plugin:** components to include, plugin name, who installs it, distribution (marketplace
  repo or local path).
- **Harness:** stages of the workflow, role of each subagent, checks that must run
  automatically (hooks), where human approval is required, success criteria.

Ask only for missing items. Fill sensible defaults yourself and state them as assumptions.

## 4. Write and confirm the forge spec

When nothing required is missing, write `forge-spec.md` in the current working directory
(or where the person asks) using this shape:

```markdown
# Forge spec: <name>

- Type: skill | mcp | plugin | harness
- Name: <kebab-case-name>
- Purpose: <one sentence>
- Users: <who>
- Trigger phrases: <what people will say, in their language>
- Inputs: <...>
- Outputs: <...>
- Systems: <... or none>
- Conventions: <path to style guide / design format, or none>
- Install location: personal (~/.claude/...) | project (.claude/...) | plugin
- Assumptions: <defaults you chose>
- Open questions: <anything left for later>

## Procedure
1. ...
```

Show the spec summary and ask the person to confirm or correct it. After they confirm, use the
matching generator skill: `forge-skill`, `forge-mcp`, `forge-plugin` or `forge-harness`.

## Rules

- Never put secrets, passwords, API keys or customer personal data into a spec or a
  generated file. Refer to environment variable names instead.
- Don't invent the team's conventions. If you have no examples, say the output will use a
  generic format and offer to learn from examples.
- Keep company names and confidential data out of reusable templates; use placeholders.
