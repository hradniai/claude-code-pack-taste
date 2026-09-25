---
type: notes
title: "Prompting Claude - Quick Reference"
status: approved
summary: "Claude Code uses Anthropic's Claude models (Opus / Sonnet / Haiku)."
created: 2026-05-13 12:08
updated: 2026-09-25 10:50
owner: Šimon Hradní
client: ~
path: docs/prompting-claude.md
tags: [note]
version: "1.0.0"
release: latest
---

# Prompting Claude - Quick Reference

Claude Code uses Anthropic's Claude models (Opus / Sonnet / Haiku). They have specific preferences that differ from OpenAI / Gemini / open-weight models. This guide covers what matters for daily Claude Code work.

> Model-specific details: see `_CONTEXT/llms/` (dated, user-maintained). This page covers prompting habits that do not depend on a model version, based on Anthropic's prompting documentation and field experience.

## The five things that matter most

### 1. Use XML tags for structure

Claude is **trained** on XML tags - they're not just formatting, they're a parsing primitive. Tags are how Claude separates your instructions from your data.

```markdown
<purpose>
Extract product info from the input. Return JSON.
</purpose>

<input>
{{the actual product text}}
</input>

<constraints>
- Use null for missing values, never fabricate
- Maximum 5 categories per product
</constraints>

<output_format>
Return ONLY valid JSON. No commentary.
</output_format>
```

Common tags: `<purpose>`, `<input>`, `<context>`, `<constraints>`, `<output_format>`, `<examples>`, `<example>`, `<system>`, `<task>`. Pick names that fit your use case - Claude generalizes from any sensible XML.

### 2. Lead with purpose, not role

Don't:
```markdown
<role>You are a senior data engineer with 15 years of experience...</role>
```

Do:
```markdown
<purpose>
Extract structured product data from messy e-commerce text.
Output feeds a production pricing system, so accuracy matters more than coverage.
</purpose>
```

Goal-oriented framing outperforms role-play framing. Tell Claude what needs to happen and why; don't waste tokens on character description.

If you genuinely need persona (tone, voice), keep it short and at the end: "Write in a direct, anti-hype voice."

### 3. Explain WHY for every constraint

Motivation increases adherence. Compare:

Weak:
```markdown
- Never fabricate data.
```

Strong:
```markdown
- Never fabricate data - output feeds a production database, fabricated values cause downstream errors that take hours to debug.
```

The "why" doesn't have to be long, but it has to be there. Claude treats constrained-without-reason as soft suggestions and constrained-with-reason as hard rules.

### 4. Critical rules go at the top AND the bottom

Long prompts have a middle that gets ignored. If a rule is critical, place it once at the top of the prompt and once at the bottom (or in a closing `<critical>` block).

```markdown
<critical>
Never write to files outside the project root. This is enforced by sandboxing,
but Claude should also self-enforce - agentic loops shouldn't rely solely on
guardrails.
</critical>

[... long prompt body ...]

<critical_repeat>
Reminder: never write outside project root.
</critical_repeat>
```

This is also why CLAUDE.md / AGENTS.md is most effective when key rules are in `<cardinal_rule>` tags at the start AND a brief reminder at the end.

### 5. Be explicit about output verbosity

Claude tends toward verbose explanations when the user wants brevity. State the expectation:

```markdown
<output_format>
Return ONLY valid JSON. No prose, no preamble, no commentary, no markdown code fences.
</output_format>
```

Or for free-form:
```markdown
<output>
Reply in 1–2 sentences. No filler.
</output>
```

Default verbosity shifts between model versions (see `_CONTEXT/llms/`), so explicit instructions still help.

## Things to avoid

### Don't add "think step by step"
Current Opus and Sonnet models think adaptively (extended thinking is built in). Manually prompting "think step by step" is redundant at best, harmful at worst - it can disrupt the adaptive thinking that's already happening.

If you want to control depth through the API, use `thinking: {type: "adaptive"}` + `output_config: {effort: "low|medium|high|xhigh|max"}`. Which levels a model accepts, and whether thinking is on by default, differs per model (see `_CONTEXT/llms/model-reference-prompting.md`). Don't paste reasoning instructions into the prompt body.

### Don't over-rely on few-shot examples
Examples help on **format** (showing the exact output shape) but Claude is strong on instruction following without them. For most prompts, 0–2 well-chosen examples beat 5+ verbose ones. Each example burns tokens that could be better spent on constraints.

### Don't paste "validation scaffolding"
Phrases like:
- "Double-check your answer before responding"
- "Provide interim status updates"
- "Don't generalize"

These were workarounds for older Claude versions. On current Claude models they cause **over-validation and verbosity** - Claude does these natively now. **Re-baseline old prompts** by removing this scaffolding when you migrate.

### Don't manually structure as `Q: / A:` or `User: / Assistant:`
Claude Code's harness handles message formatting. Inside your prompts, use XML tags instead of conversational scaffolding.

## Claude Code-specific patterns

### CLAUDE.md / AGENTS.md structure
Use XML wrappers around major sections - `<purpose>`, `<persona>`, `<constraints>`, `<documentation>`. Keep total under ~5 KB per project (per ETH Zürich research, larger AGENTS.md files reduced task success).

### Skill descriptions
Skills auto-trigger based on their `description` field in YAML frontmatter. Be specific and "pushy" - Claude under-triggers by default. Bad: `"PDF processing skill."` Good: `"Use this whenever the user wants to do anything with PDF files: reading, extracting, combining, splitting, rotating, watermarking, OCR, form filling..."`

### Hooks and rules
The starter pack ships rules in `~/.claude/rules/`. They auto-load every session as system context. Each rule should:
- Wrap content in a single XML tag (e.g. `<my_rule>...</my_rule>`)
- Lead with purpose, explain WHY
- Critical rules at start AND end
- Stay under ~3 KB unless the topic genuinely needs more

### Subagent prompts
Subagents load `CLAUDE.md` and rules like a session does (the built-in Explore and Plan agents skip them), but they never see the parent conversation. Task-specific decisions, file paths and conventions go into the dispatch prompt. Treat the dispatch as a brief for someone walking into the room cold - full context, explicit constraints, output format up front.

## When you're getting bad output

Diagnostic checklist (in order):
1. **Is the goal stated, not the role?** Replace role-play with purpose.
2. **Are constraints explained with WHY?** Add motivation.
3. **Are critical rules at the top AND bottom?** Move them.
4. **Is the output format explicit?** Spell it out: "ONLY JSON", "1–2 sentences", etc.
5. **Are you using XML tags?** If you're using free-form prose, switch to structured tags.
6. **Are you over-prompting with old scaffolding?** Remove "double-check", "step by step", "interim updates" on current models.

If output is still bad after #1–6, the issue is likely your inputs or model choice - not your prompting.

## Model selection within Claude Code

| Need | Pick |
|------|------|
| Hardest reasoning, agentic coding | `opus` alias |
| Default for everyday work, code, writing | `sonnet` alias |
| High-volume, cost-sensitive, simple extractions | `haiku` alias |

The aliases follow the current model of each family; which versions those are, and how they differ, lives in `_CONTEXT/llms/model-lineup.md`.

Switch in Claude Code via `/model` slash command or set default in `~/.claude/settings.json`.

## Where to learn more

- Anthropic prompting docs: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
- Claude Code best practices: https://code.claude.com/docs/en/best-practices
- Claude Code skills: https://code.claude.com/docs/en/skills
- AGENTS.md spec (cross-tool): https://agents.md
