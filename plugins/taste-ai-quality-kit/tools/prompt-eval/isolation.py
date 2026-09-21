#!/usr/bin/env python3
"""Where an agent judge runs and what it can see.

An agent judge (Claude Code or Codex) executes the prompt under test with real tools, so the point of isolation is
not to take its tools away but to decide what it can look at. The default hides the user's machine and shows only a
curated workspace: the brief plus whatever context files the orchestrator chose to copy in. The `environment`
level is the explicit opt-in that runs the judge in the user's real workspace instead.

Levels, strongest first:

- `namespace`   Linux and WSL2 with bubblewrap. The whole judge process runs in a mount namespace: system directories
                read-only, an empty home, only the login material and the judge workspace bound in. Nothing else on
                the machine exists for it. Measured 2026-09-21 on Linux for Claude Code with Bash, Read, Write, Grep
                and Glob.
- `sandboxed`   Claude Code on macOS (and on Linux when bubblewrap is absent): Claude Code's own Seatbelt sandbox for
                shell commands (writes only inside the judge workspace, no reads outside working directories, no
                network for commands) plus permission rules that deny the file tools every user data root. It is a
                deny list, not a namespace: paths not on the list stay readable. Documented, not measured on macOS yet.
- `config-only` Codex on macOS: a fresh CODEX_HOME with the login copied in and the judge workspace as working
                directory, so no user config, skills or project instructions reach the judge. Codex's own sandbox
                confines writes, not reads.
- `environment` The judge runs in the user's real workspace with the user's own settings. Chosen by the user
                for one run and recorded in the report.

Every level scrubs provider keys from the judge's environment; that part is not negotiable.
Bubblewrap argv ordering is load-bearing: every tmpfs precedes every bind, or bwrap aborts with "Can't chdir".
"""

from __future__ import annotations

import json
import os
import platform
import secrets
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LEVELS = ("auto", "namespace", "sandboxed", "config-only", "environment")
SYSTEM_READONLY = ("/usr", "/bin", "/sbin", "/lib", "/lib64", "/etc")
TMPFS_PATHS = ("/tmp", "/run", "/home", "/root")
MASKED_POLICY_DIRS = ("/etc/claude-code", "/etc/codex")
# Data roots the file tools may not read in `sandboxed` mode. The judge workspace lives under the system temp
# directory, which is on none of these. `//` is Claude Code's absolute-path prefix in permission rules.
DENY_ROOTS = ("~/**", "//Users/**", "//home/**", "//root/**", "//srv/**", "//mnt/**", "//media/**",
              "//Volumes/**", "//opt/**")
FILE_TOOLS = ("Read", "Edit", "Write", "Grep", "Glob")


class IsolationError(RuntimeError):
    pass


@dataclass
class JudgeLaunch:
    level: str
    workdir: Path
    argv_prefix: list = field(default_factory=list)
    cli_args: list = field(default_factory=list)
    env_overrides: dict = field(default_factory=dict)
    note: str = ""
    cleanup_paths: list = field(default_factory=list)


def home_dir() -> Path:
    return Path(os.environ.get("HOME") or Path.home())


def cache_root() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or (home_dir() / ".cache")) / "taste-ai-quality-kit" / "judge"


def bwrap_available() -> bool:
    return platform.system() == "Linux" and shutil.which("bwrap") is not None


def resolve_level(requested: str, runtime: str) -> str:
    """The level a run can actually deliver on this machine for this runtime."""
    if requested not in LEVELS:
        raise IsolationError(f"unknown isolation level {requested!r}; use one of {', '.join(LEVELS)}")
    if requested == "environment":
        return "environment"
    if requested == "namespace" and not bwrap_available():
        raise IsolationError("namespace isolation needs bubblewrap on Linux or WSL2 (bwrap not found)")
    if requested != "auto":
        return requested
    if bwrap_available():
        return "namespace"
    return "sandboxed" if runtime == "claude-code" else "config-only"


