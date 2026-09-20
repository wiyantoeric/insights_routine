"""Exercise the cron runner without network calls or real agent CLIs."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
RUN_SCRIPT = SCRIPTS / "run.sh"


class RunScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("scripts", "prompts", "state", "bin"):
            (self.root / directory).mkdir()

        shutil.copy2(RUN_SCRIPT, self.root / "scripts" / "run.sh")
        shutil.copy2(SCRIPTS / "codex_progress.py", self.root / "scripts" / "codex_progress.py")
        (self.root / "config.json").write_text(json.dumps({
            "agent": {
                "inference": "codex",
                "codex_model": "gpt-6-astra",
                "codex_reasoning_effort": "low",
                "prompt_file": "prompts/daily_scan.md",
                "claude_allowed_tools": ["Read", "Write", "WebFetch"],
            },
            "paths": {"vault_dir": "vaults"},
            "web": {"build_on_run": False},
        }))
        (self.root / "prompts" / "daily_scan.md").write_text("Test prompt\n")
        (self.root / "scripts" / "fetch.py").write_text(
            "import os\nfrom pathlib import Path\n"
            "Path('state/fetched').write_text('yes')\n"
            "Path('state/fetch_keys').write_text(os.getenv('CODEX_API_KEY', '') + ':' + os.getenv('ANTHROPIC_API_KEY', ''))\n"
        )
        (self.root / "scripts" / "notify.py").write_text(
            "from pathlib import Path\nPath('state/notified').write_text('yes')\n"
        )
        self.write_stub("codex", """#!/bin/sh
printf '%s\n' "$@" > "$TEST_ARGS"
printf '%s:%s\n' "${CODEX_API_KEY:-}" "${ANTHROPIC_API_KEY:-}" > "$TEST_KEYS"
cat > "$TEST_STDIN"
if [ "${TEST_AGENT_EVENT:-}" = failed ]; then
  printf '%s\n' '{"type":"turn.failed","error":{"message":"mock failure"}}'
  exit 0
fi
if [ "${TEST_AGENT_EVENT:-}" = incomplete ]; then
  printf '%s\n' '{"type":"error","message":"usage limit"}'
  exit 0
fi
if [ "${TEST_AGENT_EVENT:-}" = reconnect ]; then
  printf '%s\n' '{"type":"error","message":"Reconnecting... 2/5"}'
fi
printf '%s\n' '{"type":"thread.started","thread_id":"codex-test"}' '{"type":"item.completed","item":{"type":"web_search","query":"https://example.com"}}' '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}'
exit "${TEST_AGENT_EXIT:-0}"
""")
        self.write_stub("claude", """#!/bin/sh
printf '%s\n' "$@" > "$TEST_ARGS"
printf '%s:%s\n' "${CODEX_API_KEY:-}" "${ANTHROPIC_API_KEY:-}" > "$TEST_KEYS"
if [ "${TEST_AGENT_EVENT:-}" = failed ]; then
  printf '%s\n' '{"type":"result","subtype":"error","num_turns":1}'
  exit 0
fi
printf '%s\n' '{"type":"system","subtype":"init","session_id":"claude-test"}' '{"type":"result","subtype":"success","num_turns":1,"total_cost_usd":0}'
exit "${TEST_AGENT_EXIT:-0}"
""")

    def write_stub(self, name, body):
        path = self.root / "bin" / name
        path.write_text(body)
        path.chmod(0o755)

    def run_script(self, *args, agent_exit="0", agent_event="success"):
        env = os.environ.copy()
        env["PATH"] = str(self.root / "bin") + os.pathsep + env["PATH"]
        env["TEST_ARGS"] = str(self.root / "state" / "args")
        env["TEST_KEYS"] = str(self.root / "state" / "agent_keys")
        env["TEST_STDIN"] = str(self.root / "state" / "stdin")
        env["TEST_AGENT_EXIT"] = agent_exit
        env["TEST_AGENT_EVENT"] = agent_event
        env["CODEX_API_KEY"] = "test-codex-key"
        env["ANTHROPIC_API_KEY"] = "test-claude-key"
        return subprocess.run(
            ["/bin/bash", str(self.root / "scripts" / "run.sh"), *args],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_codex_is_default_and_dry_skips_notification(self):
        result = self.run_script("--dry")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "state" / "args").read_text().splitlines()
        self.assertIn("-a", args)
        self.assertIn("never", args)
        self.assertIn("--search", args)
        self.assertIn("--ignore-user-config", args)
        self.assertEqual(args[args.index("--model") + 1], "gpt-6-astra")
        self.assertEqual(args[args.index("-c") + 1], 'model_reasoning_effort="low"')
        self.assertIn("plugins", args)
        self.assertIn("apps", args)
        self.assertIn("workspace-write", args)
        self.assertIn("--json", args)
        self.assertEqual((self.root / "state" / "stdin").read_text(), "Test prompt\n")
        self.assertIn("agent session codex-test", result.stdout)
        self.assertIn("web_search  https://example.com", result.stdout)
        self.assertEqual((self.root / "state" / "agent_keys").read_text().strip(), "test-codex-key:")
        self.assertEqual((self.root / "state" / "fetch_keys").read_text(), ":")
        self.assertFalse((self.root / "state" / "notified").exists())

    def test_claude_override_keeps_tool_allowlist(self):
        result = self.run_script("--inference", "claude", "--dry")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "state" / "args").read_text().splitlines()
        self.assertEqual(args[0:2], ["-p", "Test prompt"])
        self.assertIn("Read,Write,WebFetch", args)
        self.assertIn("agent session claude-test", result.stdout)
        self.assertEqual((self.root / "state" / "agent_keys").read_text().strip(), ":test-claude-key")
        self.assertEqual((self.root / "state" / "fetch_keys").read_text(), ":")
        self.assertFalse((self.root / "state" / "notified").exists())

    def test_external_vault_is_writable_for_codex(self):
        vault = tempfile.TemporaryDirectory()
        self.addCleanup(vault.cleanup)
        vault_path = Path(vault.name) / "outside-vault"
        config_path = self.root / "config.json"
        config = json.loads(config_path.read_text())
        config["paths"]["vault_dir"] = str(vault_path)
        config_path.write_text(json.dumps(config))

        result = self.run_script("--dry")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "state" / "args").read_text().splitlines()
        self.assertEqual(args[args.index("--add-dir") + 1], str(vault_path.resolve()))
        self.assertTrue(vault_path.is_dir())

    def test_invalid_inference_fails_before_fetch(self):
        result = self.run_script("--inference", "other")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "state" / "fetched").exists())

    def test_agent_failure_stops_notification(self):
        result = self.run_script(agent_exit="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / "state" / "fetched").exists())
        self.assertFalse((self.root / "state" / "notified").exists())

    def test_reconnect_notice_does_not_stop_completed_run(self):
        result = self.run_script(agent_event="reconnect")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("agent notice: Reconnecting... 2/5", result.stdout)
        self.assertIn("agent done: input_tokens=10", result.stdout)
        self.assertTrue((self.root / "state" / "notified").exists())

    def test_missing_completion_stops_notification(self):
        result = self.run_script(agent_event="incomplete")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("without a successful turn", result.stderr)
        self.assertFalse((self.root / "state" / "notified").exists())

    def test_failed_event_stops_notification_even_with_zero_cli_exit(self):
        for args in ((), ("--inference", "claude")):
            with self.subTest(args=args):
                result = self.run_script(*args, agent_event="failed")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "state" / "notified").exists())


if __name__ == "__main__":
    unittest.main()
