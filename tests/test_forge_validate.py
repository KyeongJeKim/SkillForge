"""Tests for the SkillForge validator, templates, hook script and text extractor.

Run from the repo root:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "skillforge"
SCRIPTS = PLUGIN / "scripts"
SKILLS = PLUGIN / "skills"
SF = re.compile(r"\{\{\s*SF\s*:[^}]*\}\}")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


fv = load("forge_validate", SCRIPTS / "forge_validate.py")
hook = load("check_required_sections", SKILLS / "forge-harness" / "templates" / "check_required_sections.py")
xt = load("extract_text", SCRIPTS / "extract_text.py")


def run(kind: str, path: Path) -> "fv.Report":
    rep = fv.Report()
    fv.CHECKS[kind](path, rep)
    return rep


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def fill(text: str, **named: str) -> str:
    """Fill {{SF: key}} blanks the way a generator would: named keys first, then any text."""
    for k, v in named.items():
        text = re.sub(r"\{\{\s*SF\s*:\s*" + re.escape(k) + r"\s*\}\}", v, text)
    return SF.sub("filled", text)


GOOD_SKILL = """---
name: prd-writer
description: "Writes a PRD in the team's format. Use when someone asks to write a PRD, e.g. PRD 작성해 줘."
---

# PRD writer

