---
type: core
title: "Custom Subagents"
status: approved
summary: "This directory holds custom subagent definitions."
created: 2026-05-13 12:08
updated: 2026-09-23 13:30
owner: Šimon Hradní
client: ~
path: kernel/agents/README.md
tags: [readme]
version: "1.0.0"
release: latest
---

# Custom Subagents

This directory holds custom subagent definitions. Files here are auto-discovered by Claude Code and made available as subagent types you can dispatch via the `Agent` tool.

## Included agents

The kernel ships one agent in this directory:

- **`research-analyst`** - focused single-topic lookup returning a self-contained verdict inline. Every claim explained, abbreviations defined, key findings linked. For quick research, not deep multi-source investigation.

Prompt engineering, prompt evaluation, and external skill admission live together in the separately installed `taste-ai-quality-kit` plugin. This prevents a global agent from carrying stale model advice or silently bypassing the user-maintained `_CONTEXT/llms` reference.

Built-in subagents (`general-purpose`, `Explore`, `Plan`) cover the most common needs.

## When to add a custom subagent

Add a custom agent here only when you need:
- A specialized persona that's reused across many sessions (e.g. a code reviewer with a specific style guide)
- A task that benefits from a stable system prompt + tightly scoped tools
- Skill bundling (custom agents can list `skills:` in frontmatter; built-in agents cannot)

## Format

A subagent file is a markdown file with YAML frontmatter:

```markdown
---
name: my-agent
description: One-line description shown in agent picker.
tools:           # Optional. Defaults to all available.
  - Read
  - Glob
  - Grep
  - WebSearch
skills:          # Optional. Skill bodies are injected into the agent's startup context.
  - some-skill
---

# System prompt for this agent

Multi-paragraph system prompt that sets the agent's behavior, tone, and constraints.
```

## Inheritance reminder

A subagent loads, like a session does:
- Your `CLAUDE.md` / `AGENTS.md` and the rules in `~/.claude/rules/` (the built-in Explore and Plan agents skip them)
- Permissions from `~/.claude/settings.json`
- Working directory
- Environment variables

A subagent does NOT see:
- The parent conversation (history, decisions made so far, files already read)
- Skills already invoked in the parent session (it can invoke skills itself; list them in `skills:` frontmatter to preload them)

When dispatching, put task-specific decisions, file paths and conventions into the prompt, and treat it as a brief for someone who just walked into the room without the conversation.
