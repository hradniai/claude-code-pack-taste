from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginContractTests(unittest.TestCase):
    def test_manifest_and_required_workflows_exist(self) -> None:
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "taste-ai-quality-kit")
        for path in (
            "agents/prompt-engineer.md",
            "skills/using-taste-ai-quality-kit/SKILL.md",
            "skills/prompt-eval/SKILL.md",
            "skills/skill-intake/SKILL.md",
            "scripts/check_llm_context.py",
            "scripts/sanitize_prompt.py",
            "scripts/run_live_eval.sh",
            "tools/prompt-eval/run_eval.py",
            "references/agent-judge-runtimes.md",
            "tools/skill-scanner/scripts/scan.py",
        ):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_plugin_does_not_bundle_user_llm_context(self) -> None:
        forbidden = [path for path in ROOT.rglob("*") if path.is_file() and "llms" in path.as_posix().lower()]
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main()