1. Ask for the feature.
2. Fill the template.
"""


class TempDir(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)


class SelfCheck(unittest.TestCase):
    """The shipped plugin and marketplace must pass their own validator with no warnings."""

    def test_marketplace_and_plugin_pass(self):
        rep = run("marketplace", ROOT)
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])

    def test_cli_exit_code(self):
        out = subprocess.run([sys.executable, str(SCRIPTS / "forge_validate.py"), "plugin", str(PLUGIN)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("Validation passed", out.stdout)

    def test_every_template_uses_sf_markers(self):
        # hooks.template.json is complete as shipped; only the script it calls is configured.
        for f in SKILLS.rglob("*.template.*"):
            if f.name == "hooks.template.json":
                continue
            self.assertRegex(f.read_text(encoding="utf-8"), SF, f"{f} has no {{{{SF: ...}}}} blanks")

    def test_descriptions_are_quoted_and_have_triggers(self):
        for skill_md in SKILLS.glob("*/SKILL.md"):
            line = next(l for l in skill_md.read_text(encoding="utf-8").splitlines() if l.startswith("description:"))
            self.assertTrue(line.startswith('description: "'), skill_md)
            self.assertRegex(line.lower(), r"use (when|after)", skill_md)

    def test_generators_defer_to_intake(self):
        """Bare 'make X' phrases belong to intake; generators send vague requests back to it."""
        for name in ("forge-skill", "forge-mcp", "forge-plugin", "forge-harness"):
            desc = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8").split("\n")[2]
            self.assertIn("start forge-intake instead", desc, name)
            for phrase in ("스킬 만들어 줘", "MCP 만들어 줘", "플러그인 만들어 줘", "하네스 만들어 줘"):
                self.assertNotIn(phrase, desc, f"{name} should not claim '{phrase}'")


class SkillChecks(TempDir):
    def check(self, text: str, folder: str = "prd-writer") -> "fv.Report":
        write(self.tmp / folder / "SKILL.md", text)
        return run("skill", self.tmp / folder)

    def test_good_skill(self):
        self.assertEqual(self.check(GOOD_SKILL).errors, [])

    def test_missing_frontmatter(self):
        self.assertFalse(self.check("# no frontmatter\n").ok)

    def test_missing_description(self):
        rep = self.check("---\nname: prd-writer\n---\n\nbody\n")
        self.assertTrue(any("description is missing" in e for e in rep.errors))

    def test_bad_name(self):
        self.assertFalse(self.check(GOOD_SKILL.replace("prd-writer", "Bad_Name"), "Bad_Name").ok)

    def test_long_description(self):
        self.assertFalse(self.check(GOOD_SKILL.replace("Writes a PRD", "x" * 1100)).ok)

    def test_unfilled_placeholder(self):
        self.assertFalse(self.check(GOOD_SKILL + "\n{{SF: Step}}\n").ok)

    def test_korean_placeholder(self):
        self.assertFalse(self.check(GOOD_SKILL + "\n{{SF: 단계 설명}}\n").ok)

    def test_merge_fields_are_allowed(self):
        self.assertTrue(self.check(GOOD_SKILL + "\n안녕하세요 {{customer_name}} 고객님\n").ok)

    def test_placeholder_in_code_is_documentation(self):
        self.assertTrue(self.check(GOOD_SKILL + "\nReplace every `{{SF: ...}}` blank.\n").ok)

    def test_placeholder_in_supporting_file(self):
        write(self.tmp / "prd-writer" / "reference" / "style-guide.md", "# Guide\n{{SF: rule}}\n")
        self.assertFalse(self.check(GOOD_SKILL).ok)

    def test_broken_link(self):
        self.assertFalse(self.check(GOOD_SKILL + "\nSee [guide](reference/missing.md).\n").ok)

    def test_broken_link_with_anchor(self):
        self.assertFalse(self.check(GOOD_SKILL + "\nSee [guide](reference/missing.md#rules).\n").ok)

    def test_links_in_code_and_mailto_are_ignored(self):
        text = GOOD_SKILL + "\n```md\n[x](not/here.md)\n```\nMail [us](mailto:a@b.c) or see [top](#top).\n"
        self.assertTrue(self.check(text).ok)

    def test_quoted_phrase_then_text_fails(self):
        """Claude Code drops frontmatter whose value starts with a quote that closes early."""
        text = '---\nname: prd-writer\ndescription: "PRD 써 줘" 라고 하면 사용.\n---\n\nbody\n'
        self.assertFalse(self.check(text).ok)

    def test_list_description_fails(self):
        text = "---\nname: prd-writer\ndescription:\n  - one\n  - two\n---\n\nbody\n"
        self.assertFalse(self.check(text).ok)

    def test_unquoted_colon_is_a_warning_not_an_error(self):
        """Claude Code accepts 'says: x' in a plain description; strict YAML does not."""
        text = "---\nname: prd-writer\ndescription: Writes PRDs. Use when someone says: PRD 써 줘.\n---\n\nbody\n"
        self.assertTrue(self.check(text).ok)

    def test_korean_trigger_clause_accepted(self):
        text = '---\nname: prd-writer\ndescription: "PRD를 팀 양식으로 씁니다. PRD 써 달라고 할 때 사용합니다."\n---\n\nbody\n'
        self.assertEqual(self.check(text).warnings, [])

    def test_crlf_and_bom(self):
        self.assertTrue(self.check("﻿" + GOOD_SKILL.replace("\n", "\r\n")).ok)

    def test_flat_parser(self):
        data, problem = fv._parse_flat_yaml("name: a\ndescription: >-\n  line one\n  line two\n")
        self.assertEqual((data, problem), ({"name": "a", "description": "line one line two"}, ""))
        _, problem = fv._parse_flat_yaml('description: "a" b\n')
        self.assertTrue(problem)

    def test_skill_template_fills_to_valid(self):
        tpl = (SKILLS / "forge-skill" / "templates" / "SKILL.template.md").read_text(encoding="utf-8")
        rep = self.check(fill(tpl, **{"skill-name": "promo-plan"}), "promo-plan")
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])

    def test_unfilled_skill_template_fails(self):
        tpl = (SKILLS / "forge-skill" / "templates" / "SKILL.template.md").read_text(encoding="utf-8")
        self.assertFalse(self.check(tpl.replace("{{SF: skill-name}}", "promo-plan"), "promo-plan").ok)


class PluginChecks(TempDir):
    def setUp(self):
        super().setUp()
        self.plugin = self.tmp / "plugins" / "team-kit"
        write(self.plugin / ".claude-plugin" / "plugin.json", json.dumps(
            {"name": "team-kit", "version": "0.1.0", "description": "d", "author": {"name": "KJ"}}))
        write(self.plugin / "skills" / "prd-writer" / "SKILL.md", GOOD_SKILL)
        write(self.tmp / ".claude-plugin" / "marketplace.json", json.dumps(
            {"name": "team", "owner": {"name": "KJ"},
             "plugins": [{"name": "team-kit", "source": "./plugins/team-kit"}]}))

    def manifest(self, **extra):
        data = {"name": "team-kit", "version": "0.1.0", "description": "d", "author": {"name": "KJ"}, **extra}
        write(self.plugin / ".claude-plugin" / "plugin.json", json.dumps(data))

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

    def test_helper_folder_under_skills_is_a_warning(self):
        (self.plugin / "skills" / "shared").mkdir()
        rep = run("plugin", self.plugin)
        self.assertTrue(rep.ok)
        self.assertTrue(any("no SKILL.md" in w for w in rep.warnings))

    def _harness(self, copy_script: bool) -> None:
        tdir = SKILLS / "forge-harness" / "templates"
        shutil.copy(tdir / "hooks.template.json", write(self.plugin / "hooks" / "hooks.json", ""))
        if copy_script:
            shutil.copy(tdir / "check_required_sections.py",
                        write(self.plugin / "scripts" / "check_required_sections.py", ""))
        agent = fill((tdir / "agent.template.md").read_text(encoding="utf-8"), **{"role-name": "reviewer"})
        write(self.plugin / "agents" / "reviewer.md", agent)

    def test_harness_templates_are_valid(self):
        self._harness(copy_script=True)
        self.assertEqual(run("plugin", self.plugin).errors, [])

    def test_harness_missing_hook_script_fails(self):
        """A hooks.json pointing at a missing script would fire an error after every edit."""
        self._harness(copy_script=False)
        rep = run("plugin", self.plugin)
        self.assertTrue(any("check_required_sections.py" in e for e in rep.errors), rep.errors)

    def test_bad_hook_event(self):
        write(self.plugin / "hooks" / "hooks.json", json.dumps(
            {"hooks": {"AfterWrite": [{"hooks": [{"type": "command", "command": "true"}]}]}}))
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_shell_hook_with_user_config_fails(self):
        write(self.plugin / "hooks" / "hooks.json", json.dumps(
            {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo ${user_config.x}"}]}]}}))
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_agent_needs_description(self):
        write(self.plugin / "agents" / "x.md", "---\nname: x\n---\n\nprompt\n")
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_agent_placeholder_fails(self):
        write(self.plugin / "agents" / "x.md", "---\nname: x\ndescription: Reviews.\n---\n\nYou are {{SF: role}}.\n")
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_mcp_json(self):
        write(self.plugin / "servers" / "inv" / "server.py", "")
        write(self.plugin / ".mcp.json", json.dumps(
            {"mcpServers": {"inv": {"command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/servers/inv/server.py"]}}}))
        self.assertTrue(run("plugin", self.plugin).ok)
        write(self.plugin / ".mcp.json", json.dumps({"mcpServers": {"inv": {}}}))
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_mcp_json_missing_server_file(self):
        write(self.plugin / ".mcp.json", json.dumps(
            {"mcpServers": {"inv": {"command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/servers/inv/server.py"]}}}))
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_mcp_json_hardcoded_token_fails(self):
        write(self.plugin / ".mcp.json", json.dumps(
            {"mcpServers": {"inv": {"url": "https://x.example", "env": {"API_TOKEN": "abc123secret"}}}}))
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_user_config(self):
        good = {"tok": {"type": "string", "title": "Token", "description": "API token", "sensitive": True}}
        self.manifest(userConfig=good)
        self.assertTrue(run("plugin", self.plugin).ok)
        self.manifest(userConfig={"tok": {"type": "secret", "title": "T", "description": "d", "colour": 1}})
        self.assertFalse(run("plugin", self.plugin).ok)

    def test_plugin_templates_fill_to_valid(self):
        tdir = SKILLS / "forge-plugin" / "templates"
        write(self.plugin / ".claude-plugin" / "plugin.json",
              fill((tdir / "plugin.template.json").read_text(), **{"plugin-name": "team-kit"}))
        write(self.tmp / ".claude-plugin" / "marketplace.json",
              fill((tdir / "marketplace.template.json").read_text(),
                   **{"plugin-name": "team-kit", "marketplace-name": "team"}))
        rep = run("marketplace", self.tmp)
        self.assertEqual(rep.errors, [])


class McpChecks(TempDir):
    TPL = SKILLS / "forge-mcp" / "templates" / "python"

    def _filled(self) -> str:
        return fill((self.TPL / "server.template.py").read_text(encoding="utf-8"),
                    **{"server-name": "inventory", "ENV_PREFIX": "INVENTORY", "system": "the inventory system"})

    def _server(self, text: str) -> Path:
        d = self.tmp / "inventory"
        write(d / "server.py", text)
        shutil.copy(self.TPL / "requirements.txt", d / "requirements.txt")
        write(d / "README.md", "# inventory\n")
        return d

    def test_filled_template_passes(self):
        rep = run("mcp", self._server(self._filled()))
        self.assertEqual((rep.errors, rep.warnings), ([], []))

    def test_unfilled_template_fails(self):
        self.assertFalse(run("mcp", self._server((self.TPL / "server.template.py").read_text())).ok)

    def test_hardcoded_secrets_fail(self):
        for secret in ('\nAPI_KEY = "sk-live-abcdefghijkl"\n', '\nHEADERS = {"Authorization": "Bearer abcdefghijklmnop"}\n'):
            self.assertFalse(run("mcp", self._server(self._filled() + secret)).ok, secret)

    def test_hidden_error_message_warns(self):
        text = self._filled().replace("raise ToolError(", "raise RuntimeError(")
        rep = run("mcp", self._server(text))
        self.assertTrue(rep.ok)
        self.assertTrue(any("ToolError" in w for w in rep.warnings), rep.warnings)

    def test_no_tools_fails(self):
        self.assertFalse(run("mcp", self._server(
            "from mcp.server.mcpserver import MCPServer\nmcp = MCPServer('x')\nmcp.run()\n")).ok)

    def test_missing_run_fails(self):
        self.assertFalse(run("mcp", self._server(self._filled().replace("mcp.run()", "pass"))).ok)

    def test_syntax_error_fails(self):
        self.assertFalse(run("mcp", self._server("def broken(:\n")).ok)


class HookScript(TempDir):
    SCRIPT = SKILLS / "forge-harness" / "templates" / "check_required_sections.py"

    def _run(self, file_path: Path) -> subprocess.CompletedProcess:
        event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})
        return subprocess.run([sys.executable, str(self.SCRIPT)], input=event,
                              capture_output=True, text=True, check=False)

    def test_missing_sections_exit_2(self):
        out = self._run(write(self.tmp / "login-spec.md", "# 개요\n\ntext\n"))
        self.assertEqual(out.returncode, 2)
        self.assertIn("요구사항", out.stderr)

    def test_korean_numbered_headings_pass(self):
        f = write(self.tmp / "FS-POS-022 포인트 취소 명세.md",
                  "# 1. 개요\n## 4. 기능 상세\n## 5) 예외 처리\n")
        self.assertEqual(self._run(f).returncode, 0)

    def test_english_headings_pass(self):
        f = write(self.tmp / "login-spec.md", "# Overview\n## 2.1 Requirements\n## Exceptions (errors)\n")
        self.assertEqual(self._run(f).returncode, 0)

    def test_other_files_ignored(self):
        self.assertEqual(self._run(write(self.tmp / "notes.md", "nothing\n")).returncode, 0)

    def test_normalize(self):
        self.assertEqual(hook.normalize("Ⅱ. 개요"), "개요")
        self.assertEqual(hook.normalize("2.3 예외 처리"), "예외 처리")


class ExtractText(TempDir):
    def _zip(self, name: str, files: dict) -> Path:
        p = self.tmp / name
        with zipfile.ZipFile(p, "w") as z:
            for k, v in files.items():
                z.writestr(k, v)
        return p

    def test_docx(self):
        w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        doc = (f'<w:document {w}><w:body>'
               '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>개요</w:t></w:r></w:p>'
               '<w:p><w:r><w:t>본문입니다.</w:t></w:r></w:p>'
               '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>항목</w:t></w:r></w:p></w:tc>'
               '<w:tc><w:p><w:r><w:t>내용</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
               '</w:body></w:document>')
        out = xt.docx_text(self._zip("a.docx", {"word/document.xml": doc}))
        self.assertIn("# 개요", out)
        self.assertIn("| 항목 | 내용 |", out)

    def test_xlsx(self):
        s = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        r = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
        files = {
            "xl/workbook.xml": f'<workbook {s} {r}><sheets><sheet name="매출" sheetId="1" r:id="rId1"/></sheets></workbook>',
            "xl/_rels/workbook.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                          '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
            "xl/sharedStrings.xml": f'<sst {s}><si><t>채널</t></si></sst>',
            "xl/worksheets/sheet1.xml": f'<worksheet {s}><sheetData><row><c t="s"><v>0</v></c><c><v>42</v></c></row></sheetData></worksheet>',
        }
        out = xt.xlsx_text(self._zip("a.xlsx", files))
        self.assertIn("## Sheet: 매출", out)
        self.assertIn("| 채널 | 42 |", out)

    def test_pptx(self):
        a = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
        files = {f"ppt/slides/slide{i}.xml": f'<p:sld xmlns:p="x" {a}><a:p><a:r><a:t>슬라이드 {i}</a:t></a:r></a:p></p:sld>'
                 for i in (1, 2, 10)}
        out = xt.pptx_text(self._zip("a.pptx", files))
        self.assertLess(out.index("슬라이드 2"), out.index("슬라이드 10"))

    def test_unsupported_format(self):
        p = write(self.tmp / "a.hwp", "x")
        out = subprocess.run([sys.executable, str(SCRIPTS / "extract_text.py"), str(p)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(out.returncode, 1)
        self.assertIn("PDF", out.stdout)


if __name__ == "__main__":
    unittest.main()
