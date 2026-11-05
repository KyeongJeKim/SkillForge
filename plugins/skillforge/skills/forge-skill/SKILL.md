---
name: forge-skill
description: "Generates a working Claude Skill (a SKILL.md folder with optional style guide and check script) from a confirmed SkillForge spec, makes its description trigger from natural language, tests it and validates it. Use after forge-intake has a confirmed spec of type skill, or when the person has already agreed what the skill should do and says to turn it into a skill (e.g. 이걸 스킬로 만들어 줘). If the need is still vague, start forge-intake instead."
---

# Forge a Skill

## Inputs

A confirmed `forge-spec.md` with type skill, or a clear agreement in the conversation. If the
purpose, triggers or procedure are missing, go back to `skillforge:forge-intake`.

## Steps

1. **Location** from the spec (default: project `.claude/skills/<name>/`):
   personal `~/.claude/skills/<name>/`, project `.claude/skills/<name>/`, or plugin `<plugin>/skills/<name>/`.
2. **Copy** [templates/SKILL.template.md](templates/SKILL.template.md) to `<location>/SKILL.md`
   and replace every `{{SF: ...}}` blank. Delete optional lines you don't need.
3. **Description** (the only thing Claude sees before deciding to load the skill):
   - First sentence: what it does. Then "Use when ..." with the real phrases people say, in their
     language (Korean and English if the team uses both). Add "Do not use for ..." if a nearby
     request should not trigger it.
   - Wrap the whole value in double quotes. Under 1024 characters. No `<` or `>`.
4. **Name:** lowercase letters, digits and hyphens, at most 64 characters, same as the folder.
5. **Body:** numbered procedure, output format, quality bar, edge cases, corrections and rules.
   Copy the spec's 품질 기준, 예외 처리 and 금지·승인 into the skill's Quality bar, Edge cases and
   Rules sections as concrete checks, not general advice: "목표 매출은 전년 대비 %와 금액을 함께 쓴다",
   not "write a good target". Keep the "When the person corrects a result" section from the
   template; it is how the skill keeps learning. Keep `SKILL.md` under 500 lines; put long
   material (style guide, examples, checklists) in sibling files linked with relative paths.
6. **Draft first:** the generated skill must produce the full result right away, marking unknown
   values as `[확인 필요: ...]` and listing them at the end, instead of asking questions before it
   starts. It asks first only when the request is too vague to begin.
7. **Conventions:** if a style guide or design format was learned, copy it to
   `reference/style-guide.md` (or `reference/design-format.md`) and tell the skill to follow it.
8. **Scripts (optional):** put deterministic checks in `scripts/` and call them as
   `python3 "${CLAUDE_SKILL_DIR}/scripts/<name>.py"` so they work from any folder.
   Standard library only, unless the person agrees to a dependency.
   If the person uses Windows, write `python` (or `py -3`) instead of `python3` in the skill.
9. **Validate**, fix every error, re-run until it passes:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" skill <location>
   ```

10. **Try it yourself:** follow the new skill once on a realistic example (use the person's examples
    if there are any) and check the result against the style guide, the quality bar and one edge case
    from the spec. Fix the skill if the result is off. Save the trial output somewhere clearly named (e.g. `skillforge-trial/`) and say so. Trial
    files must not change how the skill behaves later: anything that scans existing documents (next
    ID, latest report) skips `skillforge-trial/`.
    The person is waiting: one trial on one example, at most one fix and retry, no extra reviewer
    or tester subagents. If more testing would clearly help, offer it in the hand-over instead.

11. **Claude app users:** if the spec says the users work in the Claude app (claude.ai or the Chat
    tab of Claude Desktop) rather than Claude Code, also make an upload file and say where it is:

    ```bash
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/package_skill.py" <location>
    ```

    They upload it in Settings > Capabilities > Skills (code execution must be on). The Code tab of
    Claude Desktop uses the skill folder or plugin as is.

## Hand-over (in the person's language, short)

1. Where the skill is, in one line.
2. Two example sentences that start it, and one that should not.
3. What you assumed, as a short list.
4. One line: when they correct a result, the skill remembers it, and "이 스킬 개선해 줘" makes it permanent.

Don't paste commands they don't need to run. Don't delete files unless they ask.

Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.

## Rules

- No secrets, credentials or customer personal data in the skill files.
- Don't copy confidential document content into templates; use placeholders.
- Don't add `allowed-tools` unless the person wants to restrict tools.
