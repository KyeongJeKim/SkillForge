---
name: learn-design-system
description: "Learns a team's UI design format from screenshots of its existing screens (e-commerce pages, POS screens, admin tools) and designs a new screen or page that stays within that format while matching or improving on market-leading products, with a page spec and an HTML prototype. Use when someone needs a new screen, page or UI flow that must look like the rest of their product, e.g. 기존 화면이랑 톤 맞춰서 새 화면 만들어 줘, 새 POS 화면 디자인해 줘, design a new page like our existing ones, or when forge-intake needs a design format. Do not use for planning documents without a screen (기획서 only); use learn-doc-conventions for those."
---

# Learn a design system and design within it

## 1. Ask for screenshots

Ask for **3 to 6 screenshots of real screens** in use: at least one list or table screen,
one detail or form screen, and one screen with buttons and states (empty, error, loading) if
they exist. Ask which platform they target (web, tablet POS, mobile) and the screen sizes.

Ask the person to hide customer names, prices they consider confidential and other personal
data before sharing. They can paste a screenshot into the terminal (Ctrl+V, or Cmd+V on Mac),
drag image files in, or give a folder path. Look in the current folder first (e.g. `examples/`).

## 2. Extract the design format

From the screenshots, record what you can actually see. Mark estimates as estimates.

| Area | What to record |
| --- | --- |
| Layout | Grid, navigation position, header, sidebars, density, max widths |
| Color | Primary, secondary, background, surface, text, status colors (approximate hex) |
| Typography | Font style (serif/sans), relative sizes for title / body / caption, weights |
| Spacing and shape | Spacing rhythm, corner radius, borders, shadows |
| Components | Buttons (primary/secondary/destructive), inputs, tables, cards, tabs, modals, toasts |
| States | Hover, selected, disabled, empty, loading, error |
| Copy | Tone, capitalization, labels, Korean/English usage, units and number formats |
| Patterns | How search, filters, bulk actions, confirmation and navigation work |

Write `design-format.md` with these sections plus a short "Do / Don't" list. This is the
**constraint**: new work must not break it.

## 3. Benchmark against market leaders

For the page or feature requested, find how leading products in the same space handle it
(for e-commerce and POS, the major commerce and point-of-sale platforms). Use web search when
it is available and cite what you looked at; if not, say the comparison is from general
knowledge and may be out of date.

List, briefly:

- **Table stakes:** what every leader has; the new design must have these.
- **Improvements:** patterns that would make the team's version better.
- **Not adopted:** ideas that would break the team's format, and why.

## 4. Design the new page

Produce:

1. A **page spec**: purpose, users, entry points, layout, components, states, copy, edge cases.
   If the team has a function-spec format (from `learn-doc-conventions`), write it in that format.
2. A **prototype** as one self-contained HTML file (no external fonts, scripts or images) sized for
   the target screen, using only the colors, type, spacing and components from `design-format.md`.
   Include the main flow and the key states (empty, error, approval), switchable for review.
3. A short note on how it compares to the leaders (table stakes met, improvements added).

Tell the person how to look at it: open the HTML file in a browser (double-click it).

Improvements are expressed inside the team's format: new behavior, not a new visual style.

## 5. Confirm and reuse

Ask the person to check the design format and the prototype. Then offer to package
`design-format.md` as a Skill with `forge-skill`, so future pages follow it automatically.

Write everything in the person's language. Don't delete files unless the person asks. Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.
