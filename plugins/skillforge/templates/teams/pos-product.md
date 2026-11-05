# Starter template: POS product (UI/UX, planning, function specifications)

Use with `forge-intake` when the person works on a point-of-sale product: screen design,
planning documents and function specifications. Confirm each item with the person.

## Common needs and suggested artifacts

| Need | Suggested type | Notes |
| --- | --- | --- |
| Function specification in the team's format | Skill | Learn from 3-5 specs with `learn-doc-conventions` |
| Planning document for a new feature | Skill | Learn the team's planning template |
| New screen that matches existing screens and benchmarks market leaders | Skill | Use `learn-design-system` with screenshots |
| Spec review: completeness, edge cases, error states, offline behavior | Harness | Reviewer subagent + required-sections hook |
| Package design and spec skills for the whole team | Plugin | One install |

## Questions to ask

- Which devices and screen sizes does the POS run on (terminal, tablet, mobile)?
- Can you share screenshots of 3-6 current screens and 3-5 recent function specs?
- Which flows matter most (checkout, refunds, discounts, inventory, shifts)?
- Which states must every screen handle (offline, error, loading, permission denied)?

## Guardrails

- Hide customer and transaction data in screenshots before sharing.
- New designs stay within the existing design format; improvements are behavior, not a new style.
