# Starter template: data analysis and AI-assisted development

Use with `forge-intake` when the person analyzes data or builds apps with AI-assisted
(vibe) coding. These are starting points; confirm each one with the person.

## Common needs and suggested artifacts

| Need | Suggested type | Notes |
| --- | --- | --- |
| Write SQL that follows the team's naming and table conventions | Skill | Learn conventions from 3-5 existing queries |
| Standard analysis report (question, method, result, caveats) | Skill | Learn the format with `learn-doc-conventions` |
| Query a data warehouse or internal API directly | MCP server | Read-only first; credentials from env vars |
| Code review and test checks before a commit | Harness | Reviewer subagent + `PostToolUse` lint/test hook |
| Share all of the above with the team | Plugin | One install for everyone |

## Questions to ask

- Which data sources and tools do you use (warehouse, BI tool, notebooks, repos)?
- Is there a naming convention for tables, columns, files or branches?
- What does a finished deliverable look like (dashboard, report, script, PR)?
- What must always be checked before you share a result (data freshness, row counts, tests)?

## Hard parts to ask about (deep interview)

- 숫자의 기준: 집계 기준일·시간대, 취소·반품 포함 여부, 단위와 반올림
- 비교 기준: 전주·전년 동기·목표 대비 중 무엇을 쓰는지, 데이터가 없을 때 표시 방법
- 데이터가 이상할 때: 결측·중복·급변을 어떻게 표시하고 누구에게 알리는지
- 보안: 고객 단위 데이터·개인정보를 결과에 넣지 않는 규칙, 접속 정보는 환경변수 이름만
- 코드 규칙: SQL·파이썬 스타일, 리뷰에서 자주 지적받는 부분

## Guardrails

- Never put credentials or connection strings in files; use environment variables.
- Start database tools read-only.
