---
name: forge-skill
description: "Generates a working Claude Skill (a SKILL.md folder with optional style guide and check script) from a confirmed SkillForge spec, makes its description trigger from natural language, tests it and validates it. Use after forge-intake has a confirmed spec of type skill, or when the person has already agreed what the skill should do and says to turn it into a skill (e.g. 이걸 스킬로 만들어 줘). Also use to package an existing skill as a ZIP for the Claude app (claude.ai or Claude Desktop chat), e.g. 이 스킬 Claude 앱에 올리게 zip으로 만들어 줘; then run only step 11. If the need is still vague, start forge-intake instead."
---

# Forge a Skill

## Inputs

A confirmed `forge-spec.md` with type skill, or a clear agreement in the conversation. If the
purpose, triggers or procedure are missing, go back to `skillforge:forge-intake`.

**Before you build:** if this conversation has no confirmed `forge-spec.md` (the person said yes to a
played-back summary), start `skillforge:forge-intake` first, even when the request looks complete.
It can be short when the examples answer most questions, but it still confirms what they settle,
asks about the hard parts and plays back the summary before anything is built.
Packaging an existing skill as a ZIP (step 11 alone) needs no spec.

## Steps

1. **Location** from the spec (default: project `.claude/skills/<name>/` in the current folder):
   personal `~/.claude/skills/<name>/`, project `.claude/skills/<name>/`, or plugin `<plugin>/skills/<name>/`.
   Use personal only when the person chose it; if the spec marks it as an assumption, use project
   and say so in the hand-over (personal skills load in every other project they open).
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
   Even when the person wants missing numbers asked for, the skill writes the draft and then asks
   for them in one numbered list. "없으면 물어봐 주세요", "추측하지 말고 먼저 물어봐" for one input
   means: don't guess that value, leave it as written or `[확인 필요]`, save the draft, and put that
   question first in the reply. Write the skill's step that way, not as "stop and wait before
   writing"; only when the person says no draft may exist until they answer does the skill wait. A missing optional input (last year's data, a reference file)
   leaves that part marked, never the whole draft. A check script reports problems next to the
   draft; it never stops the draft from being written. Use `[확인 필요]` only for values the
   input really lacks; write what the input states plainly, and a team default as a default.
   **Save without asking:** when the result is a document or file, the skill writes it to the file in
   the same turn ("정리해서 저장해 주세요" means write it now), then lists the `[확인 필요]` items.
   It never asks "저장할까요?" first. The spec's 금지·승인 rules (승인 전 발송 금지, 리드 확인 후 확정)
   cover sending, posting, finalising and overwriting an existing file, never writing the draft; say
   so in the skill's Rules so the two don't get mixed up.
   **Fill rules from the examples:** when the spec came with 2 or more examples, use the comparison
   from the interview, or run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/compare_examples.py" <examples>`,
   and write a `Fill rules` table into the skill's Output format, one row per header field:
   same in every example → write that value as the default; counts up → the next number after the
   newest such file in the save folder, or after the newest example when there is none (new files are
   never saved into the examples folder; the examples only seed the number); date → the
   request, else today; varies → the request, else `[확인 필요]`. A value is `[확인 필요]` only when
   its row says so and the request doesn't give it. Copy sentences that every example shares only when
   the person confirmed they are fixed wording, and never copy one period's content (last week's tasks,
   last event's numbers) into a new document.
7. **Conventions:** if a style guide or design format was learned, copy it to
   `reference/style-guide.md` (or `reference/design-format.md`) and tell the skill to follow it.
8. **Scripts (optional):** put deterministic checks in `scripts/` and call them as
   `python3 "${CLAUDE_SKILL_DIR}/scripts/<name>.py"` so they work from any folder.
   Standard library only, unless the person agrees to a dependency.
   A generated skill never points at `${CLAUDE_PLUGIN_ROOT}` (SkillForge's folder): a teammate who
   gets the skill doesn't have it. Copy what it needs into its own `scripts/` instead.
   **Office files:** when the examples, or the files the skill will read, include .docx, .xlsx,
   .pptx, .hwpx or .hwp, copy `${CLAUDE_PLUGIN_ROOT}/scripts/extract_text.py` into
   `<location>/scripts/extract_text.py` (standard library only) and keep the template's Office-files
   lines in Inputs; otherwise delete them. The skill then reads every example and input, not only
   the .md ones. The validator fails a skill that runs a script it doesn't carry.
   If the person uses Windows, write `python` (or `py -3`) instead of `python3` in the skill.
9. **Validate**, fix every error, re-run until it passes:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" skill <location>
   ```

10. **Try it yourself:** follow the new skill once on a realistic example (use the person's examples
    if there are any) and check the result against the style guide, the quality bar and one edge case
    from the spec. Phrase the trial the way the person would ("…정리해서 저장해 주세요"); it must end with the
    file written and, when examples are Office files, with them read. If the skill stopped to ask
    before writing, fix the skill. Fix the skill if the result is off. Save the trial output somewhere clearly named (e.g. `skillforge-trial/`) and say so. Trial
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
    Claude Desktop uses the skill folder or plugin as is. You can't send a file into their chat
    window or see their screen: give the ZIP's full path once, and the upload steps in three short
    lines. If the upload doesn't work for them, say their organisation may need to allow skills and
    stop there; don't switch to other workarounds unasked.

## Hand-over (in the person's language, short)

1. Where the skill is, in one line.
2. Two example sentences that start it, and one that should not.
3. What you assumed, as a short list.
4. One line: when they correct a result, the skill remembers it, and "이 스킬 개선해 줘" makes it permanent.

End the hand-over without a question. Don't offer extras (a ZIP, a plugin, more tests) the spec
didn't ask for; one short line saying they exist is enough.

Don't paste commands they don't need to run. Don't delete files unless they ask.

Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.

## Rules

- No secrets, credentials or customer personal data in the skill files.
- Don't copy confidential document content into templates; use placeholders.
- Don't add `allowed-tools` unless the person wants to restrict tools.
