---
type: notes
title: "Codex CLI - usage & configuration reference"
status: ai-generated
summary: "Reference for OpenAI Codex CLI: install, auth, full command/flag surface, config.toml, sandbox & approval modes (incl. --yolo), telemetry off, AGENTS.md, MCP, skills/agents/hooks/plugins, a Codex<->Claude Code concept map, reasoning-effort cost, rate limits. Codex is alpha (multiple builds/day) - re-verify a flag before relying on it."
created: 2026-06-24 13:18
updated: 2026-09-10 22:45
owner: Šimon Hradní
client: ~
path: workspace/_CONTEXT/llms/codex-cli-reference.md
tags: [note, codex, cli, ai-review, openai]
version: "0.4.0"
release: latest
---

<codex_cli_reference>

# Codex CLI - usage & configuration reference

> AI-generated (research subagents against developers.openai.com/codex + GitHub; local ground-truth CLI v0.142.0, docs surface re-verified 2026-07-14 against release **v0.144.4** / GPT-5.6, changelog-checked 2026-07-31 against **v0.146.0**). **Codex is alpha and ships multiple builds/day, so the flag/command surface drifts - re-verify before relying on a detail.** This file may reference out to `model-reference-prompting.md` (this folder) for how to prompt GPT-5.x; it is otherwise standalone.

## Install

- **Mac:** `brew install --cask codex` -> `/opt/homebrew/bin/codex` (dep: ripgrep). Cask is current.
- **Linux server (node 22+):** `npm install -g @openai/codex` -> `/usr/bin/codex`. The npm package is `@openai/codex` (the unscoped `codex` is an unrelated 2012 project). The official `curl -fsSL https://chatgpt.com/codex/install.sh | sh` installer is the no-Node path but is blocked by the global remote-execute deny, so npm or the GitHub-release binary is used here. Install `bubblewrap` on Linux so sandboxed exec uses the system sandbox instead of the bundled fallback.

## Auth

- **Two paths.** ChatGPT OAuth login (`codex login`, browser, callback on port 1455, tokens in `~/.codex/auth.json`; needs Plus/Pro/Business/Team/Edu/Enterprise - free is blocked) vs OpenAI API key (`printenv OPENAI_API_KEY | codex login --with-api-key`, or `CODEX_API_KEY=sk-... codex exec ...` one-shot; `CODEX_API_KEY` works ONLY with `codex exec`, not the interactive TUI).
- **Headless server:** ChatGPT OAuth has no native headless flow. Options: (a) copy `~/.codex/auth.json` from a logged-in machine, (b) `codex login --device-auth` (needs device-code login enabled in account security), (c) SSH-forward port 1455. **API key is the clean headless/CI path** and also bypasses the subscription rate windows (see Rate limits).
- Source: https://developers.openai.com/codex/auth , https://developers.openai.com/codex/noninteractive

## Command surface

| Command | What it does |
|---|---|
| `codex` | Interactive TUI session. |
| `codex exec` (alias `codex e`) | **Non-interactive / headless run** = the equivalent of `claude -p`. Feeds a task, writes the final answer to stdout, exits with a code. The entry point for all automation. |
| `codex exec resume --last "<follow-up>"` | Continue a prior non-interactive session with full prior context. **Claude Code has no equivalent.** |
| `codex exec review` | Git-aware review subcommand (see below). |
| `codex mcp add\|list\|get\|remove\|login` | Manage MCP servers (writes to `~/.codex/config.toml`). |
| `codex mcp-server` | Expose Codex ITSELF as an MCP server over stdio, so another agent can drive it as a tool. Distinct from the `mcp` management subcommand. |
| `codex plugin add\|list\|remove\|marketplace` | Manage plugin bundles (skills + MCP + hooks). **`add` (renamed from `install`)** pulls from a Git/npm source; `codex plugin marketplace add\|list\|remove\|upgrade` manages sources. Remote plugins + marketplace are ON by default since 0.143.0; `/plugins` in the TUI browses them. |
| `codex features enable\|disable <flag>` | Toggle experimental internal features (e.g. `unified_exec`, `shell_snapshot`). Not a tool-extension mechanism. |
| `codex exec-server` | Experimental WebSocket subcommand for remote agent coordination. |
| `codex remote-control start\|stop\|pair` | Drive/pair a running Codex host from the ChatGPT mobile app (QR pairing). **Codex Remote reached GA 2026-06-25.** New since v0.143.0. |

