from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ISOLATION = ROOT / "tools" / "prompt-eval" / "isolation.py"


def load_isolation():
    spec = importlib.util.spec_from_file_location("taste_quality_isolation", ISOLATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve postponed annotations through sys.modules
    spec.loader.exec_module(module)
    return module


class IsolationTests(unittest.TestCase):
    def test_auto_picks_namespace_when_bubblewrap_exists_else_per_runtime_fallback(self) -> None:
        iso = load_isolation()
        with mock.patch.object(iso, "bwrap_available", return_value=True):
            self.assertEqual(iso.resolve_level("auto", "claude-code"), "namespace")
            self.assertEqual(iso.resolve_level("auto", "codex"), "namespace")
        with mock.patch.object(iso, "bwrap_available", return_value=False):
            self.assertEqual(iso.resolve_level("auto", "claude-code"), "sandboxed")
            self.assertEqual(iso.resolve_level("auto", "codex"), "config-only")
            self.assertEqual(iso.resolve_level("environment", "codex"), "environment")
            with self.assertRaises(iso.IsolationError):
                iso.resolve_level("namespace", "codex")
        with self.assertRaises(iso.IsolationError):
            iso.resolve_level("bogus", "codex")

    def test_namespace_argv_orders_every_tmpfs_before_every_bind_and_binds_the_workspace(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            home_stage = Path(temp_dir) / "home"
            home_stage.mkdir()
            work = Path(temp_dir) / "work"
            work.mkdir()
            argv, env = iso.namespace_argv(runtime="codex", work=work, home_stage=home_stage, cli_paths=["/opt/fake-cli", "/usr/bin"])
        self.assertEqual(argv[0], "bwrap")
        first_bind_after_tmpfs = min(i for i, a in enumerate(argv) if a in ("--bind", "--ro-bind") and i > argv.index("--tmpfs"))
        last_tmpfs = max(i for i, a in enumerate(argv) if a == "--tmpfs" and argv[i + 1] in iso.TMPFS_PATHS)
        self.assertLess(last_tmpfs, first_bind_after_tmpfs, "a tmpfs after a bind hides it and bwrap aborts")
        self.assertIn(str(work), argv)
        self.assertIn("--ro-bind", argv[argv.index("/opt/fake-cli") - 1:argv.index("/opt/fake-cli")])
        self.assertNotIn("/usr/bin", argv[argv.index("--tmpfs"):])  # already covered by the /usr bind
        self.assertEqual(argv[-1], "--")
        self.assertEqual(argv[argv.index("--chdir") + 1], str(work))
        self.assertIn("--die-with-parent", argv)
        self.assertIn("CODEX_HOME", env)
        self.assertNotIn("/tmp", env["CODEX_HOME"].split(os.sep)[:2])

    def test_namespace_binds_claude_login_material_only(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir) / "user"
            (fake_home / ".claude").mkdir(parents=True)
            (fake_home / ".claude" / ".credentials.json").write_text("{}", encoding="utf-8")
            (fake_home / ".claude.json").write_text("{}", encoding="utf-8")
            (fake_home / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
            home_stage = Path(temp_dir) / "stage"
            home_stage.mkdir()
            work = Path(temp_dir) / "work"
            work.mkdir()
            with mock.patch.dict(os.environ, {"HOME": str(fake_home)}, clear=False):
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
                argv, env = iso.namespace_argv(runtime="claude-code", work=work, home_stage=home_stage, cli_paths=[])
            self.assertIn(str(fake_home / ".claude" / ".credentials.json"), argv)
            self.assertIn(str(fake_home / ".claude.json"), argv)
            self.assertNotIn(str(fake_home / ".claude" / "settings.json"), argv)
            self.assertTrue((home_stage / "claude-state.json").exists())
            self.assertEqual(env["HOME"], str(fake_home))

    def test_sandboxed_settings_deny_user_data_roots_for_every_file_tool(self) -> None:
        iso = load_isolation()
        settings = json.loads(iso.sandboxed_settings(Path("/tmp/judge")))
        self.assertTrue(settings["sandbox"]["enabled"])
        self.assertTrue(settings["sandbox"]["failIfUnavailable"])
        self.assertFalse(settings["sandbox"]["allowUnsandboxedCommands"])
        self.assertEqual(settings["sandbox"]["network"]["allowedDomains"], [])
        self.assertTrue(settings["permissions"]["blockReadsOutsideWorkingDirectories"])
        deny = settings["permissions"]["deny"]
        for tool in iso.FILE_TOOLS:
            self.assertIn(f"{tool}(~/**)", deny)
            self.assertIn(f"{tool}(//Users/**)", deny)

    def test_prepare_workspace_writes_brief_and_copies_context(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "guidelines"
            source_dir.mkdir()
            (source_dir / "style.md").write_text("Be brief.", encoding="utf-8")
            source_file = Path(temp_dir) / "sample.csv"
            source_file.write_text("a,b\n", encoding="utf-8")
            work = Path(temp_dir) / "work"
            work.mkdir()
            copied = iso.prepare_workspace(work, "the brief", [source_dir, source_file])
            self.assertEqual((work / "brief.md").read_text(encoding="utf-8"), "the brief")
            self.assertEqual(sorted(copied), ["context/guidelines", "context/sample.csv"])
            self.assertEqual((work / "context" / "guidelines" / "style.md").read_text(encoding="utf-8"), "Be brief.")
            with self.assertRaises(iso.IsolationError):
                iso.prepare_workspace(work, "x", [Path(temp_dir) / "missing"])

    def test_environment_level_runs_in_the_workspace_with_nothing_to_clean(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            launch = iso.plan_launch(runtime="claude-code", requested="environment", brief="b", context_paths=[], environment_workdir=Path(temp_dir))
            self.assertEqual(launch.level, "environment")
            self.assertEqual(launch.workdir, Path(temp_dir))
            self.assertEqual(launch.argv_prefix, [])
            self.assertEqual(launch.cleanup_paths, [])
            self.assertFalse((Path(temp_dir) / "brief.md").exists())

    def test_config_only_level_gives_codex_a_fresh_home_with_only_the_login(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_codex_home = Path(temp_dir) / "codex"
            fake_codex_home.mkdir()
            (fake_codex_home / "auth.json").write_text("{}", encoding="utf-8")
            (fake_codex_home / "config.toml").write_text("model = 'x'\n", encoding="utf-8")
            stage = Path(temp_dir) / "stage"
            stage.mkdir()
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(fake_codex_home)}, clear=False):
                env = iso.config_only_env(stage)
            fresh = Path(env["CODEX_HOME"])
            self.assertTrue((fresh / "auth.json").exists())
            self.assertFalse((fresh / "config.toml").exists())


if __name__ == "__main__":
    unittest.main()
