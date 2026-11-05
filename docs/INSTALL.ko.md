# SkillForge 설치·사용 안내

팀원이 처음 설치할 때 이 문서 하나만 따라 하시면 됩니다. 5분 정도 걸립니다.

## 1. 준비물

| 필요한 것 | 확인 방법 |
| --- | --- |
| Claude Code | 터미널에서 `claude --version` 이 버전 번호를 보여 주면 됩니다. 없으면 [설치 안내](https://code.claude.com/docs/en/setup)를 따라 설치합니다. |
| 이 저장소 읽기 권한 | 비공개 저장소입니다. 관리자에게 GitHub 아이디를 알려 주고 초대를 받아 수락합니다. |
| GitHub 로그인 | 터미널에서 `gh auth status` 가 로그인된 계정을 보여 주면 됩니다. 아니면 `gh auth login` 을 실행해 로그인합니다. |
| Python 3.10 이상 (MCP 서버를 만들 때만) | `python3 --version` 이 3.10 이상이면 됩니다 (Windows는 `python --version` 또는 `py -3 --version`). 스킬·플러그인만 만들 때는 필요 없습니다. |
| Python 3.8 이상 (권장) | 예시 문서 읽기와 결과물 검증에 씁니다. Mac·Linux에는 대부분 들어 있습니다. 없으면 SkillForge가 알려 드립니다. |

`gh` 가 없으면 [GitHub CLI](https://cli.github.com/)를 설치하거나, Git에 GitHub 계정이 연결되어 있으면 됩니다
(`git ls-remote https://github.com/kyeongjekim/skillforge` 가 오류 없이 끝나면 준비된 것입니다).

## 2. 설치 (한 번만)

Claude Code를 열고 아래 두 줄을 차례로 입력합니다.

```text
/plugin marketplace add kyeongjekim/skillforge
/plugin install skillforge@skillforge
```

터미널에서 하셔도 같습니다.

```bash
claude plugin marketplace add kyeongjekim/skillforge
claude plugin install skillforge@skillforge
```

설치 후 Claude Code를 한 번 껐다 켭니다. `claude plugin details skillforge` 를 실행해
`Skills (8)` 이 보이면 설치가 끝난 것입니다.

## 3. 써 보기

명령어를 외울 필요 없이, 평소처럼 말하면 됩니다.

| 이렇게 말하면 | 이렇게 진행됩니다 |
| --- | --- |
| "매주 같은 양식으로 보고서 쓰는 걸 자동화하고 싶어요" | 몇 가지를 물어본 뒤, 팀 양식대로 보고서를 쓰는 스킬을 만듭니다 |
| "우리 재고 시스템이랑 Claude를 연결하고 싶어요" | 필요한 정보(주소, 인증 방식)를 확인하고 MCP 서버 뼈대를 만듭니다 |
| "기존 POS 화면이랑 톤 맞춰서 새 화면 만들어 줘" | 화면 캡처를 보고 디자인 양식을 정리한 뒤 새 화면 시안을 만듭니다 |
| "이 스킬들 팀원들이 설치해서 쓰게 묶어 줘" | 팀원이 설치할 수 있는 플러그인으로 묶습니다 |
| "Skill이랑 MCP랑 뭐가 달라요?" | 네 가지 유형을 쉬운 말로 설명하고 골라 드립니다 |
| "저번에 만든 스킬이 자꾸 같은 걸 틀려요. 고쳐 주세요" | 그동안 고친 내용을 모아 스킬에 반영하고 다시 시험합니다 |

팁:

- **예시 파일을 주시면 결과가 훨씬 좋아집니다.** 잘 쓴 기존 문서 3~5개나 화면 캡처 3~6장을
  작업 폴더의 `examples/` 에 넣거나, 터미널에 끌어다 놓으세요. 캡처는 붙여넣기(Ctrl+V, Mac은 Cmd+V)도 됩니다.
- Word·Excel·PowerPoint·**한글(.hwp, .hwpx)** 파일은 그대로 읽습니다. 암호가 걸렸거나 배포용으로 저장한 한글 문서,
  예전 형식(.doc, .xls, .ppt)은 "다른 이름으로 저장 → PDF" 로 바꿔서 주세요. 표와 글은 읽지만 글꼴·색·배치는 읽지 못하니,
  모양이 중요한 양식은 PDF나 화면 캡처도 한 장 같이 주세요.
- **처음엔 질문을 여러 번 합니다.** 한 번에 하나씩, 보기와 함께 묻습니다. 바쁘면 "추천대로 해 주세요" 라고 하시면
  기본값을 한 번에 보여 드리고 확인만 받습니다.
- **만든 스킬은 쓸수록 좋아집니다.** 결과를 고치면서 "다음부터는 ~" 라고 하시면 기억했다가 다음부터 반영합니다.
- 고객 이름, 연락처, 대외비 숫자는 지우거나 가린 뒤 주세요.
- 만든 결과물은 작업 폴더에만 저장되고, 커밋·푸시·삭제는 요청하실 때만 합니다.

## 4. 업데이트

새 버전이 나오면 아래 두 줄로 받고, Claude Code를 다시 시작합니다.

```bash
claude plugin marketplace update skillforge
claude plugin update skillforge@skillforge
```

Claude Code 안에서는 `/plugin` 을 입력해 메뉴에서 업데이트할 수도 있습니다.

## 5. 문제가 생기면

| 증상 | 해결 |
| --- | --- |
| `marketplace add` 에서 "not found" 또는 인증 오류 | 저장소 초대를 수락했는지, `gh auth status` 로 로그인되어 있는지 확인합니다. |
| 말해도 SkillForge가 시작되지 않음 | Claude Code를 다시 시작하고, `claude plugin details skillforge` 로 설치를 확인합니다. "SkillForge로 스킬 만들어 줘" 처럼 이름을 넣어 말해도 됩니다. |
| MCP 서버 설치 중 `mcp` 패키지 오류 | `python3 --version` 이 3.10 이상인지 확인합니다. 낮으면 Python을 새로 설치해야 합니다. |
| 지우고 다시 설치하고 싶음 | `claude plugin uninstall skillforge@skillforge` 후 2번을 다시 합니다. |

## 6. Windows에서 쓰는 분

- Claude Code는 Windows에서 **Git for Windows**(Git Bash)가 있으면 그것으로 명령을 실행합니다. 먼저 설치해 두시면 가장 매끄럽습니다.
- Python은 [python.org](https://www.python.org/downloads/) 설치 파일로 설치하고, 설치 첫 화면에서 **"Add python.exe to PATH"** 를 체크합니다.
  Microsoft Store가 열리면 설정 → 앱 → 고급 앱 설정 → **앱 실행 별칭**에서 `python3.exe`, `python.exe` 를 꺼 주세요.
- SkillForge는 `python3` 이 없으면 `python` 이나 `py -3` 으로 대신 실행합니다. 자동 점검 훅도 셋 중 있는 것을 찾아 쓰고, 하나도 없으면 조용히 넘어갑니다.
- MCP 서버의 가상환경 경로는 Windows에서 `.venv\Scripts\python.exe` 입니다 (Mac·Linux는 `.venv/bin/python`).
- 한글 파일 이름과 내용은 UTF-8로 처리해서 Windows 기본 콘솔(cp949)에서도 깨지지 않게 했습니다.

> [!NOTE]
> Windows에서는 Linux에서 같은 조건(cp949 콘솔, python3 없음)을 흉내 내어 시험했습니다. 실제 Windows PC에서는 아직 돌려 보지 않았습니다.

## 7. Claude Desktop · claude.ai 웹을 쓰는 분

| 어디서 | 방법 |
| --- | --- |
| **Claude Desktop의 Code 탭** | Claude Code와 같습니다. Code 탭에서 **+ → Add plugins** 로 이 마켓플레이스를 추가하고 SkillForge를 설치합니다 (로컬·SSH 세션에서 가능, 클라우드 세션 제외). |
| **claude.ai 웹 · Desktop 채팅** | 플러그인은 설치할 수 없습니다. 대신 SkillForge가 Claude Code에서 만든 **스킬을 zip으로 올려** 쓸 수 있습니다. |

채팅에서 쓸 스킬을 만들 때는 SkillForge에 "Claude 앱에서 쓸 거예요" 라고 말씀해 주세요. 스킬을 만든 뒤 업로드용 zip도 만들어 드립니다.
이미 만든 스킬은 Claude Code에서 "이 스킬 Claude 앱에 올릴 수 있게 zip으로 만들어 줘" 라고 하시면 됩니다.

그다음 Claude 앱의 **설정 → Capabilities → Skills** 에서 zip을 올립니다. **코드 실행(Code execution)** 이 켜져 있어야 합니다.
조직(Team·Enterprise) 플랜은 관리자가 스킬 사용을 허용해야 할 수 있습니다.

> [!NOTE]
> 압축 파일 형식과 업로드 위치는 Claude 공식 문서 기준입니다. claude.ai에 실제로 올려 보는 시험은 이 환경에서 할 수 없어서 아직 하지 못했습니다.