def new_judge_root(label: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = cache_root() / f"{stamp}-{label}-{secrets.token_hex(3)}"
    (root / "work").mkdir(parents=True)
    (root / "home").mkdir()
    return root


def prepare_workspace(work: Path, brief: str, context_paths: list) -> list:
    """Write the brief and copy the curated context into the judge workspace. Returns what was copied."""
    (work / "brief.md").write_text(brief, encoding="utf-8")
    copied = []
    for raw in context_paths:
        source = Path(raw).expanduser().resolve()
        if not source.exists():
            raise IsolationError(f"judge context path does not exist: {source}")
        target = work / "context" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
        copied.append(str(target.relative_to(work)))
    return copied


def cli_bind_paths(executable: str) -> list:
    """Directories a CLI needs read-only inside the namespace: its PATH entry, its real package, and node for Codex."""
    found = shutil.which(executable)
    if not found:
        raise IsolationError(f"{executable} is not installed or not on PATH")
    real = Path(found).resolve()
    package = real.parent
    for ancestor in real.parents:  # an npm install lives under a node_modules tree; bind that whole prefix
        if ancestor.name == "node_modules":
            package = ancestor.parent
            break
    paths = {str(Path(found).parent), str(package)}
    node = shutil.which("node")
    if node:
        paths.add(str(Path(node).resolve().parent))
    return sorted(paths)


def _covered(path: str, roots) -> bool:
    p = Path(path)
    return any(p == Path(r) or Path(r) in p.parents for r in roots)


def namespace_argv(*, runtime: str, work: Path, home_stage: Path, cli_paths: list) -> tuple:
    """bwrap prefix plus the environment overrides that make the login material visible inside it."""
    home = home_dir()
    argv = ["bwrap"]
    for path in SYSTEM_READONLY:
        if Path(path).exists():
            argv += ["--ro-bind", path, path]
    for path in TMPFS_PATHS:  # every tmpfs before every bind
        if Path(path).exists():
            argv += ["--tmpfs", path]
    resolve_dir = "/run/systemd/resolve"  # /etc/resolv.conf is often a symlink into it
    if Path(resolve_dir).exists():
        argv += ["--ro-bind", resolve_dir, resolve_dir]
    for path in MASKED_POLICY_DIRS:  # organisation-level policies of the host never reach the judge
        if Path(path).exists():
            argv += ["--tmpfs", path]
    system_roots = [p for p in SYSTEM_READONLY if Path(p).exists()]
    for path in cli_paths:
        if not _covered(path, system_roots):
            argv += ["--ro-bind", path, path]
    env = {"HOME": str(home), "TMPDIR": "/tmp"}
    if runtime == "claude-code":
        config_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (home / ".claude"))
        credentials = config_dir / ".credentials.json"
        state_file = config_dir / ".claude.json" if (config_dir / ".claude.json").exists() else home / ".claude.json"
        argv += ["--dir", str(config_dir)]
        if credentials.exists():
            argv += ["--ro-bind", str(credentials), str(credentials)]
        if state_file.exists():  # Claude Code updates this file, so the judge gets a disposable copy
            staged = home_stage / "claude-state.json"
            shutil.copy2(state_file, staged)
            argv += ["--bind", str(staged), str(state_file)]
        if os.environ.get("CLAUDE_CONFIG_DIR"):
            env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    else:
        codex_home = home_stage / "codex-home"  # under ~/.cache, never under /tmp: the CLI refuses helpers there
        codex_home.mkdir(exist_ok=True)
        auth = Path(os.environ.get("CODEX_HOME") or (home / ".codex")) / "auth.json"
        argv += ["--bind", str(codex_home), str(codex_home)]
        if auth.exists():
            argv += ["--ro-bind", str(auth), str(codex_home / "auth.json")]
        env["CODEX_HOME"] = str(codex_home)
    argv += ["--bind", str(work), str(work)]
    argv += ["--proc", "/proc", "--dev", "/dev"]
    for name, value in env.items():
        argv += ["--setenv", name, value]
    argv += ["--chdir", str(work), "--die-with-parent", "--"]
    return argv, env


def sandboxed_settings(work: Path) -> str:
    """Claude Code settings for the `sandboxed` level, passed with --settings."""
    deny = [f"{tool}({root})" for tool in FILE_TOOLS for root in DENY_ROOTS]
    settings = {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "network": {"allowedDomains": []},
        },
        "permissions": {"blockReadsOutsideWorkingDirectories": True, "deny": deny},
    }
    return json.dumps(settings)


def config_only_env(home_stage: Path) -> dict:
    """A fresh CODEX_HOME carrying only the login, so no user config or skills reach the judge."""
    codex_home = home_stage / "codex-home"
    codex_home.mkdir(exist_ok=True)
    auth = Path(os.environ.get("CODEX_HOME") or (home_dir() / ".codex")) / "auth.json"
    if auth.exists():
        shutil.copy2(auth, codex_home / "auth.json")
    return {"CODEX_HOME": str(codex_home)}


def plan_launch(*, runtime: str, requested: str, brief: str, context_paths: list, environment_workdir: Path) -> JudgeLaunch:
    """Decide the level, build the workspace and return everything the caller needs to spawn the judge."""
    level = resolve_level(requested, runtime)
    if level == "environment":
        return JudgeLaunch(level=level, workdir=Path(environment_workdir),
                           note="runs in the user's workspace with the user's own settings; chosen for this run")
    root = new_judge_root(runtime)
    work, home_stage = root / "work", root / "home"
    copied = prepare_workspace(work, brief, context_paths)
    context_note = f"context copied in: {', '.join(copied)}" if copied else "no context files, brief only"
    if level == "namespace":
        prefix, env = namespace_argv(runtime=runtime, work=work, home_stage=home_stage,
                                     cli_paths=cli_bind_paths("claude" if runtime == "claude-code" else "codex"))
        return JudgeLaunch(level=level, workdir=work, argv_prefix=prefix, env_overrides=env, cleanup_paths=[root],
                           note=f"bubblewrap namespace, only the judge workspace visible; {context_note}")
    if level == "sandboxed":
        return JudgeLaunch(level=level, workdir=work, cli_args=["--settings", sandboxed_settings(work)], cleanup_paths=[root],
                           note=f"Claude Code sandbox for commands plus file-tool deny rules on user data roots; {context_note}")
    return JudgeLaunch(level=level, workdir=work, env_overrides=config_only_env(home_stage), cleanup_paths=[root],
                       note=f"fresh CODEX_HOME with login only, judge workspace as cwd, reads not confined; {context_note}")


def describe_workspace(work: Path, limit: int = 40) -> list:
    """Relative paths the judge left behind, for the transcript."""
    if not work.exists():
        return []
    return sorted(str(p.relative_to(work)) for p in work.rglob("*") if p.is_file())[:limit]


if __name__ == "__main__":  # `python3 isolation.py` prints what this machine can deliver
    for runtime in ("claude-code", "codex"):
        print(runtime, "->", resolve_level("auto", runtime))
    sys.exit(0)