### `codex exec` review patterns

- Feed a diff/file/text via stdin: `git diff HEAD~1 | codex exec "Review this diff"` ; `codex exec "Review" < file` ; `codex exec - < full-prompt.txt`.
- Read a dir in place: `codex exec -C /path "Review the auth module" -s read-only` (also `--add-dir`).
- Clean output: `-o <file>` (writes last message to file, ALSO echoes to stdout); `--json` JSONL stream (events `thread.started` / `turn.started` / `item.completed` / `turn.completed`) filtered with jq; `--output-schema <file>` for forced structured output (schema needs `"additionalProperties": false` + every property in `required`).
- stdout = final answer, stderr = progress/diagnostics (`2>/dev/null` to suppress).
- Global flags like `-a never` / `-s <mode>` must precede `exec` or it is a parse error. No approval prompt in exec (no TTY = `approval: never` implicit on the bare command).
- `--ephemeral` stops session JSONL writes to `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. `--skip-git-repo-check` for non-git dirs. `--ignore-user-config --ignore-rules` to isolate from local config/hooks/rules. `CODEX_HOME=/tmp/...` for full isolation.

### `codex exec review` subcommand

- `codex exec review --uncommitted` (staged+unstaged+untracked) | `--base main` | `--commit <sha>` | `--title <t>` | `-m <model>`. Runs git status/diff itself.
- LIMITATION: cannot combine a custom instruction string with `--base`/`--commit` - the prompt drops the target. For target + focus, use plain `codex exec` with a manual `git diff` pipe. Source: https://github.com/openai/codex/issues/22145

## Sandbox modes (the confinement layer)

Source: https://developers.openai.com/codex/agent-approvals-security . CLI flag `-s` / `--sandbox <mode>`.

| Mode | Filesystem | Network | Use |
|---|---|---|---|
| `read-only` | read only; writes + command exec need approval | off | auditing, explanation (this is the `codex exec` default) |
| `workspace-write` | read + write + run commands inside the workspace; writes outside need approval | **off by default**; set `network_access = true` in `[sandbox_workspace_write]` to allow | normal development / CI |
| `danger-full-access` | no filesystem restrictions; write anywhere | off (configurable) | externally isolated VMs only |

- In `workspace-write`, `.git/` and `.codex/` stay read-only even though the rest is writable (so `git commit` may still prompt).
- `--add-dir /path` (repeatable) grants extra write dirs alongside the workspace.
- **MEASURED 2026-09-10 on a Linux host, CLI 0.153.4: `-s` does NOT decide the sandbox when a managed `default_permissions` is set, and `codex exec` has no `--permission-profile` flag to reach the permission stack with.** With `/etc/codex/requirements.toml` declaring `default_permissions = ":danger-full-access"`, a `codex exec -s read-only` agent asked to write outside its working root did so with exit 0, no error and no warning; adding `-c default_permissions=":read-only"` refused the identical write with `Read-only file system` and exit 1. So the config key is the lever, not the flag. Two neighbouring facts: a profile absent from `[allowed_permission_profiles]` is silently replaced by the default rather than refused (which is why `-s workspace-write` became full access here), and the built-in token is **`:workspace`** - `:workspace-write` is not a profile name and yields `unknown built-in profile`. Verify any host's real behaviour with no model call and no quota: `codex sandbox --include-managed-config -P ":read-only" -C <dir> -- bash -c 'printf x > <path outside dir>'`.
- **Running the CLI inside a bubblewrap namespace restores `-s`.** `/etc/codex` is not mounted inside the namespace, so the managed policy that voids the flag is invisible and the CLI applies the profile it was asked for: two layers that agree instead of one silently failing. Measured there: the host tree is absent rather than unwritable (`ls /srv` -> `No such file or directory`), `--search` still works because web search is a Responses-API tool rather than a sandboxed shell call, hooks do NOT fire (the managed `features.hooks` flag lives in the unmounted `/etc/codex`, so this is not an `--ignore-*` effect), and an isolated `CODEX_HOME` cuts input tokens by roughly 27% on a like-for-like task because the operator's real home loads 83 plugin-skill descriptions into every session. Two gotchas: every `--tmpfs` must precede any bind under it or bwrap aborts with `Can't chdir`, and `auth.json` must be bind-mounted rather than symlinked or the run dies with repeating `401 Unauthorized`.

