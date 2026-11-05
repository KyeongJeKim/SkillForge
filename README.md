<p align="center">
  <img src="assets/banner.svg" alt="SkillForge: 말로 설명하면 Claude 스킬과 도구를 만들어 드립니다" width="100%">
</p>

<p align="center">
  <b>필요한 걸 평소 말로 설명하면</b>, SkillForge가 무엇을 만들지 정하고, 빠진 정보를 묻고,<br>
  Claude <b>Skill · MCP 서버 · Plugin · Harness</b> 로 만들어 검증까지 마칩니다.<br>
  <sub>Describe what you need in plain words. SkillForge picks the right artifact, asks for what's missing, builds it and validates it.</sub>
</p>

<p align="center">
  <a href="#-시작하기">시작하기</a> ·
  <a href="#-이렇게-말하면-됩니다">사용 예시</a> ·
  <a href="#-무엇을-만들어-주나요">네 가지 유형</a> ·
  <a href="#-팀별-예시">팀별 예시</a> ·
  <a href="#-개발">개발</a>
</p>

---

## 🔨 어떻게 동작하나요

<p align="center">
  <img src="assets/flow.svg" alt="동작 흐름: 말하기, 인터뷰(forge-intake), 유형 정하기(forge-spec.md), 만들기(forge-skill, forge-mcp, forge-plugin, forge-harness), 검증·전달(forge_validate.py). 팀 문서·화면 예시가 있으면 learn-doc-conventions, learn-design-system 으로 먼저 양식을 배웁니다." width="100%">
</p>

- **슬래시 명령어가 없습니다.** "이런 거 만들어야 될 것 같아", "매번 똑같은 거 반복해" 처럼 말하면 알아서 시작합니다.
- **질문은 최소한으로.** 한 번에 세 개 이하만 묻고, "추천대로 해 주세요" 라고 하면 기본값으로 진행합니다.
- **먼저 초안, 나중에 확인.** 만든 스킬은 정보가 조금 모자라도 초안부터 쓰고, 확인할 곳을 `[확인 필요]` 로 표시합니다.
- **한 번만 하는 일에는 끼어들지 않습니다.** "PRD 한 개만 써 줘", "이 엑셀 수식 왜 에러 나요?" 같은 요청은 평소처럼 처리합니다.

## 🧰 무엇을 만들어 주나요

<p align="center">
  <img src="assets/types.svg" alt="Skill은 업무 매뉴얼, MCP server는 연결 케이블, Plugin은 공구 상자, Harness는 작업 라인" width="100%">
</p>

어떤 걸 만들어야 할지 몰라도 괜찮습니다. SkillForge가 추천하거나, 네 가지를 설명하고 직접 고르게 해 드립니다.

## 👥 팀별 예시

<p align="center">
  <img src="assets/teams.svg" alt="데이터 분석·개발, 이커머스 운영, PM·QA, POS 기획·디자인 팀별로 만들 수 있는 것" width="100%">
</p>

팀마다 시작용 템플릿이 들어 있습니다: [데이터·개발](plugins/skillforge/templates/teams/data-dev.md) ·
[이커머스 운영](plugins/skillforge/templates/teams/ecommerce-ops.md) ·
[PM·QA](plugins/skillforge/templates/teams/pm-qa.md) ·
[POS 기획·디자인](plugins/skillforge/templates/teams/pos-product.md)

## 🚀 시작하기

<p align="center">
  <img src="assets/start.svg" alt="1. Claude Code에서 /plugin marketplace add kyeongjekim/skillforge, /plugin install skillforge@skillforge 로 설치. 2. 명령어 없이 말로 시작." width="100%">
</p>

Claude Code에서 아래 두 줄을 입력합니다.

```text
/plugin marketplace add kyeongjekim/skillforge
/plugin install skillforge@skillforge
```

> [!NOTE]
> 비공개 저장소라서 팀원마다 **저장소 읽기 권한**과 **GitHub 로그인**(`gh auth login`)이 필요합니다.
> MCP 서버를 만들 때만 **Python 3.10 이상**이 필요합니다.
> 준비물, 업데이트, 문제 해결은 [설치 안내 (docs/INSTALL.ko.md)](docs/INSTALL.ko.md)에 있습니다.

## 💬 이렇게 말하면 됩니다

| 이렇게 말하면 | 시작되는 것 | 결과 |
| --- | --- | --- |
| "매달 프로모션 기획서 쓰는 게 오래 걸려요. 우리 양식대로 써 주는 걸 만들고 싶어요" | `forge-intake` → `learn-doc-conventions` → `forge-skill` | 기획서 스킬 |
| "우리 재고 시스템이랑 Claude를 연결하고 싶어요" | `forge-intake` → `forge-mcp` | 읽기 전용 MCP 서버 뼈대 |
| "기존 POS 화면이랑 톤 맞춰서 새 화면 만들어 줘" | `learn-design-system` | 디자인 양식 + 화면 명세 + HTML 시안 |
| "이 스킬들 팀원들이 설치해서 쓰게 묶어 줘" | `forge-plugin` | 팀 설치용 플러그인 |
| "명세서 쓰고 리뷰어가 검토하는 흐름 만들어 줘" | `forge-harness` | 작성·검토 에이전트 + 자동 점검 훅 |
| "Skill이랑 MCP랑 뭐가 달라요?" | `forge-intake` | 네 가지 유형 설명과 추천 |

