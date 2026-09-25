---
type: notes
title: "subagent-rules"
status: approved
summary: "Guidelines for dispatching parallel subagents to handle independent research and tasks while protecting main context from information bloat."
created: 2026-05-13 12:08
updated: 2026-09-23 13:30
owner: Šimon Hradní
client: ~
path: kernel/rules/subagent-rules.md
tags: [note]
version: "1.0.0"
release: latest
---

<subagent_rules>

## When to use
Dispatch parallel subagents when 2+ subtasks are independent. Subagents protect main context from bloat. Don't force it for sequential or trivial tasks.

**Research = subagent.** Non-trivial research (web search, documentation lookup, multi-source verification) goes to a subagent: `research-analyst` for a focused single-topic lookup, `general-purpose` for broader multi-source work. Raw search results never land in the main context.

The main context must never be polluted with raw search results or fetched pages. Subagent returns maximum detail (not just a summary) so the main context can make informed decisions without re-researching.

## Inheritance - what subagents do and don't see
- **Permissions** (`settings.json` allow/deny): inherited from main session
- **Working directory**: inherited
- **Environment variables**: inherited
- **CLAUDE.md / AGENTS.md and rules in `~/.claude/rules/`**: loaded like in a session (the built-in Explore and Plan agents skip them)
- **Parent conversation**: NOT visible - no history, no decisions made so far, no files the parent already read
- **Skills**: skills already invoked in the parent are NOT carried over; a subagent can still invoke skills itself, and a custom agent can preload them with `skills:` frontmatter (built-in agents don't preload skills)

**Practical implication:** the subagent knows your CLAUDE.md and rules, but not the conversation. Task-specific decisions, file paths and conventions agreed in the conversation go into the dispatch prompt.

## Model selection
- **Haiku**: simple lookups, formatting, translations
- **Sonnet**: medium complexity - summaries, non-technical research, copy
- **Opus**: architecture, debugging, code changes, deep technical analysis

Pick the cheapest model that can handle the task.

## Prompt quality
Give maximum context - background, constraints, expected output, file paths, decisions. Subagent has NO access to parent conversation. Treat the dispatch prompt as a self-contained brief for someone who just walked into the room.

## Reporting (mandatory)
Full transparency. On errors: exact error message, what was attempted, which tool/step. Never summarize as "didn't work."

On success, report any: deviations from instructions, retry attempts, fallback strategies, assumptions made, partial failures, unexpected behaviors.

## Research output convention
- **Substantial research** (best practices, competitor analysis, technology deep-dives, multi-source verification): always save full findings to a file `{topic}-research-{YYYY-MM-DD}.md` in the project's `research/` dir. The file IS the deliverable. Return a concise verdict to the main context.
- **Smaller research** (single-topic lookup, quick verification): no file needed, but return MAXIMUM data - full details, exact quotes, specific findings, edge cases. Never just a bare summary.

</subagent_rules>
