---
title: "Agent judge runtime guidance"
summary: "Operational minimum for Claude Code and Codex when they are selected as prompt-eval judges."
status: draft
version: "0.2.0"
---

# Agent judge runtime guidance

Read this before selecting `claude-code/...` or `codex/...` as a prompt-eval judge. This is runtime guidance for the evaluating agent, not client-facing onboarding copy.

## Shared boundary

- An agent judge works only in a new temporary workspace. It must never run in the user's real project or receive client secrets beyond the selected evaluation input.
- The judge receives the prompt, one test input, target output and criteria. It must return JSON verdict data and preserve only the resulting transcript in the workspace-local eval archive.
- A failed agent judge remains `CALL_FAILED`. Do not silently replace it with an API model or claim a partial jury was complete.
- Agent judges are for agentic behavior, tool-use reasoning and runtime-specific failure modes. They are not a replacement for an API judge when a precise API model comparison is the goal.

## Claude Code

- The evaluator invokes `claude -p` with `--setting-sources ""`, `--strict-mcp-config`, `--no-session-persistence`, `--disable-slash-commands`, `--output-format json`, `--add-dir <temporary-workspace>`, read-only tools only (`Read`, `Grep`, `Glob`) and an explicit model where one was selected. With these flags the user's settings, instruction files, hooks, plugins and MCP servers do not reach the call.
- Authentication is the user's own Claude Code login. A logged-in subscription seat is enough and is the only credential the judge receives: the evaluator strips every provider key and other secret-looking variable from the judge's environment (only `CLAUDE_CODE_OAUTH_TOKEN`, the headless login form, is kept), so the judge is never billed to an API account and a crafted prompt cannot read keys through it. Verified 2026-09-20 with a subscription login on Linux.
- The four data blocks of the judge brief carry per-run delimiter tags; text inside them is data, and a closing tag planted in the prompt under test does not end its block.
- `--bare` must not be used: it also skips the stored login, so a user without an API key always receives "Not logged in". Measured 2026-09-20.
- Treat `is_error`, an empty result or a "Not logged in" result as `CALL_FAILED` with the exact reason the runtime returned. On an invalid key Claude Code may retry for several minutes before it fails; the evaluator waits up to five minutes per judge call.
- Managed (organisation-level) hooks cannot be disabled by flags; when one appends text to the result, the JSON verdict is still extracted from the first JSON object in the text.
- The current JSON mode returns the final result but not a complete tool-call trace. Record that limit in the judge transcript instead of inventing actions the agent did not expose.

## Codex

- The evaluator invokes `codex exec` with `--skip-git-repo-check`, a new temporary workspace, `-s workspace-write`, `--json` and `-o <temporary-final-output>`.
- The Codex sandbox stays on: the evaluator never passes the Codex flag that turns approvals and the sandbox off. If the sandbox cannot initialise, the judge fails closed and the report names the failure.
- Record the requested model ID. Under subscription authentication Codex may not prove which model actually served the turn, so do not claim model identity beyond the requested value.
- `--json` may omit tool-call events. Preserve the events it does expose and state the trace gap.
- Headless Codex startup can carry a large context and consume significant quota even for a short prompt. Use it for a reason, not as a default member of every jury.

## Before release

For each supported local runtime, verify: executable exists, noninteractive auth works, harmless JSON judge succeeds, a missing-auth state is clear, temporary workspace is removed, and transcript/report paths are written exactly once.
