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

## Hard parts to ask about (deep interview)

- 기능 ID·화면 ID 규칙과 번호 매기는 방법 (기존 문서가 제각각이면 어느 쪽으로 통일할지)
- 필수 섹션 (특히 예외 처리, 권한, 변경 이력)과 선택 섹션
- 화면: 기기와 해상도(태블릿 가로 등), 비활성·오류·로딩 상태, 옛 스타일 화면 구분
- 결제·환불처럼 돈이 오가는 기능의 예외 (부분 취소, 통신 오류, 이중 결제)
- 매장 직원이 실수하기 쉬운 지점과 권한(점장 승인 등)

## Guardrails

- Hide customer and transaction data in screenshots before sharing.
- New designs stay within the existing design format; improvements are behavior, not a new style.
