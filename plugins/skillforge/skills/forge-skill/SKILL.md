---
name: forge-skill
description: Generates a working Claude Skill (a SKILL.md folder) from a confirmed SkillForge spec or a clear request such as "make this a skill", "turn our PRD format into a skill", "스킬로 만들어 줘". Writes the frontmatter so it triggers from natural language, adds supporting files, and validates it before handing over. Use forge-intake first if the need is still vague.
---

# Forge a Skill

## Inputs

A confirmed `forge-spec.md` with `Type: skill`, or enough detail from the conversation to fill
one. If the purpose, triggers or procedure are missing, go back to `forge-intake`.

## Steps

1. **Pick the location** from the spec (ask if not set):
   - personal: `~/.claude/skills/<name>/`
   - project: `.claude/skills/<name>/`
   - plugin: `<plugin-root>/skills/<name>/`
2. **Copy the template** [templates/SKILL.template.md](templates/SKILL.template.md) to
   `<location>/SKILL.md` and fill every placeholder.
3. **Write the description carefully.** It is the only thing Claude sees before deciding to
   load the skill, so it decides whether natural-language triggering works:
   - First sentence: what the skill does.
   - Then "Use when ..." with the real phrases people will say, in their own language
     (include Korean and English phrases if the team uses both).
   - Keep it under 1024 characters. No angle brackets.
4. **Name:** lowercase letters, digits and hyphens, at most 64 characters, matching the folder.
5. **Body:** a numbered procedure, the output format, and rules. Keep `SKILL.md` under 500
   lines; move long material (style guides, examples, checklists) into sibling files and link
   them with relative paths.
6. **Conventions:** if the spec points to a style guide or design format from
   `learn-doc-conventions` or `learn-design-system`, copy it next to `SKILL.md` as
   `reference/style-guide.md` (or `reference/design-format.md`) and tell the skill to follow it.
7. **Scripts (optional):** put deterministic steps (formatting, checks, conversions) in
   `scripts/` and call them from the body. Use only the standard library unless the person
   agrees to a dependency.
8. **Validate:**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" skill <location>
   ```

   Fix every error and re-run until it passes. Report warnings to the person.
9. **Test the trigger:** suggest two or three sentences the person can type in a new session to
   check that the skill loads, and one sentence that should *not* trigger it.

## Hand-over

Tell the person, briefly: where the skill is, the phrases that trigger it, the validation
result, and anything you assumed.

## Rules

- No secrets, credentials or customer personal data in the skill files.
- Don't copy confidential document content into templates; replace it with placeholders.
- Don't add `allowed-tools` unless the person wants to restrict tools; explain the effect if you do.
