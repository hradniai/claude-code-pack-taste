---
type: core
title: "_CONTEXT"
status: approved
summary: "This directory holds the user's persistent context - information about you, your work, and your preferences that Claude reads across all projects."
created: 2026-05-13 12:08
updated: 2026-09-25 10:50
owner: Šimon Hradní
client: ~
path: workspace/_CONTEXT/README.md
tags: [readme]
version: "1.0.0"
release: latest
---

# _CONTEXT

This directory holds the user's persistent context - information about you, your work, and your preferences that Claude reads across all projects.

## Files

| File | Purpose |
|------|---------|
| `user-profile.md` | Who you are, what you do, how you like to collaborate. Imported from `~/.claude/AGENTS.md` during install, so sessions load it. |
| `notes.md` | Personal brain dump for ideas, impulses, things to explore. A plain file, no automation. |
| `best-practices/` | Topic-organized notes on how *you* think about recurring problems. Distinct from generic online best practice. |
| `llms/` | Mandatory user-maintained model records, prompting rules, decisions, evaluation target, and local provider credentials for agent work. |

## How Claude uses this

During install, an `@` import of `user-profile.md` is appended to `~/.claude/AGENTS.md` (which Claude Code reads through the `CLAUDE.md` symlink), so every session loads your profile. If you move the file, update that line. Claude uses your profile to:

- Tailor explanations to your level of expertise
- Frame suggestions in your business and technical context
- Avoid wasting time explaining things you already know
- Push back appropriately given your role and authority

`best-practices/` is read on demand, not loaded every session: the install also adds one line to `~/.claude/AGENTS.md` telling Claude to check this folder for your own approach before giving generic advice on a recurring topic.

## How you should use this

- **Edit `user-profile.md` whenever something material changes** about your role, focus, tools, or preferences. Outdated profiles are worse than no profile.
- **Drop notes into `notes.md`** without overthinking format. It is a plain file: nothing reads it automatically and nothing is sent anywhere. When a note deserves research, ask Claude for it.
- **Add `best-practices/{topic}.md` files** when you've developed an approach to a recurring topic that differs from generic guidance. Crystallize, don't dump.
