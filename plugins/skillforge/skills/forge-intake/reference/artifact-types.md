# The four artifact types

Use this when the person wants to understand the options before choosing.
Explain in their language, in a few lines, with an example from their own work.

## Skill

A folder with a `SKILL.md` file (instructions) and optional scripts or reference files.
Claude reads each skill's `description` and loads the skill automatically when a request
matches it, so nobody has to type a command.

- Good for: a procedure, a document format, a checklist, a writing style.
- Example: "Write a PRD in our team's format."
- Lives in: `~/.claude/skills/<name>/` (personal), `.claude/skills/<name>/` (project) or a plugin's `skills/`.

## MCP server (Model Context Protocol)

A small program that connects Claude to an external system and exposes **tools** Claude can
call, such as "look up an order" or "query a table".

- Good for: live data or actions in a database, an API or an internal tool.
- Example: "Check today's stock for a product in our inventory system."
- Lives in: a script or service, registered with `claude mcp add` or a plugin's `.mcp.json`.

## Plugin

An installable package that bundles skills, subagents, hooks, slash commands and MCP servers.
A team installs it once from a marketplace (a Git repo) and gets everything together.

- Good for: sharing several pieces with a team and updating them in one place.
- Example: "Give every e-commerce teammate our listing, promotion and inquiry skills."
- Lives in: a folder with `.claude-plugin/plugin.json`, listed in a `marketplace.json`.

## Harness

The working setup around the model for a bigger job: which subagents do which step, which
checks run automatically (hooks), and where a person must approve. Designing this is
called harness engineering.

- Good for: multi-step workflows that need roles, quality gates or guardrails.
- Example: "Draft a function spec, have a reviewer agent check it against our template,
  and block saving if required sections are missing."
- Lives in: subagents (`agents/*.md`), hooks (`hooks/hooks.json`) and an orchestrating skill,
  usually shipped as a plugin.

## One-line summary

Skill = what Claude knows how to do. MCP = what Claude can connect to.
Plugin = the package that ships them. Harness = the workflow that runs them together.
