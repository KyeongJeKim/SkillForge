# Starter template: data analysis and AI-assisted development

Use with `forge-intake` when the person analyzes data or builds apps with AI-assisted
(vibe) coding. These are starting points; confirm each one with the person.

## Common needs and suggested artifacts

| Need | Suggested type | Notes |
| --- | --- | --- |
| Write SQL that follows the team's naming and table conventions | Skill | Learn conventions from 3-5 existing queries |
| Standard analysis report (question, method, result, caveats) | Skill | Learn the format with `learn-doc-conventions` |
| Query a data warehouse or internal API directly | MCP server | Read-only first; credentials from env vars |
| Code review and test checks before a commit | Harness | Reviewer subagent + `PostToolUse` lint/test hook |
| Share all of the above with the team | Plugin | One install for everyone |

## Questions to ask

- Which data sources and tools do you use (warehouse, BI tool, notebooks, repos)?
- Is there a naming convention for tables, columns, files or branches?
- What does a finished deliverable look like (dashboard, report, script, PR)?
- What must always be checked before you share a result (data freshness, row counts, tests)?

## Guardrails

- Never put credentials or connection strings in files; use environment variables.
- Start database tools read-only.
