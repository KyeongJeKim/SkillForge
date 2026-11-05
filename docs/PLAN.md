# SkillForge 계획 (Plan)

> 대화로 필요한 것을 파악하고, 그에 맞는 **Skill · MCP · Plugin · Harness**를 자동으로 만들어 주는 도구

- **작성일:** 2026-11-05
- **출처:** KJ와의 음성 대화 (2026-11-05)
- **상태:** v0.2 품질 점검 완료 ([10. v0.2 품질 점검](#10-v02-품질-점검-2026-11-05)). 결정되지 않은 부분은 [열린 질문](#7-열린-질문-open-questions)에 정리했습니다.

---

## 1. 목표 (Goal)

누구나 **universal**하게 쓸 수 있는 framework / infrastructure를 만듭니다.

1. 사용자가 대화하면서 원하는 것을 이야기하면,
2. 도구가 "이런 이런 부분이 필요해요"라고 **부족한 정보를 알려 주고**,
3. 필요한 부분이 다 채워지면 **Skill, MCP, Plugin, Harness 중 알맞은 것을 자동으로 만들어 줍니다.**

핵심은 결과물 하나를 만들어 주는 것이 아니라 **만드는 도구 자체를 제공하는 것**입니다.
업무가 서로 달라도, 각 업무를 맡은 팀원이 이 도구로 자기 업무에 맞는 것을 직접 만들어 쓸 수 있습니다.

## 2. 첫 적용 대상 (First target)

- **환경:** Claude (팀 공용 AI 도구로 이미 Claude를 사용 중)
- **사용자:** 회사의 유닛(Unit) 팀원들. 유닛 안에 여러 서브팀이 있습니다.

| 서브팀 | 주요 업무 |
| --- | --- |
| 데이터 분석 · 앱 개발 | 데이터 분석, AI를 활용한 vibe coding 개발 |
| 이커머스 운영 | 제품 listing, 프로모션 계획, customer inquiry 대응 |
| 프로젝트 (PM) | 여러 프로젝트의 PM 역할, 필요 시 QA/QC 일부 |
| POS 시스템 | POS 개발, UI/UX 디자인, 기획서, function specification |

설계는 universal하게 하되, 처음에는 이 팀원들에게 도움이 되는 것을 목표로 합니다.

## 3. 결과물 유형 정하기: 두 가지 방식

1. **추천 방식:** 대화 내용을 보고 도구가 알맞은 유형(Skill, MCP, Plugin, Harness)을 추천합니다.
2. **선택 방식:** 도구가 각 유형이 무엇인지 설명해 주고, 사용자가 원하는 것을 고릅니다.

## 4. 예시로부터 배우기 (Learn from examples)

팀의 기존 자료를 받아 공통 규칙을 스스로 찾아내고, 그 안에서 만듭니다.

### 문서 업무 (예: function specification, PRD)

- 도구가 "어떤 문서가 있는지 알려 주세요"라고 기존 문서를 요청합니다.
- 받은 문서에서 공통된 **convention rule**, 자주 쓰는 스타일과 구성을 판단합니다.
- 그 규칙에 맞춰 새 문서 작성을 돕습니다.

### 디자인 업무 (예: UI/UX, 새 화면·페이지)

- 도구가 "실제로 쓰고 있는 화면의 screenshot을 몇 개 올려 주세요"라고 요청합니다.
- 기존 페이지와 **톤이 어긋나지 않는** 새 화면을 만듭니다.
- 기능은 이커머스·POS 시장을 선도하는 기업들과 비교해 **최소한 뒤지지 않거나 더 개선된** 수준을 제안합니다.
- 단, 팀의 디자인과 양식은 **벗어나지 않습니다.**

## 5. 제공 방식 (Delivery)

- **Claude Plugin** 형태로 만들어 팀원 각자가 설치하고, 설치·사용법은 교육으로 안내합니다.
- 팀원은 플러그인 안의 Skill이나 slash command를 일일이 입력하지 않습니다.
- "나 이런 거 만들어야 될 것 같아"처럼 **자연어로 대화를 시작하면 플러그인이 알아서 트리거되어** 작동합니다.

> 참고: Claude의 Skill은 각 Skill의 설명(description)과 사용자 요청이 맞으면 Claude가 자동으로 불러 씁니다. 자연어 트리거는 이 방식을 활용합니다.

## 6. 핵심 용어 (Skill · MCP · Plugin · Harness)

| 용어 | 한 줄 설명 | 예시 |
| --- | --- | --- |
| **Skill** | 지침(`SKILL.md`)과 필요 시 스크립트·참고 파일을 담은 폴더. 요청이 설명과 맞으면 Claude가 자동으로 불러 씁니다. | "우리 팀 PRD 양식대로 작성하기" |
| **MCP** (Model Context Protocol) server | Claude를 외부 시스템(API, DB, 사내 도구)에 연결하는 표준 방식. Claude가 호출할 수 있는 tool을 제공합니다. | 사내 DB 조회, 주문 시스템 연동 |
| **Plugin** | Skill, slash command, subagent, hook, MCP server 등을 하나로 묶어 설치·배포하는 패키지 | SkillForge 자체를 팀에 배포 |
| **Harness** | 모델이 일하는 실행 환경 전체: 지침, 도구 연결, 작업 순서, 여러 agent의 조율 방식. 이를 설계하는 것이 harness engineering입니다. | 여러 단계를 자동으로 이어 가는 작업 흐름 |

정리하면 Skill은 "할 줄 아는 일", MCP는 "연결된 도구", Plugin은 "이것들을 묶은 설치 패키지", Harness는 "전체가 돌아가는 틀"입니다.

## 7. 열린 질문 (Open questions)

- [ ] **Proactive 모드:** 팀원이 먼저 요청하지 않아도, 작업 스타일을 지켜보다가 필요한 도구를 먼저 제안하거나 만들어 줄 수 있을까요? 기술적으로 가능한지 검토가 필요합니다. 설계 메모: [PROACTIVE.md](PROACTIVE.md)
- [ ] **유형 결정 방식:** 추천 방식과 선택 방식 중 기본값을 무엇으로 할지, 또는 둘 다 제공할지
- [ ] **Universal 확장:** Claude 외 다른 환경까지 지원할 범위와 시점
- [ ] **배포·교육:** 플러그인 배포 경로와 팀원 교육 방식

## 8. 저장소 (Repository)

- **이름:** `kyeongjekim/skillforge` (private)
- **설명:** Builds skills and tools with natural language

## 9. v0.1 구현 현황

| 계획 항목 | v0.1 구현 |
| --- | --- |
| 대화로 필요 파악, 부족한 정보 안내 | `forge-intake` skill |
| 추천 방식 / 선택 방식 | `forge-intake` (유형 설명: `reference/artifact-types.md`) |
| Skill · MCP · Plugin · Harness 자동 생성 | `forge-skill`, `forge-mcp`, `forge-plugin`, `forge-harness` + 템플릿 |
| 생성 결과 검증 | `scripts/forge_validate.py` (모든 생성 skill이 사용) |
| 문서 예시에서 convention 추출 | `learn-doc-conventions` |
| 화면 screenshot에서 디자인 양식 추출, 선두 기업 비교 | `learn-design-system` |
| 서브팀별 출발점 | `templates/teams/` (데이터·개발, 이커머스, PM·QA, POS) |
| Plugin 형태로 설치, 자연어 트리거 | `.claude-plugin/marketplace.json` + 각 skill의 description |
| Proactive 모드 | 미구현, 설계 메모만 ([PROACTIVE.md](PROACTIVE.md)) |

## 10. v0.2 품질 점검 (2026-11-05)

실제 Claude Code 세션으로 서브팀 4곳의 흐름을 처음부터 끝까지 돌리고, 별도 리뷰어의 검토를 받아 고쳤습니다.
시나리오는 [`tests/e2e`](../tests/e2e)에 있어 언제든 다시 돌릴 수 있습니다.

| 항목 | 고치기 전 | 고친 뒤 |
| --- | --- | --- |
| 만든 스킬의 첫 응답 | 질문부터 함 | 초안부터 쓰고 `[확인 필요]` 표시 |
| git | 요청 없이 커밋, 한 번은 SkillForge 저장소까지 수정·푸시 | 사람이 직접 요청할 때만 커밋·푸시, SkillForge 자체 파일은 수정 금지 |
| 데이터팀 흐름 | 생성 스킬을 건너뛰고 직접 작성 | `forge-skill`, `forge-mcp` 를 거쳐 만들고 검증 |
| 시험 시간 | 스킬 2개에 15분 넘게 시험 | 시험 1회, 수정 후 재시험 1회 |
| 검증기 | 훅·MCP가 부르는 파일이 없어도 통과 등 | 경로·userConfig·토큰·빈칸·링크까지 확인 |
| 예시 문서 | Markdown·PDF만 | Word·Excel·PowerPoint 읽기 추가 (.hwp 는 PDF로 변환 안내) |
| 훅 스크립트 | 영어 제목만 인식 | 한국어·번호 붙은 제목 인식 |

3차 실행 결과: 11개 시나리오 모두 통과 (서브팀 4곳, 유형 설명·선택, 모호한 요청, 끼어들면 안 되는 요청 4개).

아직 확인하지 못한 것:

- 다른 팀원 PC에서 GitHub로 설치 (비공개 저장소 권한)
- 실제 팀 문서·화면으로 학습 (테스트는 가상 예시로만)
- 웹 검색을 켠 상태의 선두 제품 비교 (테스트에서는 일반 지식으로 비교)
- Claude Desktop · 웹 사용자용 방법, `.hwp` 직접 읽기, Windows
