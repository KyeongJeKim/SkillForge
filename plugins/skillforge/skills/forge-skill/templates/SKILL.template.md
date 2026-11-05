---
name: {{SF: skill-name}}
description: "{{SF: What this skill does, in one sentence.}} Use when {{SF: the situations and the exact phrases people say, in their language}}. {{SF: Optional: Do not use for ...}}"
---

# {{SF: Skill title}}

{{SF: One or two sentences on the goal and who uses it.}}

## Inputs

- {{SF: What the person provides. Mark which items are required and which have defaults.}}

## Procedure

1. Read the request and collect the inputs above. If a required input is missing, still write the
   full draft: put `[확인 필요: ...]` where the value belongs, then list those items at the end.
   Ask questions after the draft, not before, unless the request is too vague to start.
2. {{SF: Step}}
3. {{SF: Step}}
4. Save the result as a file named {{SF: file naming rule}} in {{SF: folder, default: current folder}}.
5. {{SF: Check step, e.g. run python3 "${CLAUDE_SKILL_DIR}/scripts/check.py" <file>, or delete this step}}

## Output format

{{SF: Exact structure of the result: sections in order, fields, tables, naming. Point to reference/style-guide.md when it exists.}}

## Rules

- Reply in the person's language. Keep the hand-over short: where the file is, and the `[확인 필요]` items.
- Don't commit, push, send or delete anything unless the person asks.
- {{SF: Team rule, e.g. "Never include customer personal data."}}
