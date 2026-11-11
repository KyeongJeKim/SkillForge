"""The eval must not let test sessions read or write the host's memory (see sim.isolate_from_host_memory)."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "e2e"))
import sim  # noqa: E402


class IsolationTest(unittest.TestCase):
    def test_memory_settings_removed_and_auto_memory_off(self):
        env = {"PATH": "/bin", "CLAUDE_MEMORY_STORES": "x", "CLAUDE_CODE_POST_TURN_MEMORY": "1",
               "SYSTEM_REMINDER_MEMORY_CONTEXT": "y", "CLAUDE_COWORK_MEMORY_PATH_OVERRIDE": "/m"}
        removed = sim.isolate_from_host_memory(env)
        self.assertEqual(len(removed), 4)
        self.assertEqual(env, {"PATH": "/bin", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"})

    def test_import_already_isolated_this_process(self):
        self.assertFalse([k for k in os.environ if "MEMORY" in k and k != "CLAUDE_CODE_DISABLE_AUTO_MEMORY"])


class UserMcpLeakTest(unittest.TestCase):
    """forge-mcp registers with `claude mcp add -s user`; the eval must take such servers back out."""

    def _home(self, servers, extra=None):
        import json
        import tempfile
        home = Path(tempfile.mkdtemp())
        data = {"numStartups": 3, "mcpServers": servers, **(extra or {})}
        (home / ".claude.json").write_text(json.dumps(data), encoding="utf-8")
        os.chmod(home / ".claude.json", 0o600)
        return home

    def test_new_server_removed_rest_kept(self):
        import json
        home = self._home({"keep-me": {"command": "a"}, "pos-daily-sales": {"command": "b"}},
                          {"projects": {"/x": {"mcpServers": {"local": {}}}}})
        removed = sim.remove_user_mcp_servers({"keep-me"}, home)
        self.assertEqual(removed, ["pos-daily-sales"])
        data = json.loads((home / ".claude.json").read_text(encoding="utf-8"))
        self.assertEqual(list(data["mcpServers"]), ["keep-me"])
        self.assertEqual(data["numStartups"], 3)
        self.assertEqual(data["projects"], {"/x": {"mcpServers": {"local": {}}}})
        self.assertEqual((home / ".claude.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(sim.user_mcp_servers(home), {"keep-me"})

    def test_nothing_new_leaves_file_untouched(self):
        home = self._home({"keep-me": {"command": "a"}})
        before = (home / ".claude.json").read_bytes()
        self.assertEqual(sim.remove_user_mcp_servers({"keep-me"}, home), [])
        self.assertEqual((home / ".claude.json").read_bytes(), before)

    def test_missing_or_broken_file_is_harmless(self):
        import tempfile
        home = Path(tempfile.mkdtemp())
        self.assertEqual(sim.user_mcp_servers(home), set())
        self.assertEqual(sim.remove_user_mcp_servers(set(), home), [])
        (home / ".claude.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(sim.remove_user_mcp_servers(set(), home), [])


if __name__ == "__main__":
    unittest.main()


class JudgeModelPinned(unittest.TestCase):
    """Scores are compared across days, so the judge must not follow a moving alias (2026-11-11)."""

    def test_judge_is_a_versioned_model(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("run_eval", Path(__file__).resolve().parent / "e2e" / "run.py")
        run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run)
        for mode in run.MODES.values():
            self.assertRegex(mode["SF_JUDGE_MODEL"], r"^claude-[a-z]+-\d")
