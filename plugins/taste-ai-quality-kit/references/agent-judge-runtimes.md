---
title: "Agent judge runtime guidance"
summary: "Operational minimum for Claude Code and Codex when they are selected as prompt-eval judges, including where they run and what they may see."
status: draft
version: "0.3.0"
---

# Agent judge runtime guidance

Read this before selecting `claude-code/...` or `codex/...` as a prompt-eval judge. This is runtime guidance for the evaluating agent, not client-facing onboarding copy.

## Why an agent judge, and why it is fenced

An agent judge does not merely read the target output. It executes the prompt under test with real tools (shell, file reads and writes, search) and reports how an agent actually behaves under it. That measurement is only honest when the judge sees exactly the context the orchestrator chose. A judge that can wander into the user's real workspace finds guidelines, earlier reports and finished processes, and the run then measures the workspace instead of the prompt. So the default hides the machine and shows a curated workspace; the user opts into the real environment for one run when the measurement needs it.

## Isolation levels

| Level | Where it applies | What the judge can see |
|---|---|---|
| `namespace` | Linux and WSL2 with bubblewrap installed; both judges. The only Linux level. | A mount and PID namespace: system directories read-only, an empty home, only the login material (credential file read-only, a stripped disposable copy of the state file) and the judge workspace; no host process table, no host IPC. Of the machine's files, only those exist for the judge. Measured 2026-09-21 on Linux with Bash, Read, Write, Grep and Glob: a file in the real home directory does not exist for the judge. The network stays shared. |
| `sandboxed` | Claude Code on macOS. Default there. | Claude Code's own sandbox for shell commands (writes only inside the judge workspace, no reads outside the working directories, no network for commands, hard failure if the sandbox cannot start) plus permission rules that deny the file tools every user data root (`~` including its credential dot-directories, `/Users`, `/home`, `/Volumes`, `/mnt`, `/srv`, `/opt`, `/media`, `/root`). The judge workspace sits under the system temp directory, outside all of them. A deny list, not a namespace: a path on none of those roots stays readable. Documented behaviour; not yet measured on macOS. `scripts/verify_isolation.py` measures it on the user's machine. |
| `config-only` | Codex on macOS. Default there. | A fresh `CODEX_HOME` carrying only the login, the judge workspace (under the system temp directory) as working directory. No user config, skills or project instructions reach it. Codex's own sandbox confines writes to the workspace; it does not confine reads. State this limit in the report. |
| `environment` | Any runtime, only when the user asks for it for one run. | The user's real workspace (the `--workspace` directory) with the user's own settings, hooks and deny rules active; the judge runs shell commands and edits files there without asking. The choice is recorded in the report and in `history.jsonl`. |

The orchestrator passes `--isolation auto` unless the user asked otherwise; `auto` resolves to the level the machine offers. A level the runtime cannot deliver (`sandboxed` for Codex, `config-only` for Claude Code, `namespace` without bubblewrap, anything on Linux without bubblewrap because Claude Code's own Linux sandbox is bubblewrap too) fails closed as `CALL_FAILED` with the reason, never a silent downgrade and never a recorded level that did not apply.

## Curated context

`--judge-context <path>` (repeatable) copies a file or directory into the judge workspace under `context/`. This is how the orchestrator gives the judge exactly what a real run would have: a sample data file, a style guide the prompt refers to, an example input. Anything not copied does not exist for the judge at the `namespace` level. The brief itself is written to `brief.md` in the workspace as well. Ask the user in plain Czech which files the judge should have; default to none.

## Shared boundary

- Every level scrubs provider keys and other secret-looking variables from the judge's environment. The Claude Code judge keeps only `CLAUDE_CODE_OAUTH_TOKEN` (the headless login form); the Codex judge keeps nothing secret. A judge is therefore never billed to an API account and cannot read a key through its environment.
- The judge receives the prompt, one test input, the target output and the criteria in four blocks delimited by tags with a per-run random suffix. Text inside them is data; a closing tag planted in the prompt under test does not end its block.
- A failed agent judge remains `CALL_FAILED` with the runtime's own reason. Do not silently replace it with an API model or claim a partial jury was complete.
- The report lists, per judge, the isolation level that actually applied and the files the judge left in its workspace. The judge workspace is removed after the run; the `environment` level removes nothing, because that workspace is the user's.
- Agent judges are for agentic behavior, tool-use reasoning and runtime-specific failure modes. They are not a replacement for an API judge when a precise API model comparison is the goal.
- The network is shared at every level: the judge's own model calls need it, so a shell inside the judge can reach the internet too (the `sandboxed` level blocks it for commands; the namespace does not). The brief carries no secrets, which is what keeps that acceptable.

## Claude Code

- The evaluator invokes `claude -p` with `--strict-mcp-config`, `--no-session-persistence`, `--disable-slash-commands`, `--output-format json`, `--permission-mode acceptEdits`, the tools `Bash`, `Read`, `Write`, `Edit`, `Grep`, `Glob`, and an explicit model where one was selected. At every level except `environment` it also passes `--setting-sources ""`, so the user's settings, instruction files, hooks and plugins do not reach the call. At the `environment` level those stay active on purpose: they are the user's protection inside the real workspace.
- Authentication is the user's own Claude Code login. Inside the namespace the credential file is bound read-only and the state file is a disposable copy. `--bare` must not be used: it also skips the stored login, so a user without an API key always receives "Not logged in". Measured 2026-09-20.
- Treat `is_error`, an empty result or a "Not logged in" result as `CALL_FAILED` with the exact reason. On an invalid key Claude Code may retry for several minutes before it fails; the evaluator waits up to five minutes per judge call.
- Managed (organisation-level) settings of the host cannot be disabled by flags. The namespace masks `/etc/claude-code`; at other levels a managed hook may append text to the result, and the JSON verdict is still extracted from the first JSON object in it.
- The current JSON mode returns the final result but not a complete tool-call trace. Record that limit in the judge transcript instead of inventing actions the agent did not expose.

## Codex

- The evaluator invokes `codex exec` with `--skip-git-repo-check`, the judge workspace as `-C`, `-s workspace-write`, `--json` and `-o <final-output>`. Inside the namespace the final-output file sits in the judge workspace; at the `environment` level it goes to a scratch directory so nothing lands in the user's project.
- The Codex sandbox stays on: the evaluator never passes the Codex flag that turns approvals and the sandbox off. If the sandbox cannot initialise, the judge fails closed and the report names the failure.
- Record the requested model ID. Under subscription authentication Codex may not prove which model actually served the turn, so do not claim model identity beyond the requested value.
- `--json` may omit tool-call events. Preserve the events it does expose and state the trace gap. The real failure reason (usage limit, authentication) travels as an `error` event on stdout and is what the report carries.
- Headless Codex startup can carry a large context and consume significant quota even for a short prompt. Use it for a reason, not as a default member of every jury.

## Before release

For each supported local runtime, verify: executable exists, noninteractive auth works, harmless JSON judge succeeds, a missing-auth state is clear, the judge workspace is removed, and transcript and report paths are written exactly once. On a new machine, run `scripts/verify_isolation.py` once and keep its output with the release notes.
