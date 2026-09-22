---
name: using-taste-ai-quality-kit
description: Use when working in Taste with a new prompt, a prompt evaluation, or an external skill or plugin before it is admitted - route the work through the shared quality kit.
---

<purpose>
Route Taste AI quality work through one consistent workflow while keeping user-maintained LLM knowledge outside the plugin.
</purpose>

<constraints>
- Resolve `TASTE_LLM_CONTEXT_DIR` before prompt engineering or live evaluation. Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_llm_context.py`.
- If the result is `CONTEXT_NOT_READY`, stop the affected workflow. Explain which user-maintained file is missing or incomplete. Do not create, replace, or populate it.
- Never read `.env` values. Runtime scripts may consume the file without printing values.
- Never install, enable, execute, import, or connect an artifact supplied to `skill-intake`.
</constraints>

## Route

| Work state | Required next step |
|---|---|
| A prompt, agent instruction, skill, or plugin needs authoring or refinement | Use `taste-ai-quality-kit:prompt-engineer`. |
| A prompt artifact exists and needs a hygiene check or a live evaluation | Use `taste-ai-quality-kit:prompt-eval`. |
| An external skill, plugin, archive, hook bundle, or MCP configuration needs admission review | Use `taste-ai-quality-kit:skill-intake`. |

The context is deliberately not bundled here. Its model records, provider prompting notes, and decisions are user-owned operational knowledge and must be updated when the user's environment changes.

<constraints>
Do not bypass missing context by using remembered model facts, generic prompt advice, or a personal configuration. The point of this plugin is a maintained Taste operating context.
</constraints>
