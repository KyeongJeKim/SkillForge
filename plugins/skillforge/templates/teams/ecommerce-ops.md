# Starter template: e-commerce operations

Use with `forge-intake` when the person runs online store operations: product listings,
promotion planning and customer inquiries. Confirm each item with the person.

## Common needs and suggested artifacts

| Need | Suggested type | Notes |
| --- | --- | --- |
| Product listing copy in the store's format (title, bullets, specs, keywords) | Skill | Learn from 3-5 good existing listings |
| Promotion plan (goal, period, offer, channel, budget, success metric) | Skill | Learn the team's plan template |
| Customer inquiry replies in the brand's tone, by inquiry type | Skill | Draft only; a person sends |
| Look up orders, stock or listing status in a store system | MCP server | Read-only first |
| Listing QA before publishing (required fields, banned words, image count) | Harness | Checker subagent + hook on written files |

## Questions to ask

- Which marketplaces or store platforms do you sell on, and do formats differ by channel?
- Which listings or promotions are good examples to learn from?
- Are there words, claims or formats that are not allowed?
- Which inquiry types come up most, and which need a person to answer?

## Guardrails

- Drafted customer replies are never sent automatically.
- Remove customer names, addresses and order details from examples before learning from them.
