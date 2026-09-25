---
type: context
title: "Architecture"
status: approved
summary: "How the starter pack is laid out and why each piece exists."
created: 2026-05-13 12:08
updated: 2026-09-25 10:50
owner: Šimon Hradní
client: ~
path: docs/architecture.md
tags: [handbook]
version: "1.0.0"
release: latest
---

# Architecture

How the starter pack is laid out and why each piece exists.

## Two halves: kernel and workspace

```
~/.claude/             ← kernel: settings, rules, skills, scripts, hooks
~/Documents/           ← workspace: per-context directories you actually work in
```

**Kernel** is the configuration that travels with Claude across all projects. It defines safety boundaries, default behaviors, available skills, and reusable scripts. Lives in `~/.claude/`.

**Workspace** is where your work happens. Per-client, per-business-area, per-app directories. Each top-level directory is opinionated about what belongs there.

The two halves are loosely coupled - you can install just the kernel if you don't want the workspace structure, and vice versa.

## Kernel layout

```
~/.claude/
├── settings.json              ← permissions (allow/deny/ask), hooks, env vars
├── AGENTS.md                  ← global behavioral baseline
├── CLAUDE.md → AGENTS.md      ← symlink so Claude Code reads same content
├── rules/                     ← auto-loaded into every session
├── reference/                 ← on-demand reference docs (frontmatter standard), not auto-loaded
├── scripts/                   ← user-invokable utilities
├── hooks/                     ← harness-invoked, runs on events
├── agents/                    ← custom subagent definitions
├── skills/                    ← bundled skills (setup, skill-creator, prd-creator, dr-prompt, client-data-check, idea-file-creator)
├── plugins/                   ← separately installed workflow bundles
└── templates/                 ← scaffolding templates for the /setup skill
```

## Workspace layout

```
~/Documents/
├── _CONTEXT/                  ← user profile, notes, best-practices, mandatory llms/
├── _CLIENTS/                  ← per-client engagement folders
├── _BUSINESS/                 ← your own business work
└── _APPS/                     ← tools and apps you build
```

Each top-level workspace directory has its own AGENTS.md (with CLAUDE.md symlink) explaining what belongs there, except `_CLIENTS/` itself (you should never run Claude from `_CLIENTS/`, only from a specific client subfolder).

## File convention: AGENTS.md + CLAUDE.md symlink

Every project root has both files. They point to the same content via symlink:

```
project/
├── AGENTS.md       ← canonical content
└── CLAUDE.md       ← symlink → AGENTS.md
```

**Why both?**
- `AGENTS.md` is a cross-tool convention adopted by Cursor, Codex, Gemini CLI, Aider, and ~20 other tools (Linux Foundation Agentic AI Foundation, ratified Dec 2025).
- `CLAUDE.md` is what Claude Code reads. Claude Code 2.1.277+ can fall back to AGENTS.md when a folder has no CLAUDE.md, but that fallback needs feature flags, which this pack's `DISABLE_TELEMETRY=1` switches off. In this pack Claude Code reads only CLAUDE.md, so the CLAUDE.md symlink is required, not a convenience.
- Symlink means one source of truth, two file paths. Edit either, and both reflect.

## Hook flow (data path)

When Claude uses a tool, multiple things happen:

```
Claude uses a tool (Bash, Read, Edit, Write, ...)
        ↓
PreToolUse hooks fire   ← bash-safety-extended.py (Bash and Read) blocks dangerous patterns and env-file reads
        ↓
Permission engine       ← allow/deny/ask matched against settings.json
        ↓
Tool executes
```

Hooks invoked by harness do NOT go through the permission engine. They're trusted code shipped with the kernel.

## Notes and inbox

### Notes (plain file)

Every `notes.md` is a plain file for ideas and impulses. No hook watches it and nothing is sent anywhere; when a note deserves research, ask Claude for it.

### Inbox → knowledge base (manual)

`docs/inbox/`: drop files here, then ask Claude to ingest them into `knowledge-base/drafts/` (manual, no hook). You review the drafts and promote what is useful to `docs/knowledge-base/`.

## What flows where

| Layer | Reads from | Writes to |
|-------|------------|-----------|
| Claude Code session | `~/.claude/CLAUDE.md`, `~/.claude/rules/*`, project `AGENTS.md/CLAUDE.md` | Files via Edit/Write tools (with permissions) |
| `bash-safety-extended.py` hook | hook stdin (Bash and Read tool input) | stderr (block reasons), exit code 0/2 |
| `list-env-keys.sh` script | process env, `~/.claude/.env`, `./.env` | stdout (var names only) |

## Trust boundary

The kernel ships with safety enforced via:
1. **`settings.json` denies** - destructive bash, sensitive file reads
2. **`bash-safety-extended.py` hook** - patterns that simple deny rules miss
3. **`disableBypassPermissionsMode: "disable"`** - bypass mode locked off
4. **`respect-denies.md` rule** - Claude is instructed to never bypass denies, only inform user

These protect against accidents and Claude being misled into destructive actions. They do **not** protect against a determined adversary on your machine. For locked-down environments, see `safety-model.md`.