## Approval modes (the human-gate layer)

Source: https://developers.openai.com/codex/cli/reference . Flag `--ask-for-approval` / `-a`.

| Value | Behavior |
|---|---|
| `untrusted` | auto-run known-safe ops; ask for state-mutating / external-execution commands |
| `on-request` | ask when an action exceeds sandbox bounds (writes outside, network, destructive). Recommended interactive. |
| `never` | no prompts; autonomous within the configured sandbox. Recommended for CI / headless. |
| `on-failure` | **REMOVED from the codebase** (v0.143.0, not merely deprecated) - do not use |

- **`--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`)** removes BOTH the sandbox AND the approval prompts. **This is the exact equivalent of Claude Code's `--dangerously-skip-permissions`.** Commands run with the invoking user's full OS permissions, no confinement. Docs: "Only use inside an externally hardened environment." **Security: with `--yolo`, a malicious `AGENTS.md` or hook in a repo you do not own can exfiltrate `OPENAI_API_KEY`** - the May 2026 `codexui-android` supply-chain attack did exactly this. Never run full bypass against an untrusted repo. [OFFICIAL + COMMUNITY]
- `--full-auto` = DEPRECATED (still works, warns); replace with `codex exec --sandbox workspace-write` + `approval_policy = "never"`.
- `--dangerously-bypass-hook-trust` runs enabled hooks without persisted hook trust (automation only).
- Granular policy (config.toml): `approval_policy = { granular = { sandbox_approval, rules, mcp_elicitations, request_permissions, skill_approval } }`.
- `approvals_reviewer = "auto_review"` routes approvals through an automated reviewer policy (a Markdown policy string) - a "guardian" pattern that is safer than bare `never` for headless. Changes the reviewer, not the sandbox.
- **`writes` app-approval mode (new, v0.144.0)** - for MCP "apps" / connectors: an app's read-only actions run without prompting, writes still pause. CAVEAT: "read-only" is decided by the MCP server's `readOnlyHint` annotation, whose spec default is `false`, so tools that do not declare `readOnlyHint: true` are still treated as writes and `writes` mode often does NOT reduce prompts as expected. In `codex exec` (headless) an unresolved approval is auto-CANCELLED, not auto-approved. [OFFICIAL + community caveat]

## config.toml

Source: https://developers.openai.com/codex/config-reference . The equivalent of Claude Code's `settings.json`.

- **Locations:** user `~/.codex/config.toml` (primary - provider, auth, telemetry); project `.codex/config.toml` (loaded only for TRUSTED projects, and CANNOT override provider/auth/telemetry); profile overlay `~/.codex/<name>.config.toml`. **Precedence (highest first): CLI flags > project config > profile overlay > user config.** `CODEX_HOME` overrides the `~/.codex` path.
- **Project config silently IGNORES** `openai_base_url`, `model_provider`, `model_providers`, `profile`, `profiles`, `otel`, `notify` (and more) - those must live in the user-level file.

