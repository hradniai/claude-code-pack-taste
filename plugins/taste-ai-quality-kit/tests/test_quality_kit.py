from __future__ import annotations

import json
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RUN_EVAL = ROOT / "tools" / "prompt-eval" / "run_eval.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("taste_quality_run_eval", RUN_EVAL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QualityKitTests(unittest.TestCase):
    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPTS / script), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_context_rejects_unmaintained_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ("models.md", "prompting.md", "decisions.md"):
                (root / name).write_text(f"# {name}\n\nstatus: TODO\n", encoding="utf-8")
            result = self.run_script("check_llm_context.py", "--context-dir", str(root))
            self.assertEqual(result.returncode, 10)
            self.assertEqual(json.loads(result.stdout)["status"], "CONTEXT_NOT_READY")

    def test_context_accepts_maintained_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ("models.md", "prompting.md", "decisions.md"):
                (root / name).write_text("# Record\n\nVerified operating record with source and date.\n" * 3, encoding="utf-8")
            result = self.run_script("check_llm_context.py", "--context-dir", str(root))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["status"], "CONTEXT_READY")

    def test_sanitizer_blocks_secret_like_literal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = Path(temp_dir) / "prompt.md"
            # Split so the source file itself carries no key-shaped literal for repository secret scanners.
            prompt.write_text("Return JSON. Key: " + "sk-" + "not-a-real-key-012345678901", encoding="utf-8")
            result = self.run_script("sanitize_prompt.py", "--prompt", str(prompt))
            self.assertEqual(result.returncode, 20)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL")
            self.assertTrue(any(item["rule"] == "secret_like_literal" for item in payload["findings"]))

    def test_sanitizer_warns_when_escape_hatch_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = Path(temp_dir) / "prompt.md"
            prompt.write_text("Return JSON with a title.", encoding="utf-8")
            result = self.run_script("sanitize_prompt.py", "--prompt", str(prompt))
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "WARN")
            self.assertTrue(any(item["rule"] == "missing_escape_hatch" for item in payload["findings"]))

    def test_live_runner_hides_runtime_when_context_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt = root / "prompt.md"
            prompt.write_text("Return JSON with null for unknown values.", encoding="utf-8")
            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS / "run_live_eval.sh"),
                    "--context-dir",
                    str(root / "missing-context"),
                    "--prompt",
                    str(prompt),
                    "--intent",
                    "Return a safe result.",
                    "--tier",
                    "single-judge",
                    "--model",
                    "google/gemini-test",
                    "--judge",
                    "google/gemini-judge",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 10)
            self.assertIn("EVAL_NOT_CONFIGURED", result.stderr)
            self.assertNotIn("agents-cli", result.stderr)

    def test_model_id_requires_a_supported_provider_prefix(self) -> None:
        runner = load_runner_module()
        self.assertEqual(runner.parse_model_id("google/gemini-example"), ("google", "gemini-example"))
        self.assertEqual(runner.parse_model_id("gemini/gemini-example"), ("google", "gemini-example"))
        self.assertEqual(runner.parse_model_id("claude-code/sonnet-example"), ("claude-code", "sonnet-example"))
        self.assertEqual(runner.parse_model_id("codex/gpt-example"), ("codex", "gpt-example"))
        with self.assertRaises(ValueError):
            runner.parse_model_id("gemini-example")
        with self.assertRaises(ValueError):
            runner.parse_model_id("unknown/model")

    def test_claude_code_headless_auth_failure_is_explicit(self) -> None:
        runner = load_runner_module()
        payload = json.dumps({"is_error": True, "result": "Not logged in · Please run /login"})
        with self.assertRaisesRegex(runner.EvaluationCallError, "authentication is not ready"):
            runner.parse_claude_code_result(payload)

    def test_tier_validates_single_judge_and_custom_jury(self) -> None:
        runner = load_runner_module()
        runner.validate_tier("single-judge", ["google/gemini-example"])
        runner.validate_tier("jury", ["google/gemini-example", "openai/gpt-example"])
        runner.validate_tier("jury", ["claude-code/sonnet-example", "codex/gpt-example"])
        with self.assertRaises(ValueError):
            runner.validate_tier("single-judge", ["google/one", "openai/two"])
        with self.assertRaises(ValueError):
            runner.validate_tier("jury", ["google/one"])

    def test_live_runner_requires_only_selected_provider_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ("models.md", "prompting.md", "decisions.md"):
                (root / name).write_text("# Record\n\nVerified operating record with source and date.\n" * 3, encoding="utf-8")
            (root / ".env").write_text("GOOGLE_API_KEY=placeholder\n", encoding="utf-8")
            prompt = root / "prompt.md"
            prompt.write_text("Return JSON with null for unknown values.", encoding="utf-8")
            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS / "run_live_eval.sh"),
                    "--context-dir",
                    str(root),
                    "--prompt",
                    str(prompt),
                    "--intent",
                    "Return a safe result.",
                    "--tier",
                    "jury",
                    "--model",
                    "google/gemini-test",
                    "--judge",
                    "google/gemini-judge",
                    "--judge",
                    "anthropic/claude-judge",
                    "--workspace",
                    str(root),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 10)
            self.assertIn("selected model has no configured provider key", result.stderr)

    def test_workspace_history_is_grouped_by_prompt_slug(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            prompt_path = workspace / "Useful Prompt.md"
            prompt = "Return null when the answer is unknown."
            prompt_path.write_text(prompt, encoding="utf-8")
            report = {
                "target_model": "google/gemini-example",
                "judge_models": ["google/gemini-example"],
                "overall_verdict": "PASS",
                "overall_score": 4.0,
                "cases": [{"output": "{\"result\": null}", "aggregate": {"verdict": "PASS", "score": 4.0}}],
            }
            run_dir = runner.write_workspace_run(
                workspace=workspace,
                prompt_path=prompt_path,
                prompt=prompt,
                intent="Return a safe response.",
                tier="single-judge",
                examples=["unknown input"],
                report=report,
            )
            history = workspace / "prompt-evals" / "useful-prompt" / "history.jsonl"
            self.assertTrue((run_dir / "input.md").is_file())
            self.assertTrue((run_dir / "examples.json").is_file())
            self.assertTrue((run_dir / "outputs" / "00.md").is_file())
            self.assertTrue((run_dir / "verdicts.json").is_file())
            self.assertTrue((run_dir / "report.md").is_file())
            row = json.loads(history.read_text(encoding="utf-8").strip())
            self.assertEqual(row["tier"], "single-judge")
            self.assertEqual(row["target_model"], "google/gemini-example")


if __name__ == "__main__":
    unittest.main()
