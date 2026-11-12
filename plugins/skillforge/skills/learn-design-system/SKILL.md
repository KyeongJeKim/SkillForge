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

Also look next to the screenshots for the team's existing **screen or function specs**
(기능명세서, 화면 정의서, e.g. `examples/specs/`, `FS-*.md`, `.docx`, `.hwpx`). If there are two or
more, the new page spec is written in their format (step 5), so read them now, not after designing.
What they settle shortens step 4 but does not replace it: still confirm, ask, and play back before designing.

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

## 4. Confirm before designing

Before drawing anything, show in one message what the screenshots settle (numbered, one line
each) and ask, one at a time, only what changes the screen and isn't in the request: the main
task and flow (how the user finds the item, what they confirm), required fields and rules, the
device and orientation. Offer a default for each ("잘 모르시면 ~로 하겠습니다"). Two to four
questions is usual; if the request already answers them, confirm and go on.

Policy values the person didn't give (rates, limits, fees, periods) are never invented: write
`[확인 필요: ...]` in the spec and show a visible placeholder in the prototype. When the person
corrects a value or a rule, change it in every file that carries it.

## 5. Design the new page

Produce:

1. A **page spec**: purpose, users, entry points, layout, components, states, copy, edge cases.
   **If the team has existing specs** (found in step 1, or a format from `learn-doc-conventions`),
   write the page spec as the next document of that series, not in a format of your own:
   - First compare them (`python3` may be `python` or `py -3` on Windows):
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/compare_examples.py" <spec folder or files>`
   - Keep every section with the same names, numbering and order, and the same header table, and
     add no sections of your own (no appendix). Put screen content inside the matching sections
     (화면 흐름, 기능 상세, 예외 처리 …); the visual details already live in `design-format.md` and
     the prototype. A document's own version (버전) starts fresh (0.1 for a draft), not after the
     examples' versions.
   - A field the comparison calls a sequence (기능 ID, file name) takes the **next number** it
     reports (e.g. FS-POS-022), with requirement rows numbered the same way (FS-POS-022-01 …).
     Never leave the ID as `[확인 필요]`; if the team assigns numbers elsewhere, use the next number
     and say in the hand-over that it is provisional. Name the file like the examples
     (`FS-POS-022.md`, or the examples' pattern), with no brackets or spaces.
   - Check it, fix what it lists, and repeat until it passes:
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/compare_examples.py" <spec folder or files> --check <new spec>`
2. A **prototype** as one self-contained HTML file (no external fonts, scripts or images) sized for
   the target screen, using only the colors, type, spacing and components from `design-format.md`.
   Include the main flow and the key states (empty, error, approval), switchable for review.
   Text must still fit on other people's machines, where Korean and number fonts are often wider:
   - Font stack ends in common Korean system fonts:
     `font-family: Pretendard, "Apple SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", sans-serif;`
   - No fixed `width`/`height` on boxes that hold text; use padding, `min-width` and wrapping.
     One-line labels (buttons, badges, tabs, table cells) keep room for text about 20% wider.
   - Put this overflow check at the end of the HTML. Opening the file with `#check` at the end
     of the address outlines in red any box whose text doesn't fit:
     ```html
     <script>
     if (location.hash === "#check") document.querySelectorAll("body *").forEach((el) => {
       const s = getComputedStyle(el);
       if (s.display === "inline" || /auto|scroll/.test(s.overflow)) return;
       if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
         el.style.outline = "2px solid red";
     });
     </script>
     ```
3. A short note on how it compares to the leaders (table stakes met, improvements added).

In the hand-over, say in one line which format the spec follows (e.g. "기존 명세서 3개와 같은
7개 섹션, 번호는 FS-POS-022").

Before hand-over, check the prototype in every state against each rule in `design-format.md`
(for example "one primary button per screen") and against the text-fit rules above, and fix what
breaks them.

Tell the person how to look at it: open the HTML file in a browser (double-click it). To check
that nothing overflows, add `#check` to the end of the address; red outlines mark text that doesn't fit.

Improvements are expressed inside the team's format: new behavior, not a new visual style.

## 6. Confirm and reuse

Ask the person to check the design format and the prototype, and end the turn there; if they
say they'll look later, that's the end of this step, not something to wait on. Then offer to package
`design-format.md` as a Skill with `forge-skill`, so future pages follow it automatically.

Write everything in the person's language. Don't delete files unless the person asks. Git and SkillForge files: run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.