Key keys (selected):
- Model: `model`, `model_provider` (default `"openai"`), `model_reasoning_effort` (`minimal|low|medium|high|xhigh`), `model_reasoning_summary` (`auto|concise|detailed|none`), `model_verbosity` (`low|medium|high`), `model_context_window`, `model_auto_compact_token_limit`, `model_instructions_file` (absolute path that REPLACES the built-in system instructions and bypasses AGENTS.md - the bluntest customization lever), `model_catalog_json`.
- Confinement: `approval_policy`, `sandbox_mode`, `approvals_reviewer`, `[sandbox_workspace_write]` (`writable_roots`, `network_access`, `exclude_slash_tmp`, `exclude_tmpdir_env_var`).
- `[features]`: `multi_agent` (on), `hooks`, `unified_exec` (on except Windows), `network_proxy` (experimental), and (added since 0.142) `remote_plugin`, `personality`, `fast_mode`, `enable_request_compression`, `skill_mcp_dependency_install`, `[features.code_mode]`, `[features.rollout_budget]`. **`memories` MOVED out of `[features]` into its own top-level `[memories]` table** (`generate_memories`, `use_memories`, `disable_on_external_context`) - the old `[features] memories` key is gone.
- `[permissions.<name>]`: `extends` (`:read-only` / `:workspace` / `:danger-full-access` / a custom name), `[permissions.<name>.filesystem]` (`"path" = "write"|"deny"`), `[permissions.<name>.network]` (`enabled`, `domains."host" = "allow"`).
- `requirements.toml` = an admin/MDM enforcement layer for hooks and policies that users cannot override. **Claude Code has no equivalent.**
- **Schema is much wider than listed here (verified 2026-07-14 vs the official sample config).** Other top-level keys/tables: `personality`, `review_model`, `service_tier`, `plan_mode_reasoning_effort` (separate effort for Plan Mode), `default_permissions` (shorthand `:read-only` / `:workspace` / `:danger-full-access`), a full `[agents]` table (`max_threads`, `max_depth`, `job_max_runtime_seconds`, named sub-agent roles like `[agents.reviewer]` with own model/effort/`config_file` - the concrete surface behind `multi_agent`), `[permissions.workspace.*]` (rich: `workspace_roots`, filesystem glob allow/deny, network SOCKS5/proxy), `[tui]` (keymaps, themes e.g. `catppuccin-mocha`, status line), `[apps]` / `[apps._default]` per-app tool approvals, `[projects."<path>"] trust_level`, `[shell_environment_policy]`, `[[skills.config]]`, `[feedback]`, `[notice]` (nag-suppression + `model_migrations`).

### Profiles

Source: https://developers.openai.com/codex/config-advanced . **Breaking change in 0.134.0** (installed 0.142.0 is well past it): the old `[profiles.name]` table inside `config.toml` is GONE and the top-level `profile = "name"` selector is removed. Profiles are now **separate files** `~/.codex/<name>.config.toml` holding only the keys that differ. Activate with `codex --profile ci` / `codex exec --profile deep-review "..."`. Pre-0.134 blog posts showing `[profiles.name]` tables are actively wrong. [DRIFT - GitHub #21580]

## Telemetry - what is collected and how to disable it

Source: https://developers.openai.com/codex/config-advanced . Two separate concerns:

1. **Anonymous usage metrics - ON by default** (which features/config are in use, health; no PII; independent of OTel). **Disable entirely:**
   ```toml
   [analytics]
   enabled = false
   ```
2. **OTel export - logs + traces OFF by default, but METRICS default to Statsig.** The official sample config ships `log_user_prompt = false`, `exporter = "none"`, `trace_exporter = "none"` - BUT `metrics_exporter = "statsig"`, so anonymous usage METRICS go to Statsig (a third-party analytics vendor) unless you set `metrics_exporter = "none"`. To silence everything, set all three exporters to `"none"`. Block keys: `environment` (`dev|staging|prod`), `exporter` / `trace_exporter` / `metrics_exporter` (`none|otlp-http|otlp-grpc|statsig`), `log_user_prompt`.

`[otel]` in a project-local `.codex/config.toml` is silently ignored - put it in the user file.

## AGENTS.md - Codex's CLAUDE.md

Source: https://developers.openai.com/codex/guides/agents-md . AGENTS.md is the open cross-tool convention (Claude Code can also read it).

- **Per-directory name priority:** `AGENTS.override.md` (temporary global override) > `AGENTS.md` > any name in the `project_doc_fallback_filenames` config key (you could add `CLAUDE.md`). One file per directory (first non-empty wins).
- **Discovery tiers:** global `~/.codex/` (or `$CODEX_HOME`) first; project = from git root (or CWD if no `.git`) walking DOWN to your CWD. Merge order = global, then project root, then nested toward CWD (closer to CWD = later in the prompt = higher effective priority).
- **Size limit:** 32 KiB total (`project_doc_max_bytes = 32768`); empty files skipped, stops at the limit.
- Root detection: dir with `.git`; customize via `project_root_markers` (`[]` treats CWD as root).

## MCP servers

Source: https://developers.openai.com/codex/mcp . Two transports, two management methods.

