---
type: core
title: "Rules"
status: approved
summary: "Files in this directory are auto-loaded into every Claude Code session as system context."
created: 2026-06-13 21:07
updated: 2026-09-25 10:50
owner: Šimon Hradní
client: ~
path: kernel/rules/README.md
tags: [readme]
version: "1.0.0"
release: latest
---

# Rules

Files in this directory are auto-loaded into every Claude Code session as system context. They define how Claude behaves across all projects.

## What's bundled

Four rules ship here:

| File | Purpose |
|------|---------|
| `documentation-standard.md` | XML+Markdown format conventions; AGENTS.md/CLAUDE.md/README/WORKSTATE rules |
| `respect-denies.md` | Behavior when permission engine blocks a command - never bypass, inform user |
| `subagent-rules.md` | When to use subagents, which type to pick, inheritance limits, dispatch quality |
| `language.md` | Which language to use (English by default for system files; Czech for chat and deliverables) and how to write native Czech. Banned AI calques, typography, style rules. |

The frontmatter standard (unified YAML frontmatter for every markdown artifact - closed type buckets, predefined tags) is not a rule: it lives in `~/.claude/reference/frontmatter-standard.md` and is read on demand, so it does not cost context in every session.

## Adding your own rules

Drop a new `.md` file in this directory. It will be auto-loaded.

Conventions for new rules:
- Wrap content in a single XML tag (e.g. `<my_rule>` ... `</my_rule>`) - helps Claude treat it as a coherent block
- Lead with the rule's purpose; finish with rationale or example
- Keep under ~3 KB per file unless the topic genuinely needs more
- Test by starting a new Claude session and asking about your rule - if Claude can't recall it, the rule may need to be more prominent

## Removing bundled rules

Delete the file. Rules are loose-coupled - removing one doesn't break the others. Be aware:
- Removing `respect-denies.md` may make Claude attempt to bypass denies with clever workarounds
- Removing `documentation-standard.md` may regress doc quality and lose AGENTS.md/CLAUDE.md convention
- Removing `subagent-rules.md` may regress subagent dispatch (thin briefs, raw research results in the main context)
- Removing `language.md` loses language routing (Claude may write system files in Czech) and lets Czech output drift toward translated-English style

## Custom rules vs. project-level

Rules here apply globally. For project-specific rules (e.g. "this project uses Vue, not React"), put them in the project's `AGENTS.md` instead.
