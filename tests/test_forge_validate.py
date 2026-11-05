"""Tests for plugins/skillforge/scripts/forge_validate.py.

Run from the repo root:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "skillforge"
SCRIPT = PLUGIN / "scripts" / "forge_validate.py"
SKILLS = PLUGIN / "skills"

spec = importlib.util.spec_from_file_location("forge_validate", SCRIPT)
fv = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fv)


def run(kind: str, path: Path) -> "fv.Report":
    rep = fv.Report()
    fv.CHECKS[kind](path, rep)
    return rep


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


GOOD_SKILL = """---
name: prd-writer
description: Writes a PRD in the team's format. Use when someone asks to write a PRD or "PRD 작성해 줘".
---

# PRD writer

1. Ask for the feature.
2. Fill the template.
"""


class SelfCheck(unittest.TestCase):
    """The shipped plugin and marketplace must pass their own validator."""

    def test_marketplace_and_plugin_pass(self):
        rep = run("marketplace", ROOT)
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])

    def test_cli_exit_code(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), "plugin", str(PLUGIN)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("Validation passed", out.stdout)


class SkillChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_good_skill(self):
        write(self.tmp / "prd-writer" / "SKILL.md", GOOD_SKILL)
        self.assertTrue(run("skill", self.tmp / "prd-writer").ok)

    def test_missing_frontmatter(self):
        write(self.tmp / "s" / "SKILL.md", "# no frontmatter\n")
        self.assertFalse(run("skill", self.tmp / "s").ok)

    def test_missing_description(self):
        write(self.tmp / "s" / "SKILL.md", "---\nname: s\n---\n\nbody\n")
        rep = run("skill", self.tmp / "s")
        self.assertTrue(any("description is missing" in e for e in rep.errors))

    def test_bad_name(self):
        write(self.tmp / "Bad_Name" / "SKILL.md", GOOD_SKILL.replace("prd-writer", "Bad_Name"))
        self.assertFalse(run("skill", self.tmp / "Bad_Name").ok)

    def test_long_description(self):
        text = GOOD_SKILL.replace("Writes a PRD", "x" * 1100)
        write(self.tmp / "prd-writer" / "SKILL.md", text)
        self.assertFalse(run("skill", self.tmp / "prd-writer").ok)

    def test_unfilled_placeholder(self):
        write(self.tmp / "prd-writer" / "SKILL.md", GOOD_SKILL + "\n{{Step}}\n")
        self.assertFalse(run("skill", self.tmp / "prd-writer").ok)

    def test_broken_link(self):
        write(self.tmp / "prd-writer" / "SKILL.md", GOOD_SKILL + "\nSee [guide](reference/missing.md).\n")
        self.assertFalse(run("skill", self.tmp / "prd-writer").ok)

    def test_flat_yaml_parser_block_scalar(self):
        data = fv._parse_flat_yaml("name: a\ndescription: >-\n  line one\n  line two\n")
        self.assertEqual(data, {"name": "a", "description": "line one line two"})

    def test_skill_template_fills_to_valid(self):
        """Filling every placeholder of the shipped template yields a valid skill."""
        import re

        tpl = (SKILLS / "forge-skill" / "templates" / "SKILL.template.md").read_text(encoding="utf-8")
        filled = tpl.replace("{{skill-name}}", "promo-plan")
        filled = re.sub(r"\{\{[^}]+\}\}", "filled", filled)
        write(self.tmp / "promo-plan" / "SKILL.md", filled)
        rep = run("skill", self.tmp / "promo-plan")
        self.assertEqual(rep.errors, [])


class PluginChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.plugin = self.tmp / "plugins" / "team-kit"
        write(self.plugin / ".claude-plugin" / "plugin.json", json.dumps(
            {"name": "team-kit", "version": "0.1.0", "description": "d", "author": {"name": "KJ"}}))
        write(self.plugin / "skills" / "prd-writer" / "SKILL.md", GOOD_SKILL)
        write(self.tmp / ".claude-plugin" / "marketplace.json", json.dumps(
            {"name": "team", "owner": {"name": "KJ"},
             "plugins": [{"name": "team-kit", "source": "./plugins/team-kit"}]}))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_good_plugin_and_marketplace(self):
        self.assertTrue(run("plugin", self.plugin).ok)
        self.assertTrue(run("marketplace", self.tmp).ok)

    def test_reserved_name(self):
        write(self.plugin / ".claude-plugin" / "plugin.json", json.dumps({"name": "claude-tools"}))
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_name_mismatch(self):
        mp = self.tmp / ".claude-plugin" / "marketplace.json"
        data = json.loads(mp.read_text())
        data["plugins"][0]["name"] = "other"
        mp.write_text(json.dumps(data))
        self.assertFalse(run("marketplace", self.tmp).ok)

    def test_parent_path_source(self):
        mp = self.tmp / ".claude-plugin" / "marketplace.json"
        data = json.loads(mp.read_text())
        data["plugins"][0]["source"] = "../elsewhere"
        mp.write_text(json.dumps(data))
        self.assertFalse(run("marketplace", self.tmp).ok)

    def test_component_inside_manifest_dir(self):
        write(self.plugin / ".claude-plugin" / "hooks.json", "{}")
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_harness_templates_are_valid(self):
        """The harness templates, filled in, form a valid plugin."""
        import re

        tdir = SKILLS / "forge-harness" / "templates"
        shutil.copy(tdir / "hooks.json", write(self.plugin / "hooks" / "hooks.json", ""))
        agent = re.sub(r"\{\{[^}]+\}\}", "reviewer",
                       (tdir / "agent.template.md").read_text(encoding="utf-8"))
        write(self.plugin / "agents" / "reviewer.md", agent)
        rep = run("plugin", self.plugin)
        self.assertEqual(rep.errors, [])

    def test_bad_hook_event(self):
        write(self.plugin / "hooks" / "hooks.json", json.dumps(
            {"hooks": {"AfterWrite": [{"hooks": [{"type": "command", "command": "true"}]}]}}))
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_agent_needs_description(self):
        write(self.plugin / "agents" / "x.md", "---\nname: x\n---\n\nprompt\n")
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_mcp_json(self):
        write(self.plugin / ".mcp.json", json.dumps(
            {"mcpServers": {"inv": {"command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/s.py"]}}}))
        self.assertTrue(run("plugin", self.plugin).ok)
        write(self.plugin / ".mcp.json", json.dumps({"mcpServers": {"inv": {}}}))
        self.assertFalse(run("plugin", self.plugin).ok)


class McpChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _filled_template(self) -> str:
        tpl = (SKILLS / "forge-mcp" / "templates" / "python" / "server.py").read_text(encoding="utf-8")
        return (tpl.replace("{{server-name}}", "inventory")
                   .replace("{{SYSTEM}}", "INVENTORY")
                   .replace("{{system}}", "the inventory system"))

    def test_filled_template_passes(self):
        write(self.tmp / "inventory" / "server.py", self._filled_template())
        write(self.tmp / "inventory" / "README.md", "# inventory\n")
        rep = run("mcp", self.tmp / "inventory")
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])

    def test_unfilled_template_fails(self):
        shutil.copy(SKILLS / "forge-mcp" / "templates" / "python" / "server.py",
                    write(self.tmp / "s" / "server.py", ""))
        self.assertFalse(run("mcp", self.tmp / "s").ok)

    def test_hardcoded_secret_fails(self):
        text = self._filled_template() + '\nAPI_KEY = "sk-live-abcdefghijkl"\n'
        write(self.tmp / "s" / "server.py", text)
        self.assertFalse(run("mcp", self.tmp / "s").ok)

    def test_no_tools_fails(self):
        write(self.tmp / "s" / "server.py",
              "from mcp.server.mcpserver import MCPServer\nmcp = MCPServer('x')\n")
        self.assertFalse(run("mcp", self.tmp / "s").ok)

    def test_syntax_error_fails(self):
        write(self.tmp / "s" / "server.py", "def broken(:\n")
        self.assertFalse(run("mcp", self.tmp / "s").ok)


class HookScript(unittest.TestCase):
    """The harness hook template warns on missing sections and stays quiet otherwise."""

    SCRIPT = SKILLS / "forge-harness" / "templates" / "check_required_sections.py"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _run(self, file_path: Path) -> subprocess.CompletedProcess:
        event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})
        return subprocess.run([sys.executable, str(self.SCRIPT)], input=event,
                              capture_output=True, text=True, check=False)

    def test_missing_sections_exit_2(self):
        f = write(self.tmp / "login-spec.md", "# Overview\n\ntext\n")
        out = self._run(f)
        self.assertEqual(out.returncode, 2)
        self.assertIn("Requirements", out.stderr)

    def test_complete_spec_exit_0(self):
        f = write(self.tmp / "login-spec.md",
                  "# Overview\n## Requirements\n## Acceptance criteria\n")
        self.assertEqual(self._run(f).returncode, 0)

    def test_other_files_ignored(self):
        f = write(self.tmp / "notes.md", "nothing\n")
        self.assertEqual(self._run(f).returncode, 0)


if __name__ == "__main__":
    unittest.main()
