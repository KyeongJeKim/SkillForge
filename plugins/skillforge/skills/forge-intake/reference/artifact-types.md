# The four artifact types (네 가지 유형)

Use this when the person wants to understand the options before choosing. Explain in their
language, in a few lines, with an example from their own work. The Korean analogies below help.

## Skill (스킬)

A folder with a `SKILL.md` file (instructions) and optional scripts or reference files. Claude reads
each skill's description and loads the skill automatically when a request matches it, so nobody has
to type a command.

- 비유: 팀의 **업무 매뉴얼**. Claude가 필요할 때 알아서 꺼내 읽습니다.
- Good for: a procedure, a document format, a checklist, a writing style.
- Example: "우리 팀 PRD 양식대로 써 줘", "상품 상세페이지를 우리 톤으로 써 줘"
- Lives in: `~/.claude/skills/<name>/` (personal), `.claude/skills/<name>/` (project) or a plugin's `skills/`.

## MCP server (MCP, Model Context Protocol)

A small program that connects Claude to an external system and exposes **tools** Claude can call,
such as "look up an order" or "query a table".

- 비유: 회사 시스템과 Claude를 잇는 **연결 케이블**.
- Good for: live data or actions in a database, an API or an internal tool.
- Example: "이 상품 오늘 재고 몇 개야?", "어제 POS 매출 뽑아 줘"
- Lives in: a script or service, registered with `claude mcp add` or a plugin's `.mcp.json`.
  Needs Python 3.10+ for the SkillForge template.

## Plugin (플러그인)

An installable package that bundles skills, subagents, hooks and MCP servers. A team installs it
once from a marketplace (a Git repo) and gets everything together, and updates in one place.

- 비유: 여러 도구를 담은 **설치용 공구 상자**.
- Good for: sharing several pieces with a team.
- Example: "이커머스팀 전원에게 상품등록·프로모션·고객문의 스킬을 한 번에 깔아 주기"
- Lives in: a folder with `.claude-plugin/plugin.json`, listed in a `marketplace.json`.

## Harness (하네스)

The working setup around the model for a bigger job: which subagents do which step, which checks
run automatically (hooks), and where a person must approve. Designing this is harness engineering.

- 비유: 역할과 검수 단계가 정해진 **작업 라인**.
- Good for: multi-step workflows that need roles, quality gates or approval points.
- Example: "기능명세서 초안 작성 → 검토 담당이 양식 확인 → 필수 항목 빠지면 경고 → 담당자 승인"
- Lives in: subagents (`agents/*.md`), hooks (`hooks/hooks.json`) and an orchestrating skill, shipped as a plugin.

## One-line summary (한 줄 요약)

Skill = Claude가 아는 방법. MCP = Claude가 연결되는 곳.
Plugin = 그걸 묶어 나눠 주는 패키지. Harness = 그걸 여러 단계로 엮어 돌리는 업무 흐름.
