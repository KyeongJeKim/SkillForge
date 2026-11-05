---
name: forge-plugin
description: "Packages skills, subagents, hooks and MCP servers into an installable Claude Code plugin with a marketplace.json so a team installs it from a Git repo, tests it locally and validates it. Use after forge-intake has a confirmed spec of type plugin, or when existing SkillForge results should be shared with teammates, e.g. 이 스킬들 팀원들이 설치해서 쓰게 묶어 줘, package these for my team. If the need is still vague, start forge-intake instead."
---

# Forge a Plugin

## Inputs

A confirmed `forge-spec.md` with type plugin (or a harness spec from `skillforge:forge-harness`,
which counts as this spec). Components that don't exist yet are built first with
`skillforge:forge-skill` or `skillforge:forge-mcp`.

## Layout

A marketplace repo that holds one or more plugins:

```text
<repo>/
├── .claude-plugin/
│   └── marketplace.json        # lists the plugins in this repo
├── README.md                   # install steps for teammates
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json     # only plugin.json (and an optional icon.png) goes in here
        ├── skills/<skill>/SKILL.md
        ├── agents/<agent>.md   # optional
        ├── hooks/hooks.json    # optional, scripts in scripts/
        └── .mcp.json           # optional, servers in servers/
```

Templates: [templates/plugin.template.json](templates/plugin.template.json) and
[templates/marketplace.template.json](templates/marketplace.template.json).

## Steps

1. **Name:** kebab-case. It must not start with `claude-`, `anthropic-`, `anthropics-` or
   `cc-plugin-`, and must not be `claude`, `anthropic`, `claude-code` or `claude-mods`. Use the
   same name in `plugin.json` and the marketplace entry.
2. **plugin.json** from the template: `name`, `version` (`0.1.0`), `description`, `author.name`.
   Add `homepage` only if it is a real URL.
3. **Components** at the plugin root, never inside `.claude-plugin/`. Move or copy skills from
   `.claude/skills/` into `skills/`; if you copy, say which copy is the one to edit from now on.
   Prefer `skills/` over `commands/`. A plugin-root `CLAUDE.md` is not loaded; put instructions in a skill.
4. **Paths:** hooks, MCP config and skill bodies use `${CLAUDE_PLUGIN_ROOT}`. State goes in
   `${CLAUDE_PLUGIN_DATA}`, never in the plugin folder (it is replaced on update).
5. **Secrets:** anything a teammate must provide (tokens, URLs) goes in `userConfig` with
   `"sensitive": true` for secrets; Claude Code asks for it when the plugin is enabled. Reference it as
   `${user_config.<key>}` in `.mcp.json` env or in exec-form hook `args`.
6. **marketplace.json** at the repo root: `name`, `owner.name`, `description`, and one entry per
   plugin with `source` `./plugins/<plugin-name>`.
7. **Validate** both levels and fix until clean:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_validate.py" marketplace <repo>
   claude plugin validate <repo>                       # if the claude CLI is available
   claude plugin validate <repo>/plugins/<plugin-name>
   ```

8. **Test locally** before sharing: `claude plugin marketplace add <repo>` then
   `claude plugin install <plugin-name>@<marketplace-name>` and `claude plugin details <plugin-name>`
   to see that every skill, agent, hook and server loads. Remove the test install afterwards if the
   person doesn't want it (`claude plugin uninstall <plugin-name>@<marketplace-name>`).
9. **README.md** at the repo root, in the team's language: what the plugin does, the two install lines,
   what teammates need (repo read access and Git sign-in for a private repo; Python 3.10+ if there
   is an MCP server), and how to update.

   ```text
   /plugin marketplace add <owner>/<repo>
   /plugin install <plugin-name>@<marketplace-name>
   ```

10. **Sharing:** creating a GitHub repo, committing and pushing reach other people, so offer them in
    one line and do them only after the person says yes.
11. **Git:** run `git commit`, `git push` or create a repository only when the person's own words ask for it ("확인까지 해 주세요" or "마무리해 주세요" is not that). Never edit, commit or push SkillForge's own files (this plugin's folder or the SkillForge repository); if SkillForge itself has a problem, say so in the hand-over.

## Hand-over (in the person's language, short)

What is in the plugin, that it passed validation and a local install, the two install lines, and
what's left for them (e.g. "GitHub 저장소를 만들어 올릴까요?").
