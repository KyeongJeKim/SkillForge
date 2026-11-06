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


if __name__ == "__main__":
    unittest.main()
