---
name: learn-design-system
description: Learns a team's UI/UX design format from screenshots of its existing screens (e-commerce pages, POS screens, admin tools) and designs new pages or features that stay within that format while matching or improving on market-leading products. Use when someone needs a new screen, page or feature design that must look like the rest of their product, e.g. "design a new page like our existing ones", "make a new POS screen", "기존 화면이랑 톤 맞춰서", "새 페이지 기획해 줘", or when forge-intake needs a design format before building a design skill.
---

# Learn a design system and design within it

## 1. Ask for screenshots

Ask for **3 to 6 screenshots of real screens** in use: at least one list or table screen,
one detail or form screen, and one screen with buttons and states (empty, error, loading) if
they exist. Ask which platform they target (web, tablet POS, mobile) and the screen sizes.

Ask the person to hide customer names, prices they consider confidential and other personal
data before sharing.

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
2. A **prototype** as a single HTML file that uses only the colors, type, spacing and
   components from `design-format.md`, so it looks like the team's existing screens.
3. A short note on how it compares to the leaders (table stakes met, improvements added).

Improvements are expressed inside the team's format: new behavior, not a new visual style.

## 5. Confirm and reuse

Ask the person to check the design format and the prototype. Then offer to package
`design-format.md` as a Skill with `forge-skill`, so future pages follow it automatically.
