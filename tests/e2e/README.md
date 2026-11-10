# 시나리오 테스트 (End-to-end scenarios)

실제 Claude Code 세션으로 SkillForge를 처음부터 끝까지 돌려 보고, 결과를 자동으로 판정합니다.
단위 테스트와 달리 **Claude 사용량이 듭니다** (전체 한 번에 약 20달러, 10~15분, 작성 시점 기준).
그래서 기본 테스트(`python3 -m unittest discover -s tests`)에는 들어 있지 않습니다.

```bash
tests/e2e/run.sh                    # 전체 시나리오
tests/e2e/run.sh ecommerce pos-spec # 일부만
SF_E2E_OUT=/tmp/sf-e2e tests/e2e/run.sh   # 결과 폴더 지정
python3 tests/e2e/check.py /tmp/sf-e2e    # 이미 돌린 결과만 다시 판정
```

필요한 것: 로그인된 `claude` CLI, Python 3.10+ (MCP 시나리오가 `mcp` 패키지를 설치합니다).

## 무엇을 확인하나요

| 시나리오 | 확인하는 것 |
| --- | --- |
| `ecommerce` | 예전 프로모션 기획서 3개 → 기획서 스킬 생성 → 새 세션에서 그 스킬이 말로 실행되어 초안 파일 작성 |
| `pos-spec` | 기존 기능명세서 3개 → 명세서 스킬 → 새 세션에서 초안 작성 |
| `pos-design` | 기존 POS 화면 캡처 3장 → 디자인 양식 + 화면 명세 + HTML 시안 |
| `pm-qa` | 주간 보고서·요구사항 예시 → 스킬 2개 → 새 세션에서 각각 실행 |
| `data-dev` | SQL·보고서 예시 → 보고서 스킬 + 읽기 전용 MCP 서버 뼈대, 둘 다 검증 통과 |
| `explain-choose` | 네 가지 유형 설명 후 고르기 |
| `ambiguous` | "뭘 해야 할지 모르겠어요" → 질문 3개 이하 |
| `offtopic-*` | 엑셀 수식, 시차, 대시보드 한 개, PRD 한 개: SkillForge가 **끼어들지 않아야** 통과 |

모든 시나리오 공통: 요청 없는 git 커밋 없음, SkillForge 자체 파일 수정 없음(테스트용 복사본으로 확인), 오류 없이 끝남.

## 안전장치

- 플러그인은 결과 폴더에 복사한 사본을 `--plugin-dir` 로 불러옵니다. 실제 저장소는 건드리지 않습니다.
- 세션마다 `git push` 를 막습니다.
- 시험 세션이 `claude mcp add -s user` 로 사용자 범위에 MCP 서버를 등록하면(forge-mcp 의 정상 안내), 그 시나리오가 끝나는 즉시와 실행 끝에 등록을 지우고 `summary.json` 의 `leaked_user_mcp` 에 남깁니다. 지우지 않으면 다음 세션들이 그 서버를 보고 "이미 있다"며 인터뷰를 건너뜁니다(2026-11-10 발견).
- 예시 문서와 화면(`fixtures/`)은 모두 가상의 내용입니다. 화면 캡처는 `fixtures/make_screens.py` 로 다시 그릴 수 있습니다.
