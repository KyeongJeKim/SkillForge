<div align="center">

# ⚒️ SkillForge

**Build Claude Skills and Tools with Natural Language**

Describe what you need in plain words. SkillForge works out what to build,
asks for what's missing, and forges it into a Skill, MCP server, Plugin or Harness.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Status](https://img.shields.io/badge/status-early%20development-orange)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-8A63D2)

</div>

---

## Overview

Writing a Claude Skill, MCP server, Plugin or Harness by hand means knowing which one you
need and getting the structure right. SkillForge turns that into a conversation.
It is a Claude Code plugin: once installed, you just say what you need
(*"I think I need to build X"*, *"이런 거 만들어야 될 것 같아"*) and its skills start on
their own. No slash commands to remember.

## Features

- **Natural-language start:** skills trigger from what you say, in Korean or English.
- **Intake interview:** finds out what you need and lists exactly what's still missing.
- **Recommend or explain:** recommends a type, or explains all four and lets you choose.
- **Four generators:** Skill, MCP server (Python), Plugin and Harness, each validated before hand-over.
- **Learns your team's format:** extracts conventions from existing documents (PRDs, function specs) and design formats from screenshots of existing screens.
- **Benchmarks new screens:** new pages stay within your design format while matching or improving on market leaders.
- **Team starter templates:** data/dev, e-commerce operations, PM/QA and POS product teams.

## How it works

```text
"I need something for X"
        │
        ▼
  forge-intake ──► asks what's missing ──► recommends or explains the type
        │                                     (optional) learn-doc-conventions
        │                                     (optional) learn-design-system
        ▼
   forge-spec.md (you confirm)
        │
        ├──► forge-skill    → SKILL.md folder
        ├──► forge-mcp      → MCP server skeleton
        ├──► forge-plugin   → installable plugin + marketplace
        └──► forge-harness  → subagents + hooks + orchestrating skill
        │
        ▼
   forge_validate.py ──► hand-over
```

| Type | Use it for |
| --- | --- |
| **Skill** | A procedure, document format or style Claude should follow |
| **MCP server** | Live data or actions in an external system (API, database, internal tool) |
| **Plugin** | Shipping several pieces to a team as one install |
| **Harness** | Multi-step workflows with roles, automatic checks and approval points |

## Install

Requires [Claude Code](https://code.claude.com/docs/en/plugins).
In a Claude Code session:

```text
/plugin marketplace add kyeongjekim/skillforge
/plugin install skillforge@skillforge
```

Or from a terminal:

```bash
claude plugin marketplace add kyeongjekim/skillforge
claude plugin install skillforge@skillforge
```

> This repository is private. Each teammate needs read access to it and Git credentials
> on their machine (for example, `gh auth login`) before adding the marketplace.

To update later: `claude plugin marketplace update skillforge`, then reinstall or restart.

## Usage

Just talk to Claude:

| You say | What starts |
| --- | --- |
| "우리 팀 PRD 양식대로 쓰는 걸 자동화하고 싶어요" | `forge-intake`, then `learn-doc-conventions` and `forge-skill` |
| "Connect Claude to our inventory system" | `forge-intake`, then `forge-mcp` |
| "기존 POS 화면이랑 톤 맞춰서 새 화면 기획해 줘" | `learn-design-system` |
| "Package these skills so the team can install them" | `forge-plugin` |
| "스펙 작성하고 리뷰어가 검토하는 흐름 만들어 줘" | `forge-harness` |
| "Skill이랑 MCP랑 뭐가 달라요?" | `forge-intake` explains the four types |

## Project structure

```text
skillforge/
├── .claude-plugin/
│   └── marketplace.json            # makes this repo installable as a marketplace
├── plugins/skillforge/
│   ├── .claude-plugin/plugin.json  # plugin manifest
│   ├── skills/
│   │   ├── forge-intake/           # interview, missing items, type choice
│   │   ├── forge-skill/            # Skill generator + template
│   │   ├── forge-mcp/              # MCP server generator + Python template
│   │   ├── forge-plugin/           # Plugin generator + templates
│   │   ├── forge-harness/          # Harness generator + agent/hook templates
│   │   ├── learn-doc-conventions/  # style guide from example documents
│   │   └── learn-design-system/    # design format from screenshots
│   ├── templates/teams/            # starter templates per subteam
│   └── scripts/forge_validate.py   # validator used by every generator
├── tests/                          # unit tests for the validator and templates
└── docs/
    ├── PLAN.md                     # plan (Korean)
    └── PROACTIVE.md                # proactive mode design note (open question)
```

## Development

```bash
# Run the tests (Python 3.9+, standard library only)
python3 -m unittest discover -s tests -v

# Validate the plugin and marketplace
python3 plugins/skillforge/scripts/forge_validate.py marketplace .
claude plugin validate .

# Validate something SkillForge generated
python3 plugins/skillforge/scripts/forge_validate.py skill  path/to/skill-dir
python3 plugins/skillforge/scripts/forge_validate.py plugin path/to/plugin-dir
python3 plugins/skillforge/scripts/forge_validate.py mcp    path/to/server-dir
```

## Roadmap

See [docs/PLAN.md](docs/PLAN.md) for goals and open questions. Not in v0.1:

- **Proactive mode:** suggesting tools by watching work patterns. Design note only, see [docs/PROACTIVE.md](docs/PROACTIVE.md).
- Environments other than Claude.

---

<div align="center">
<sub>Made by <a href="https://github.com/kyeongjekim">@kyeongjekim</a></sub>
</div>