- **Subcommand:** `codex mcp add context7 -- npx -y @upstash/context7-mcp` (stdio), `--env K=V`, `codex mcp login github` (OAuth for HTTP), `codex mcp list|get|remove`. TUI `/mcp` shows active. Writes to `~/.codex/config.toml`.
- **stdio** `[mcp_servers.<id>]`: `command` (req), `args[]`, `env{}`, `env_vars[]` (forward from host), `cwd`, `enabled` (true), `required` (fail startup if init fails), `startup_timeout_sec` (10), `tool_timeout_sec` (60), `enabled_tools[]` allowlist, `disabled_tools[]` denylist, `default_tools_approval_mode` (`auto|prompt|approve`).
- **HTTP**: `url` (req), `bearer_token_env_var` (the env var NAME), `http_headers{}`; OAuth overrides `mcp_oauth_callback_port` / `mcp_oauth_callback_url`.
- Read-only MCP tools advertising `readOnlyHint` now run in parallel.
- DRIFT (#3441): project-local MCP servers may be silently ignored if the project is not trusted; user-level config is reliable.

## Custom tools - what does NOT exist

**Codex has NO mechanism for defining custom tools with a JSON schema** - there is no equivalent of Claude's `tools: [{name, description, input_schema}]`. The tool surface is fixed: filesystem ops, bash/shell, model-native web search, plus whatever MCP servers expose. The three real extension paths are: (1) **MCP servers** (the primary path), (2) **`codex exec` shell composition** (each exec call is a tool from the shell's view; chain them with shell logic), (3) **feature flags** (`codex features enable/disable`, toggles internal behavior only). [OFFICIAL - absence confirmed]

## Codex <-> Claude Code concept map

This is "the equivalents of everything you deal with in Claude Code". Match = Full / Partial / None.

| Claude Code | Codex equivalent | Match | Note |
|---|---|---|---|
| `CLAUDE.md` | `AGENTS.md` | Full | open cross-tool convention; both tools read AGENTS.md |
| `settings.json` (permissions) | `config.toml` + `approval_policy` + `sandbox_mode` | Full | TOML; trust-gated project variant; plus `requirements.toml` admin enforcement (no CC equivalent) |
| Hooks | `hooks.json` / inline `[hooks]` | **Full - Codex has MORE events** | events: SessionStart, SubagentStart, PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, UserPromptSubmit, SubagentStop, Stop. **And they WORK in `codex exec` headless** - this is the exact gap Claude Code has (hooks silently fail under `claude -p`). |
| Skills (SKILL.md) | Agent Skills (SKILL.md in `~/.codex/skills/` or `.agents/skills/`) | Full | same open standard; `/skills` or `$name`; built-in `$skill-creator` |
| Subagents (Task tool) | Custom agents (TOML in `~/.codex/agents/`) | Full | concurrency is capped by `agents.max_concurrent_threads_per_session` (long name; `agents.max_threads` is accepted as an alias), `agents.max_depth` for nesting; inherit parent sandbox/approval; a "Guardian" subagent for headless safety. **MEASURED 2026-09-10 on CLI 0.153.4: the DEFAULT is 4 concurrency slots, i.e. the root agent plus THREE sub-agents, not 6.** Slots = the configured value + 1. Exceeding it rejects the spawn with `collab spawn failed: agent thread limit reached` (error variant `AgentLimitReached`), which a model may silently paper over by doing the work sequentially. `--ignore-user-config` drops the whole `[agents]` table and reverts to that default, so any headless fan-out must pass the cap on the command line. Any key under `[agents]` that is not a known setting is read as a named sub-agent role, so a scalar value hard-fails the call with `invalid type ... expected struct AgentRoleToml`. |
| Slash commands + user-defined | 50+ built-in + custom prompts (`~/.codex/prompts/*.md`, `/prompts:<name>`) | Partial | custom prompts just expand a Markdown template with placeholders into a message - they do NOT load tool context or spawn subagents (closer to CC "system-prompt snippets" than skills) |
| Plugins / marketplace | Plugin system + marketplace (`codex plugin install`, `/plugins`) | **Full - Codex is richer** | first-class Git-repo plugin bundles (skills + MCP + hooks); CC currently lacks a marketplace |
| `claude -p` | `codex exec` (alias `codex e`) | Full + resumability | plus `codex exec resume --last` (no CC equivalent) |
| MCP client | full MCP (stdio + HTTP) with per-server allow/deny | Full | Codex also exposes ITSELF via `codex mcp-server` |
| External RAG memory (custom retrieval layer) | built-in `/memories` | Partial | model-managed memory layer, not a custom retrieval pipeline |
| Custom tool schemas | none | **None** | fixed tool surface + MCP only |

