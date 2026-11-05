---
name: learn-doc-conventions
description: "Learns a team's document conventions from 3 to 5 existing examples (function specifications, PRDs, planning docs, reports, promotion plans, listings) and writes a reusable style guide that new documents and generated skills follow. Use this first, before asking for the files yourself, when there is no skill or style guide yet for that kind of document and someone wants new ones to keep matching the existing format, e.g. 기존 문서 스타일 배워서 양식 정리해 줘, 우리 명세서 양식 뽑아 줘, 예시 드릴 테니 양식 정리해서 앞으로 그대로 쓰게 해 주세요, learn our PRD style, or when forge-intake needs conventions before building a document skill. Do not use when a skill for that document type already exists; use that skill instead."
---

# Learn document conventions

## 1. Ask for examples

Ask for **3 to 5 recent, representative documents** of the same kind (more is better than
one). Accept files, pasted text or links the person can open for you. Ask which ones are
considered good examples, and whether any are outdated.

If the person can share only one, continue but mark every rule as "seen once".

**File formats:** Claude reads Markdown, text, PDF and images directly. For Word, Excel,
PowerPoint and Hangul (한글) files run the bundled extractor and read its output (on Windows use
`python` or `py -3` if `python3` is not found):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/extract_text.py" <file.docx|.xlsx|.pptx|.hwpx|.hwp> ...
```

The extractor gives text and tables but not fonts, colors or page layout. When the look matters
(a form with boxes, a poster), also ask for a PDF or a screenshot of one page. If it says a `.hwp`
is password-protected or 배포용, or the file is `.doc`, `.xls` or `.ppt`, ask for a PDF export
("다른 이름으로 저장 → PDF") or pasted text. Tell the person they can drag files into the terminal or give the folder path.

## 2. Extract the conventions

Read every example and compare them. Capture:

| Area | What to record |
| --- | --- |
| Structure | Section order, heading names and levels, mandatory vs optional sections |
| Metadata | Header fields (owner, version, date, status, IDs) and their format |
| Identifiers | How requirements, functions or tickets are numbered (e.g. `FR-001`) |
| Content units | How one requirement / function / item is written (fields, tables, user story, acceptance criteria) |
| Language | Voice, tense, formality, Korean/English mixing, terminology and abbreviations |
| Formatting | Tables vs lists, bold, code blocks, diagrams, screenshots, numbering |
| Quality rules | What every good example has (e.g. edge cases, error states, non-functional requirements) |

For each rule, note how many examples follow it (e.g. "5/5", "3/5"). Classify:

- **Required:** in all or nearly all examples.
- **Common:** in most examples; use by default.
- **Varies:** differs between examples; ask the person or choose per case.

## 3. Write the style guide

Write `style-guide.md` (where the person wants; default current folder), in the language of the
examples, with:

1. Scope: document type, team, examples used (titles only), date learned.
2. A **skeleton**: the section headings in order, with one-line guidance for each.
3. The rules table above, with counts and the Required / Common / Varies label.
4. One short **synthetic** example of a content unit written in the team's style.

Use placeholders for names, products, customers and numbers. Never copy confidential content
or personal data from the examples into the guide.

## 4. Confirm and reuse

Show the person a short summary (the skeleton and at most five Required rules, not the whole file)
and ask them to correct anything wrong. Then offer to:

- write the new document now, following the guide, or
- turn the guide into a Skill so the whole team gets documents in this format automatically: start
  `skillforge:forge-intake` (not `forge-skill` directly) so the interview confirms what the guide
  can't show (inputs, what reviewers send back, what must never appear) before anything is built;
  the guide becomes the skill's `reference/style-guide.md`.

If the person's first request was already for something that writes these documents for them
("양식대로 초안 써 주는 걸 만들어 주세요"), go straight to `skillforge:forge-intake` after the
summary instead of offering.

Don't delete files unless the person asks. Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.
