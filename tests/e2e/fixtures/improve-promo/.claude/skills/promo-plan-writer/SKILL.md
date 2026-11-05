---
name: promo-plan-writer
description: "Writes a promotion plan (프로모션 기획서) in the e-commerce team's format from the event basics. Use when someone says 프로모션 기획서 써 줘, 기획전 기획안 초안, 이벤트 기획서 만들어 줘, write a promo plan."
---

# Promotion plan writer

Writes a first draft of a promotion plan for the e-commerce operations team.

## Inputs

- Required: event name, period, benefits, target sales.
- Optional: background, channels, budget. Missing values become `[확인 필요: ...]`.

## Procedure

1. If `corrections.md` exists in this skill's folder, read it first and follow every rule in it.
2. Read the request and collect the inputs above. If a required input is missing, still write the
   full draft with `[확인 필요: ...]` and list those items at the end.
3. Write the sections in this order: 1. 배경, 2. 목표, 3. 행사 개요, 4. 혜택, 5. 일정, 6. 예산, 7. 리스크 및 대응.
4. Save the result as `promo-YYYY-MM_<행사명>.md` in the current folder.

## Output format

- Title: `# YYYY <행사명> 기획안`
- 목표: target sales as given.
- 혜택: a table with 혜택, 대상, 조건.
- 일정: a table with 단계, 날짜, 담당.

## When the person corrects a result

1. Apply the correction to the current result right away.
2. If it should hold next time too (they say 다음부터, 항상, 앞으로, or correct the same thing
   twice), add one line to `corrections.md` in this skill's folder (create it if missing):
   `- YYYY-MM-DD: <the rule in their words>`. Write the rule only, never customer data,
   confidential numbers or the document's content.
3. If that folder can't be written, skip the log and say in one line that SkillForge can make the
   change permanent ("이 스킬 개선해 줘").

## Rules

- Reply in the person's language. Keep the hand-over short: where the file is, and the `[확인 필요]` items.
- Don't commit, push, send or delete anything unless the person asks.