## Models + reasoning effort (cost lever)

- **Default model is now `gpt-5.6`** (was `gpt-5.5`) since the GPT-5.6 launch 2026-07-09. `model = "gpt-5.6"` resolves to `gpt-5.6-sol` at medium reasoning (the "Power" default); `review_model = "gpt-5.6"` is the sample default for code review too. The three GPT-5.6 tiers: `gpt-5.6-sol` (flagship), `gpt-5.6-terra` (balanced), `gpt-5.6-luna` (cheap). **All three have a 272,000-token context window** (corrected in v0.144.6 - prior bundled metadata shipped wrong values). [OFFICIAL - github.com/openai/codex release rust-v0.144.6] Authoritative pricing/lineup: `model-lineup.md` (this folder). On ChatGPT auth a deprecated `-m` model silently falls back to default; API-key auth errors instead -> pin a model only with API-key auth.
- The old review-model set (gpt-5.5 / gpt-5.4 / gpt-5.4-mini / gpt-5.4-nano) is likely stale now that `review_model` defaults to `gpt-5.6`. `gpt-5.4-mini` using ~30% of gpt-5.4's included limits is OFFICIAL; gpt-5.4-nano's role in the *review* feature specifically stays UNVERIFIED.
- `model_reasoning_effort` (or `--model-reasoning-effort`) is the main cost lever. **Effort ladder EXPANDED for GPT-5.6:** `minimal` is DROPPED (GPT-5-family only); the `/model` selector now lists Low, Medium (default), High, Extra High (`xhigh`), **`max`** (first-class since PR #30467, incl. Bedrock), and **`ultra`**. `ultra` explicitly triggers automatic MULTI-AGENT delegation (spawns sub-agents via `spawn_agent` / `resume_agent` / `close_agent`, bounded by `agent_max_depth`) and fires a usage-cost warning. **MEASURED 2026-09-10 on CLI 0.153.4, the mechanism behind that:** at every effort below `ultra` Codex injects a developer message `<multi_agent_mode>Do not spawn sub-agents unless the user or applicable AGENTS.md/skill instructions explicitly ask...</multi_agent_mode>`; `ultra` replaces it with `<multi_agent_mode>Proactive multi-agent delegation is active...</multi_agent_mode>`. So delegation at `high` needs an explicit instruction in the prompt, and that is enough. Inspect either message for free with `codex debug prompt-input "hi"` - no model call, no quota.

| Effort | Use | GPT-5.6 | GPT-5.x (5.5/5.4) |
|---|---|---|---|
| `minimal` | extraction, routing, lookups | NOT available | ~20-30% of medium |
| `low` | quick checks | yes | ~50% |
| `medium` | recommended daily interactive level | default | baseline |
| `high` | complex bugs, architecture, multi-file refactor | yes | ~200-300% |
| `xhigh` / "Extra High" | hard, non-latency-sensitive | yes | ~300-500% (3-5x) on 5.4 / gpt-5.3-codex |
| `max` | maximum single-model reasoning | yes (first-class) | - |
| `ultra` | triggers multi-agent delegation - AVOID in cost-sensitive pipelines | yes (cost warning) | - |

**No official cost-multiplier table exists for GPT-5.6 effort levels yet** (OpenAI states there is no exact GPT-5.5 -> 5.6 effort mapping; re-test a familiar task at a lower level). The multipliers above are the GPT-5.x-family figures, kept for reference. TUI shortcuts `Alt+,` / `Alt+.` lower/raise effort one step mid-session.

## Rate limits

Source: https://developers.openai.com/codex/pricing . Subscription auth has **two stacked, independent, token-based windows** (token-based since 2026-04-09):
- **5-hour rolling window - SUSPENDED since 2026-07-12 (no stated end date):** OpenAI temporarily removed this window for Plus, Pro, and Business plan users in Codex and ChatGPT Work. Only the weekly window currently applies. [COMMUNITY - eesel.ai/blog, digitaltrends.com; not confirmed by official status page - re-check if behaviour differs] Before the suspension the window was: Plus ~15-80 GPT-5.5 "messages" per window (token bands); Pro 5x = 5x bands; Pro 20x = 400-2000 GPT-5.4 per window.
- **Weekly rolling window** (resets 7 days from the first message of the week), tracked independently - you can exhaust one while the other has budget.
- **Drain acceleration - now two overlapping episodes (updated 2026-07-14):** (1) COMMUNITY, from ~2026-06-16 (GitHub #28879): per-token cost on GPT-5.5 Plus jumped ~10-20x, 20+ prompts/window down to 2-3, one user's session logs as evidence. (2) OFFICIAL incident 2026-06-26 to 06-29 (status.openai.com): root cause = "abuse and fraud prevention systems incorrectly rate limiting certain accounts", stated impact "limited". The two are not clearly the same event; the symptom recurred 2026-07-02 (#30918) after OpenAI said a fix shipped 06-30, so it was not durably fixed. `high` / `xhigh` / `ultra` effort can still exhaust a window in a few prompts.
- **Escape hatches:** API key billing (`OPENAI_API_KEY`) bypasses the windows entirely, per-token at standard rates - the better value for volume and the clean headless path. Amazon Bedrock (GA 2026-06-01) = consumption-based, no windows. OpenAI also added rate-limit reset banking (one free reset per eligible subscriber, expires 30 days).
- On exhaustion: non-zero exit + stderr error (no silent skip). Source: https://github.com/openai/codex/issues/28879

## Prompting GPT-5.x for critique

Outcome-first, rubric-first; demand disagreement (anti-sycophancy is a named GPT-5.x failure mode). Reviewer frame: "prioritise finding problems over praising"; return VERDICT (APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION) + ISSUES (severity) + RISKS; "do not summarise what it does, only flag what is wrong". Force a mandatory `flaws` field via `--output-schema` so it cannot answer "looks good". **Full per-model GPT-5.x prompting detail: `model-reference-prompting.md` (this folder).** Source: https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide

## Keeping this file current

The fast-drifting part (CLI command/flag surface + version) can be checked deterministically: capture `codex --version` + `codex [exec [review]] --help`, hash them, and refresh this file when the hash drifts. The config / model / rate-limit sections need web research and are refreshed manually.

## Sources

Official: developers.openai.com/codex/{config-reference, config-advanced, agent-approvals-security, cli/reference, cli/features, guides/agents-md, mcp, skills, subagents, custom-prompts, hooks, pricing, changelog}; cookbook gpt-5 prompting guide; github.com/openai/codex (releases, issues #21580 / #3441 / #22145 / #28879). Community (cross-checked against official): smartscope.blog, blakecrosley.com, codex.danielvaughan.com.

Flag before relying in a public/production context:
- Profile system changed in 0.134 (pre-0.134 examples are wrong); `--full-auto` deprecated, `on-failure` now REMOVED; slash-command list varies by interface (check `codex --help` / TUI `/`).
- Rate-limit bands drift with pricing/model revisions; the mid-June 2026 token-cost jump is partly explained by the OFFICIAL 2026-06-26..29 abuse/fraud incident, but community reports (#28879, #30918) suggest it was not durably fixed.
- No official cost-multiplier table for GPT-5.6 effort levels yet; the review-model set is likely stale now that `review_model` defaults to gpt-5.6.
- `codex exec review` exact flag syntax was not re-confirmable in the fetched 2026-07-14 CLI reference (a `/review` slash command + `review_model` config key both exist); re-fetch the CLI reference section before relying on the precise flags.

---

## Change log

| Date | Added | Source | Removed |
|------|-------|--------|---------|
| 2026-09-10 | **Four MEASURED corrections against the installed CLI 0.153.4** (not a research pass, no other section touched). (1) Sub-agent concurrency: the default is **4 slots = root + 3 sub-agents**, not "max 6 concurrent"; slots = configured value + 1; the current key is `agents.max_concurrent_threads_per_session` with `agents.max_threads` as an alias; exceeding it raises `collab spawn failed: agent thread limit reached` (`AgentLimitReached`); `--ignore-user-config` drops the `[agents]` table back to the default; an unknown `[agents]` key is parsed as a named role and hard-fails. (2) The mechanism behind `ultra` = proactive delegation: a `<multi_agent_mode>` developer message that forbids unprompted spawning at every lower effort and is replaced at `ultra`; inspectable for free via `codex debug prompt-input`. (3) **`-s` does not decide the sandbox when a managed `default_permissions` is set**, and `codex exec` has no `--permission-profile` flag: `-s read-only` let an agent write outside its working root with exit 0, while `-c default_permissions=":read-only"` refused it; a profile missing from `[allowed_permission_profiles]` is silently replaced by the default; the built-in token is `:workspace`, not `:workspace-write`. (4) **bubblewrap restores `-s`**: `/etc/codex` is unmounted inside the namespace so the CLI honours the requested profile; the host tree is absent rather than unwritable; `--search` still works; hooks do NOT fire there (the managed `features.hooks` flag is in the unmounted file, not an `--ignore-*` effect); an isolated `CODEX_HOME` saves ~27% input tokens. | live probes (`codex exec --json` + `~/.codex/thread_history_1.sqlite` subAgentActivity rows + `codex debug prompt-input` + binary strings) | the "max 6 concurrent" figure |
| 2026-07-31 | **Changelog pass vs v0.146.0 (current stable, published 2026-07-29).** (1) Context window for all three GPT-5.6 tiers corrected to **272,000 tokens** (wrong bundled metadata fixed in v0.144.6). (2) **5-hour rolling window suspended (2026-07-12)** for Plus/Pro/Business - only weekly window now applies; no stated end date. (3) Version reference updated from v0.144.4 to v0.146.0 in intro. | github.com/openai/codex release rust-v0.144.6 (context window); eesel.ai/blog + digitaltrends.com (5h window suspension - community/press, not official OAI docs) | - |
| 2026-07-14 | **Refresh vs Codex v0.144.4 / GPT-5.6 (v0.3.0, still ai-generated).** Default model gpt-5.5 -> **gpt-5.6** (Sol/Terra/Luna); effort ladder expanded (**`max`** first-class, **`ultra`** = multi-agent delegation, `minimal` dropped for 5.6). Approval: **`on-failure` REMOVED** (not just deprecated), new **`writes`** app-approval mode. Commands: **`codex plugin install` -> `codex plugin add`** + marketplace, remote plugins on by default, **new `codex remote-control pair`** (Codex Remote GA 2026-06-25), MCP auth elicitation default-on. Config: **`memories` moved to its own `[memories]` table**; documented the much wider schema (`[agents]`, `default_permissions`, `[permissions.workspace.*]`, `[tui]`, `[apps]`, `[projects]`, etc.). Telemetry: `[otel] metrics_exporter="statsig"` default (metrics not fully off). Rate limits: added the OFFICIAL 2026-06-26..29 abuse/fraud incident alongside the community drain reports. Bedrock gained GPT-5.6 + `max` (2026-07-08). | 2026-07-14 research pass vs github.com/openai/codex releases 0.143/0.144, developers.openai.com/codex config-reference + config-sample, status.openai.com incident | stale gpt-5.5-default + on-failure-deprecated framing |
| 2026-06-26 | **Major expansion from review-stub to full config/security/ecosystem reference.** Added: command surface table (`codex exec`/`e`, `resume`, `mcp`/`mcp-server`, `plugin`, `features`, `exec-server`); sandbox modes; approval modes incl. `--dangerously-bypass-approvals-and-sandbox`/`--yolo` (= Claude `--dangerously-skip-permissions`) + supply-chain security note; full `config.toml` (locations/precedence/keys/`[features]`/`[permissions]`/`requirements.toml`/project-ignored keys); profiles (0.134 breaking change); telemetry off (`[analytics] enabled=false` + `[otel]`); AGENTS.md discovery (= CLAUDE.md); MCP detail; "no custom tool schemas"; **Codex<->Claude Code concept map** (hooks/skills/subagents/plugins/memories all exist, custom tools do not); reasoning-effort cost table; rate limits (5h+weekly, token-based, 2026-06-16 drain, API-key bypass). | research subagents vs developers.openai.com/codex + github.com/openai/codex (2026-06-26); CLI 0.142.0 ground-truth | review-only framing of the prior stub |
| 2026-06-24 | Initial stub: install, auth, `codex exec` review patterns, review subcommand, models, GPT-5.x critique prompting, rate-limit basics. | two Sonnet research subagents + installed CLI v0.142.0 | - |
</codex_cli_reference>
