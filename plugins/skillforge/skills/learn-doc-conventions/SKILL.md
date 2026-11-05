---
name: learn-doc-conventions
description: Learns a team's document conventions from existing examples (function specifications, PRDs, planning docs, reports, listings) and writes a reusable style guide that new documents and generated skills follow. Use when someone wants new documents to match the team's existing format, e.g. "write it the way our specs are written", "learn our PRD style", "우리 팀 양식대로", "기존 문서 스타일 따라서", or when forge-intake needs conventions before building a document skill.
---

# Learn document conventions

## 1. Ask for examples

Ask for **3 to 5 recent, representative documents** of the same kind (more is better than
one). Accept files, pasted text or links the person can open for you. Ask which ones are
considered good examples, and whether any are outdated.

If the person can share only one, continue but mark every rule as "seen once".

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

Write `style-guide.md` (where the person wants; default current directory) with:

1. Scope: document type, team, examples used (titles only), date learned.
2. A **skeleton**: the section headings in order, with one-line guidance for each.
3. The rules table above, with counts and the Required / Common / Varies label.
4. One short **synthetic** example of a content unit written in the team's style.

Use placeholders for names, products, customers and numbers. Never copy confidential content
or personal data from the examples into the guide.

## 4. Confirm and reuse

Show the person the skeleton and the Required rules and ask them to correct anything wrong.
Then offer to:

- write the new document now, following the guide, or
- package the guide as a Skill with `forge-skill` (the guide becomes
  `reference/style-guide.md`), so the whole team gets documents in this format automatically.
