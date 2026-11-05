# Starter template: project management and QA/QC

Use with `forge-intake` when the person manages projects as a PM and handles part of QA/QC.
Confirm each item with the person.

## Common needs and suggested artifacts

| Need | Suggested type | Notes |
| --- | --- | --- |
| Status reports and meeting notes in the team's format | Skill | Learn from recent reports |
| Project brief or PRD in the team's format | Skill | Use `learn-doc-conventions` |
| Test cases and QA checklists generated from requirements | Skill | Each requirement maps to test cases |
| Read or update tickets in the issue tracker | MCP server | Write actions need the person's approval |
| Requirement review: drafter, reviewer and traceability check | Harness | Reviewer subagent + required-sections hook |

## Questions to ask

- Which project and issue tools do you use?
- What does a good status report, brief or test plan look like? Can you share examples?
- What are the QA/QC gates a release must pass?
- Who approves each stage?

## Hard parts to ask about (deep interview)

- 리뷰어가 가장 자주 돌려보내는 부분 (예: 비목표 누락, 측정할 수 없는 수용 기준)
- ID와 번호 규칙 (REQ-xx, TC-xx, 문서 번호), 우선순위 표기
- 정보가 모자란 요청: 기한·담당이 모호할 때 `[확인 필요]`로 둘지
- QA: 요구사항마다 최소 몇 개의 케이스, 예외·회귀 케이스를 따로 둘지, 결과 값(Pass/Fail/Blocked/N/A)
- 승인 단계: 누가 언제 확정하는지

## Guardrails

- Nothing is posted to shared channels or trackers without the person's approval.