## ✅ 품질 확인

만드는 모든 결과물은 넘겨 드리기 전에 검증합니다.

- **검증기** `forge_validate.py`: 스킬 설명과 자동 실행 문구, 빈칸 남김, 깨진 링크, 훅·MCP가 부르는 파일이 실제로 있는지,
  하드코딩된 토큰, 팀원 설정(userConfig)까지 확인합니다. Claude Code 공식 검증(`claude plugin validate`)도 함께 돌립니다.
- **단위 테스트 58개**: 검증기, 템플릿, 훅 스크립트, Office 문서 읽기를 확인합니다. 표준 라이브러리만 씁니다.
- **시나리오 테스트** [`tests/e2e`](tests/e2e): 서브팀 4곳의 실제 대화 흐름과, 끼어들면 안 되는 요청을 Claude로 직접 돌려 봅니다.

## 🗂 구성

```text
skillforge/
├── .claude-plugin/marketplace.json     # 이 저장소를 설치 가능한 마켓플레이스로 만듭니다
├── assets/                             # README 이미지 (SVG)
├── docs/
│   ├── INSTALL.ko.md                   # 팀원용 설치·사용 안내
│   ├── PLAN.md                         # 계획과 남은 질문
│   └── PROACTIVE.md                    # 먼저 제안하는 모드 설계 메모 (미구현)
├── plugins/skillforge/
│   ├── .claude-plugin/plugin.json
│   ├── skills/
│   │   ├── forge-intake/               # 인터뷰, 빠진 정보, 유형 추천·설명
│   │   ├── forge-skill/                # Skill 생성 + SKILL.template.md
│   │   ├── forge-mcp/                  # MCP 서버 생성 + Python 템플릿 (MCP SDK 2.x)
│   │   ├── forge-plugin/               # Plugin 생성 + plugin/marketplace 템플릿
│   │   ├── forge-harness/              # Harness 생성 + 에이전트·훅 템플릿, 필수 섹션 점검 스크립트
│   │   ├── learn-doc-conventions/      # 예시 문서에서 팀 양식(style-guide.md) 추출
│   │   └── learn-design-system/        # 화면 캡처에서 디자인 양식 추출, 새 화면 시안
│   ├── templates/teams/                # 서브팀별 시작 템플릿
│   └── scripts/
│       ├── forge_validate.py           # 모든 생성 단계가 쓰는 검증기
│       └── extract_text.py             # .docx / .xlsx / .pptx 텍스트 추출
└── tests/
    ├── test_forge_validate.py          # 단위 테스트
    └── e2e/                            # 시나리오 테스트 (선택, Claude 사용량 발생)
```

템플릿 파일은 `*.template.*` 이름을 쓰고, 채워야 할 곳은 `{{SF: ...}}` 로 표시합니다.
`{{customer_name}}` 같은 일반 치환 필드는 그대로 둘 수 있습니다.

## 🛠 개발

```bash
# 단위 테스트 (Python 3.9+, 표준 라이브러리만)
python3 -m unittest discover -s tests -v

# 플러그인과 마켓플레이스 검증
python3 plugins/skillforge/scripts/forge_validate.py marketplace .
claude plugin validate .

# SkillForge가 만든 결과물 검증
python3 plugins/skillforge/scripts/forge_validate.py skill  path/to/skill-dir
python3 plugins/skillforge/scripts/forge_validate.py plugin path/to/plugin-dir
python3 plugins/skillforge/scripts/forge_validate.py mcp    path/to/server-dir

# 시나리오 테스트 (claude CLI 필요, 사용량 발생)
tests/e2e/run.sh
```

새 버전을 낼 때는 `plugin.json` 과 `marketplace.json` 의 `version` 을 함께 올립니다
(테스트가 두 값이 같은지 확인합니다).

## 🧭 앞으로

[docs/PLAN.md](docs/PLAN.md)에 목표와 남은 질문이 있습니다. 아직 없는 것:

- **먼저 제안하는 모드:** 일하는 패턴을 보고 도구를 먼저 제안합니다. 설계 메모만 있습니다 ([docs/PROACTIVE.md](docs/PROACTIVE.md)).
- **Claude Desktop · 웹 지원:** 지금은 Claude Code 플러그인입니다.

---

<p align="center"><sub>Made by <a href="https://github.com/kyeongjekim">@kyeongjekim</a></sub></p>
