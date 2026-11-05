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

## Hard parts to ask about (deep interview)

- 상품정보제공고시·표시광고 기준: 카테고리별 필수 항목, 금지 표현(최저가, 100%, 의약품 오인 표현 등)
- 검수에서 가장 자주 돌아오는 부분 (예: 옵션명 규칙, 이미지 컷 수, 배송비 문구)
- 채널마다 다른 점 (자사몰과 오픈마켓의 글자 수·필수 칸 차이)
- 프로모션: 중복 할인 규칙, 정산(수수료·분담) 표기, 목표의 기준(전년 동기 대비 등)
- 고객 답변: 보상·환불 일정을 확답해도 되는지, 파트장 승인이 필요한 경우

## Guardrails

- Drafted customer replies are never sent automatically.
- Remove customer names, addresses and order details from examples before learning from them.
