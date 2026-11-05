---
name: forge-plugin
description: Generates an installable Claude Code plugin skeleton (plugin.json, skills, optional agents, hooks and MCP servers) plus a marketplace.json so a team can install it from a Git repo, validated before handing over. Use when a confirmed SkillForge spec has type plugin, or someone asks to package things for their team, e.g. "package these for my team", "make a plugin", "플러그인 만들어 줘", "팀원들이 설치해서 쓰게 해 줘".
---

# Forge a Plugin

## Inputs

A confirmed `forge-spec.md` with `Type: plugin`, listing the components, the plugin name and
how it will be distributed. Components that don't exist yet are built first with
`forge-skill`, `forge-mcp` or `forge-harness`.

## Layout

Use this layout (a marketplace repo that holds one or more plugins):

```text
<repo>/
├── .claude-plugin/
│   └── marketplace.json        # lists the plugins in this repo
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json     # only plugin.json goes in here
        ├── skills/<skill>/SKILL.md
        ├── agents/<agent>.md   # optional
        ├── hooks/hooks.json    # optional
        └── .mcp.json           # optional
```

Templates: [templates/plugin.json](templates/plugin.json) and
[templates/marketplace.json](templates/marketplace.json).

## Steps

1. **Name:** kebab-case, no spaces. It must not start with `claude-`, `anthropic-`,
   `anthropics-` or `cc-plugin-`, and must not be `claude`, `anthropic`, `claude-code` or
   `claude-mods`. Use the same name in `plugin.json` and the marketplace entry.
2. **Write `plugin.json`** from the template: `name`, `version` (start at `0.1.0`),
   `description`, `author.name`. Add `homepage` only if it is a real URL.
3. **Add components** at the plugin root (never inside `.claude-plugin/`). Prefer `skills/`
   over `commands/` so things trigger from natural language. Put instructions in a skill;
   a `CLAUDE.md` at the plugin root is not loaded.
4. **Paths inside the plugin** use `${CLAUDE_PLUGIN_ROOT}` in hooks, MCP config and skill
   bodies. Don't store state there (it changes on update); use `${CLAUDE_PLUGIN_DATA}`.
5. **Write `marketplace.json`** at the repo root with `name`, `owner.name` and one entry per
   plugin whose `source` is `./plugins/<plugin-name>`.
6. **Validate** both levels:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" plugin <repo>/plugins/<plugin-name>
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" marketplace <repo>
   claude plugin validate <repo>/plugins/<plugin-name>   # if the claude CLI is available
   claude plugin validate <repo>
   ```

   Fix every error and re-run.
7. **Write install steps** in the repo README:

   ```text
   /plugin marketplace add <owner>/<repo>
   /plugin install <plugin-name>@<marketplace-name>
   ```

   For a private repo, each teammate needs read access to it and Git credentials on their
   machine (for example, signed in with `gh auth login`).

## Hand-over

Tell the person: the components included, the two install commands, the validation results,
and how to release an update (bump `version`, push).
