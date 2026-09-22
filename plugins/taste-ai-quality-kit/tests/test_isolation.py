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
    def test_auto_picks_namespace_on_linux_and_per_runtime_levels_on_macos(self) -> None:
        iso = load_isolation()
        with mock.patch.object(iso.platform, "system", return_value="Linux"), mock.patch.object(iso, "bwrap_available", return_value=True):
            self.assertEqual(iso.resolve_level("auto", "claude-code"), "namespace")
            self.assertEqual(iso.resolve_level("auto", "codex"), "namespace")
        with mock.patch.object(iso.platform, "system", return_value="Linux"), mock.patch.object(iso, "bwrap_available", return_value=False):
            with self.assertRaisesRegex(iso.IsolationError, "bubblewrap"):
                iso.resolve_level("auto", "claude-code")  # Claude Code's own Linux sandbox is bubblewrap too: no weaker level
            with self.assertRaises(iso.IsolationError):
                iso.resolve_level("namespace", "codex")
            self.assertEqual(iso.resolve_level("environment", "codex"), "environment")
        with mock.patch.object(iso.platform, "system", return_value="Darwin"), mock.patch.object(iso, "bwrap_available", return_value=False):
            self.assertEqual(iso.resolve_level("auto", "claude-code"), "sandboxed")
            self.assertEqual(iso.resolve_level("auto", "codex"), "config-only")
        with mock.patch.object(iso.platform, "system", return_value="Windows"), mock.patch.object(iso, "bwrap_available", return_value=False):
            with self.assertRaisesRegex(iso.IsolationError, "WSL2"):
                iso.resolve_level("auto", "codex")
        with self.assertRaises(iso.IsolationError):
            iso.resolve_level("bogus", "codex")

    def test_a_level_built_for_the_other_runtime_is_refused_not_recorded(self) -> None:
        iso = load_isolation()
        with mock.patch.object(iso.platform, "system", return_value="Darwin"), mock.patch.object(iso, "bwrap_available", return_value=False):
            with self.assertRaisesRegex(iso.IsolationError, "config-only"):
                iso.resolve_level("sandboxed", "codex")
            with self.assertRaisesRegex(iso.IsolationError, "sandboxed"):
                iso.resolve_level("config-only", "claude-code")

    def test_namespace_unshares_pid_and_ipc_but_not_the_network(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            home_stage = Path(temp_dir) / "home"
            home_stage.mkdir()
            work = Path(temp_dir) / "work"
            work.mkdir()
            argv, _ = iso.namespace_argv(runtime="codex", work=work, home_stage=home_stage, cli_paths=[])
        for flag in ("--unshare-pid", "--unshare-ipc", "--new-session"):
            self.assertIn(flag, argv)
            self.assertLess(argv.index(flag), argv.index("--proc"))
        self.assertNotIn("--unshare-net", argv)
        self.assertNotIn("--unshare-all", argv)

    def test_state_file_copy_drops_mcp_servers_projects_and_secret_like_keys(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            state = Path(temp_dir) / ".claude.json"
            state.write_text(json.dumps({
                "hasCompletedOnboarding": True,
                "oauthAccount": {"emailAddress": "user@example.com"},
                "mcpServers": {"db": {"env": {"DB_PASSWORD": "x"}}},
                "projects": {"/Users/me/client-a": {}},
                "someApiToken": "abc",
            }), encoding="utf-8")
            kept = json.loads(iso.stripped_state_file(state))
        self.assertTrue(kept["hasCompletedOnboarding"])
        self.assertIn("oauthAccount", kept)
        for name in ("mcpServers", "projects", "someApiToken"):
            self.assertNotIn(name, kept)
        self.assertEqual(iso.stripped_state_file(Path(temp_dir) / "missing.json"), "{}")

    def test_non_namespace_levels_keep_the_workspace_outside_every_denied_root(self) -> None:
        iso = load_isolation()
        with mock.patch.object(iso.platform, "system", return_value="Darwin"), mock.patch.object(iso, "bwrap_available", return_value=False):
            launch = iso.plan_launch(runtime="claude-code", requested="auto", brief="b", context_paths=[], environment_workdir=Path("/tmp"))
        try:
            self.assertEqual(launch.level, "sandboxed")
            work = launch.workdir.resolve()
            self.assertTrue(str(work).startswith(str(Path(tempfile.gettempdir()).resolve())))
            self.assertNotIn(str(Path.home()), str(work))
            self.assertTrue((work / "brief.md").exists())
        finally:
            for path in launch.cleanup_paths:
                import shutil
                shutil.rmtree(path, ignore_errors=True)

    def test_cli_bind_paths_cover_symlink_dir_and_npm_package_prefix(self) -> None:
        iso = load_isolation()
        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir) / "npm-global"
            package = prefix / "lib" / "node_modules" / "@vendor" / "cli" / "bin"
            package.mkdir(parents=True)
            real = package / "cli.js"
            real.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            real.chmod(0o755)
            bin_dir = prefix / "bin"
            bin_dir.mkdir()
            (bin_dir / "fakecli").symlink_to(real)
            with mock.patch.object(iso.shutil, "which", side_effect=lambda name: str(bin_dir / "fakecli") if name == "fakecli" else None):
                paths = iso.cli_bind_paths("fakecli")
            self.assertIn(str(bin_dir), paths)
            self.assertIn(str(prefix / "lib"), paths)  # the parent of node_modules, so the package keeps its dependency tree
            with mock.patch.object(iso.shutil, "which", return_value=None):
                with self.assertRaises(iso.IsolationError):
                    iso.cli_bind_paths("missing-cli")

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
