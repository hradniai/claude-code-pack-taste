---
type: notes
title: "Model Reference: per-model & per-endpoint prompting"
status: approved
summary: "How each specific model wants to be prompted (per-provider prompt structure, behavioral shifts) PLUS the API-call parameters per endpoint / use-case (e.g. Gemini audio transcription thinking_budget=0). No pricing (see model-lineup) and no model-agnostic techniques (see ai-prompt-guidelines)."
created: 2026-05-13 00:00
updated: 2026-09-23 13:40
owner: Šimon Hradní
client: ~
path: workspace/_CONTEXT/llms/model-reference-prompting.md
tags: [note]
version: "2.2.5"
release: latest
---

# Model Reference: per-model & per-endpoint prompting

> **Purpose: how a SPECIFIC model wants to be prompted, and exactly how to CALL its endpoints.** Read one file and know the per-model prompt structure (XML for Claude, markdown for GPT/Qwen), the behavioral shifts, and the API parameters per endpoint / use-case - so you never have to invent how an endpoint is called.
>
> This is the detail tier. The model-agnostic techniques (few-shot, CoT, ReAct, decomposition, the single-call / agent scaffolds, generic JSON discipline, generic anti-patterns) live in `ai-prompt-guidelines.md`; the model catalog + pricing lives in `model-lineup.md`. The three cross-reference and do not overlap.
>
> Claude / Anthropic specifics here come from the authoritative `claude-api` reference + live platform.claude.com docs; OpenAI and Gemini specifics from each provider's current official docs. Refreshed 2026-07-31 (adds Claude Opus 5, Gemini 3.6 Flash / 3.5 Flash-Lite, OpenAI reasoning.mode/context, Gemini 3.6 sampling-param deprecation); Anthropic part refreshed 2026-09-23 (Claude Opus 5.5 is the current default Opus).

---

## Model comparison (technical attributes - pricing is in `model-lineup.md`)

### OpenAI (current: GPT-6 Astra, September 2026)

**GPT-6 Astra** (`gpt-6-astra`, GA 2026-09-03) is the current flagship. **GPT-6 Sol** (`gpt-6-sol`) and **GPT-6 Luna** (`gpt-6-luna`) followed on 2026-09-22; unlike Astra they accept `reasoning.effort: "none"` (default `medium`), and on Chat Completions they support function calling only with `reasoning_effort` set to `none`. Source: [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol); [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) (verified 2026-09-23). GPT-5.6 (Sol/Terra/Luna) remains live below it; the table below still shows the GPT-5.5 family's technical attributes as the reference baseline. Source: [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)

| | GPT-5.5 | GPT-5.5 Pro | GPT-5.5 Instant | GPT-4.1 nano | o3 |
|---|---|---|---|---|---|
| **API ID** | `gpt-5.5` | `gpt-5.5-pro` | `chat-latest` | `gpt-4.1-nano-2025-04-14` | `o3` |
| **Context** | 1.05M | 1.05M | ~272K | 1M | 200K |
| **Max output** | 128K | 128K | 32K | 32K | 100K |
| **Reasoning** | Built-in (effort none/low/med/high/`xhigh`, default `medium`) | Built-in, higher cap | Mid-stream self-correction, lighter | No | Built-in (low/med/high) |
| **Structured output** | Native | Native | Native | Native | Native |
| **Tool calling** | Native (Responses API recommended) | Native | Native | Native | Native |
| **Prompt format** | Outcome-first, minimal scaffolding | Same | Conversational | Markdown headers | Developer messages |
| **Best for** | Previous flagship: agents, large tool surfaces, multi-step reasoning, coding | Hardest reasoning, long agentic loops | ChatGPT default, low-latency chat | Cheapest OpenAI: routing, classification, extraction | Legacy reasoning (transition to GPT-5.5) |

Lineup clarifications: **"GPT-5.5 Instant" is a ChatGPT product name, NOT a separate API model** (the API flagship is `gpt-5.5`, ChatGPT alias `chat-latest`). `gpt-5.5-pro` / `gpt-5.4-pro` are real deep-reasoning API models (Responses API only). A cheaper **GPT-5.4 family** sits below 5.5 (`gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`); OpenAI's listed replacement for `gpt-4.1-nano` is now `gpt-5.6-luna` ([deprecations](https://developers.openai.com/api/docs/deprecations), verified 2026-09-23; this line named `gpt-5.4-nano` until then). **Update: the GPT-5.6 generation (Sol/Terra/Luna) shipped 2026-07-09** and is now previous-generation; reasoning remains a mode of the model, not a separate brand. **Update 2026-08-06:** `chat-latest` was updated to a newer snapshot and may no longer point to `gpt-5.5`; pin a specific model in production. Source: [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model); [OpenAI changelog](https://developers.openai.com/api/docs/changelog)

Status / deprecation (developers.openai.com/api/docs/deprecations): GPT-4o, GPT-4.1, GPT-4.1 mini, o3, o4-mini **retired from ChatGPT 2026-02-13**; API stays live with sunsets - **`gpt-4.1-nano` deprecates 2026-10-23** (-> `gpt-5.6-luna`), **`o3-mini` / `o4-mini` 2026-10-23** (-> `gpt-5.6-sol` / `gpt-5.6-terra`), **`o3` 2026-12-11** (-> `gpt-5.6-sol`; replacements per [deprecations](https://developers.openai.com/api/docs/deprecations), verified 2026-09-23). Base `gpt-4.1` / `gpt-4.1-mini` have no confirmed API sunset yet.

### Anthropic / Claude (current: Sonnet 5 + Opus 5.5, September 2026)

From the authoritative `claude-api` reference + live platform.claude.com docs (2026-07-31; Opus 5.5 facts 2026-09-23). **Claude Opus 5.5** (`claude-opus-5-5`, GA 2026-09-22) is now the current/default Opus - the [models overview](https://platform.claude.com/docs/en/models/overview) says to start with it for most workloads - and **Claude Opus 5** (`claude-opus-5`, GA 2026-07-24) is previous-gen, still Active. **Claude Sonnet 5 is the current/default Sonnet** (GA); **Claude Fable 5.1 is the newest Fable model** (above Opus tier) but is **disabled by policy - see `model-lineup.md`**. Source: [Claude Platform release notes](https://platform.claude.com/docs/en/release-notes/overview)

| | Claude Fable 5 | Claude Opus 5.5 | Claude Opus 5 | Claude Opus 4.8 | Claude Opus 4.7 | Claude Sonnet 5 | Claude Haiku 4.5 |
|---|---|---|---|---|---|---|---|
| **API ID** | `claude-fable-5` | `claude-opus-5-5` | `claude-opus-5` | `claude-opus-4-8` | `claude-opus-4-7` | `claude-sonnet-5` | `claude-haiku-4-5` |
| **Context** | 1M | 1M | 1M | 1M | 1M | 1M | 200K |
| **Max output** | 128K | 128K sync; 300K Batches (beta) | 128K sync; 300K Batches | 128K | 128K | 128K | 64K |
| **Reasoning** | Adaptive ALWAYS on (omit the param; `{type:"disabled"}` 400s) | Adaptive ALWAYS on (`{type:"disabled"}` and `{type:"enabled", budget_tokens}` 400); effort default **`medium`** | ON by default; `{type:"disabled"}` 400 with xhigh/max (allowed only <= `high`); effort low->max | Adaptive only (effort low->`xhigh`->`max`), default OFF | Adaptive only (effort low->`xhigh`->`max`), default OFF | Adaptive, ON by default (effort low->`xhigh`->`max`, default `high`) | None (no extended thinking, no effort) |
| **Sampling** | `temperature`/`top_p`/`top_k` -> 400, omit | -> 400, omit | -> 400, omit | -> 400, omit | -> 400, omit | non-default -> 400, omit | Standard |
| **Structured output** | Native (`output_config.format`) | Native | Native | Native | Native | Native | Native |
| **Tool calling** | Native | Native; forced `tool_choice` (`any` / `tool`) -> 400 | Native | Native | Native | Native | Native |
| **Prompt format** | XML tags | XML tags | XML tags | XML tags | XML tags | XML tags | XML tags |
| **Best for** | Hardest reasoning + longest-horizon agentic (disabled by policy) | **Current default Opus:** long-running agentic coding + knowledge work; at `medium` matched or beat Opus 5 at `high` in Anthropic's testing | Previous default Opus (superseded by 5.5): hardest long-horizon agentic, self-verifies work, delegates to subagents readily | Previous-gen Opus, still fully supported | Previous-gen Opus, fully supported | Current default Sonnet: near-Opus coding/agentic at Sonnet cost; best value | Real-time, high-volume, cost-sensitive |

**Claude Opus 5.5** (`claude-opus-5-5`) is now the current/default Opus (GA 2026-09-22); Opus 5 and Opus 4.8 are previous-gen, still fully supported. Opus 4.6 (`claude-opus-4-6`) and Sonnet 4.6 (`claude-sonnet-4-6`) are also previous-gen, still supported. Aliases: bare `opus` -> current Opus (5.5 in Claude Code v2.1.280+, per [Claude Code model config](https://code.claude.com/docs/en/model-config)), bare `sonnet` -> current Sonnet (5); on Bedrock/Vertex/Foundry specify the full ID. `claude-opus-4-1` **retired 2026-08-05** on the Claude API (requests there now error; Anthropic's listed replacement is `claude-opus-4-8`, per the [deprecations page](https://platform.claude.com/docs/en/about-claude/model-deprecations), verified 2026-09-23); `claude-opus-4-0` / `claude-sonnet-4-0` retired on the Claude API 2026-06-15, though the [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) still lists Opus 4.1 and Sonnet 4 on Bedrock and Google Cloud and Opus 4 on Google Cloud. Verify dates via the `claude-api` migration guide / `platform.claude.com` before quoting to a client.

New in Opus 5: prompt cache minimum **512 tokens** (down from 1,024 on Opus 4.8). Beta features: mid-conversation tool changes (header `mid-conversation-tool-changes-2026-07-01`) lets you add/remove tools between turns while preserving the prompt cache; server-side fallbacks now accept `"default"` mode (header `server-side-fallback-2026-07-01`, supersedes the June header that only accepted explicit model lists).

### Google Gemini (Nov 2025 - Sep 2026)

| | Gemini 3.8 Flash | Gemini 3.1 Pro | Gemini 3.5 Flash | Gemini 3 Flash | Gemini 3.1 Flash-Lite | Gemini 3.6 Flash | Gemini 3.5 Flash-Lite | Gemini 3.7 Flash |
|---|---|---|---|---|---|---|---|---|
| **API ID** | `gemini-3.8-flash` | `gemini-3.1-pro-preview` | `gemini-3.5-flash` (alias `gemini-flash-latest`) | `gemini-3-flash-preview` | `gemini-3.1-flash-lite` | `gemini-3.6-flash` | `gemini-3.5-flash-lite` | `gemini-3.7-flash` |
| **Context** | 1M | 1M | 1M | 1M | 1M | 1M | 1M | 1M |
| **Max output** | 64K | 65K | 65K | 64K | 64K | 64K | 64K | 64K |
| **Reasoning** | `thinking_level` low/med/high (default medium; no minimal) | `thinking_level` low/med/high (default high) | `thinking_level` minimal/low/med/high (default medium) | `thinking_level` minimal/low/med/high (default high) | `thinking_level` minimal/low/med/high (default minimal) | `thinking_level` minimal/low/med/high (default medium) | `thinking_level` | `thinking_level` low/med/high only, no minimal (default medium) |
| **Structured output** | Native | Native (`responseSchema` / Interactions `response_format`) | Native | Native | Native | Native | Native | Native |
| **Tool calling** | Native | Native (`functionDeclarations`; modes auto/any/none/`validated`) | Native | Native | Native | Native; Computer Use built-in | Native | Native |
| **Prompt format** | Markdown / plain text | Markdown / plain text | Markdown / plain text | Markdown / plain text | Markdown / plain text | Markdown / plain text | Markdown / plain text | Markdown / plain text |
| **Status** | **GA 2026-09-02**; current flagship Flash; `temperature`/`top_p`/`top_k` deprecated | **Still Preview** (no GA) as of June 2026 | **GA 2026-05-19**, free tier (rate-limited) | Preview, free tier | **GA 2026-05-07**, 340 tok/s | **GA 2026-07-21**; being superseded by 3.7 Flash; `temperature`/`top_p`/`top_k` deprecated | **GA 2026-07-21**; low-latency subagent tier; `temperature`/`top_p`/`top_k` deprecated | **GA 2026-08-13**; previous flagship Flash; `temperature`/`top_p`/`top_k` deprecated |

Free-tier change (2026-04-01): Pro-tier models (3.1 Pro, 3 Pro) are paid-only. Flash tiers keep a reduced free tier. **Deep Think** (latest: Gemini 3.1 Deep Think on 3.1 Pro) is a reasoning MODE, not a model ID - early-access API only.

> **The Gemini 2.x family is BANNED** (2026-08-03). Never name, recommend or benchmark against a `gemini-2.5-*` / `gemini-2.0-*` model. Where a legacy API parameter below is described as belonging to that generation, that is an API fact about the parameter, not a licence to use those models.

> **Gemini 3.7 Flash** (`gemini-3.7-flash`) is the previous flagship Flash model (GA **2026-08-13**, replacing Gemini 3.6 Flash), with introductory pricing through 2026-12-31; focused improvements in software engineering, web development, and agentic workflows. Full API attributes are confirmed and folded into the table above: 1M context, 64K max output, `thinking_level` low/med/high only (default medium, no `minimal`), `temperature`/`top_p`/`top_k` deprecated. Source: [Google's Gemini 3.8 Flash guide](https://ai.google.dev/gemini-api/docs/latest-model)

> **Gemini 3.8 Flash** (`gemini-3.8-flash`) is the current flagship Flash model (GA **2026-09-02**), replacing 3.7 Flash for long-horizon software engineering, autonomous agents, and complex enterprise workflows. It has 1M context, 64K max output, `thinking_level` low/medium/high (default medium; `minimal` errors), and requires omitting `temperature`/`top_p`/`top_k`, `thinking_budget`, and `candidate_count`. Prefer server-side `previous_interaction_id` for multi-turn sessions; do not prefill model turns. Source: [Google's Gemini 3.8 Flash guide](https://ai.google.dev/gemini-api/docs/latest-model)

### Perplexity Sonar (search-augmented) & Qwen 3.5/3.6 (self-hosted)

Perplexity models (`sonar`, `sonar-pro`, `sonar-reasoning-pro`, `sonar-deep-research`) retrieve live web sources and answer with citations - a different category from pure generation. Qwen 3.5/3.6 (Apache 2.0, self-hostable via vLLM) range from 0.8B edge models to a 397B-A17B flagship. Both are detailed in their per-model prompting sections below; their pricing/IDs are in `model-lineup.md`.

---

## Per-model prompting guide

### OpenAI GPT-5.5 / 5.5 Pro

**Prompt structure:** outcome-first. Describe what good looks like, success criteria, evidence rules, output shape. Avoid step-by-step process unless the path matters.
```markdown
# Goal
Decide whether the supplied invoice should be auto-approved.
# Success criteria
- Approve only if total <= budget AND vendor is on the approved list.
- If any required field is missing or ambiguous, return REVIEW with the reason.
# Evidence
Cite the exact field values you used.
# Output
JSON: { "decision": "APPROVE | REVIEW | REJECT", "reasoning": "...", "fields_used": {...} }
```
- **Re-baseline from scratch** - do not treat as a drop-in for older models. Official: "start with the smallest prompt that preserves the product contract, then tune reasoning effort, verbosity, tool descriptions, and output format against representative examples."
- Remove "think step by step", "double-check", "be thorough" - done natively.
- `reasoning.effort`: `none / low / medium (default) / high / xhigh`. Start `medium`; higher is NOT automatically better (it can overthink and regress with conflicting instructions). A last-mile tuning knob, not the primary quality lever.
- `text.verbosity`: `low / medium (default) / high`. `low` is the better starting point for concise production output.
- **Use the Responses API**, not Chat Completions. Passing `previous_response_id` lifted Tau-Bench Retail 73.9% -> 78.2% on its own (reasoning traces persist, saving CoT tokens).
- Newly-documented techniques: eagerness/persistence controls (lower effort + fixed tool-call budget for less; persistence directive for more); self-reflection rubric ("develop a 5-7 category rubric, evaluate before responding"); verification loop / completeness contract / empty-result recovery; phase parameter (`commentary` vs `final_answer`); constraint-language discipline (reserve ALWAYS/NEVER/MUST for real safety rails); separate personality from collaboration style.

### OpenAI GPT-5.6 (Sol / Terra / Luna)
> Previous flagship generation (GA 2026-07-09). Same prompt structure and Responses-API surface as GPT-5.5 above - outcome-first, minimal scaffolding, `previous_response_id` to persist reasoning.
- **Effort ladder changed - re-tune, do not port GPT-5.5 effort values.** OpenAI states there is NO exact GPT-5.5 -> 5.6 effort mapping; re-test a familiar task starting one level LOWER. `minimal` is gone on 5.6; levels are low / medium (default) / high / xhigh / **max** / **ultra**. `ultra` triggers automatic multi-agent delegation (spawns sub-agents) - reserve it, it is not just "deeper thinking".
- Pick the tier by task, not reflex: `sol` for the hardest reasoning/coding, `terra` for balanced/most work, `luna` for cheap high-volume. The name is a durable tier that can advance across generations, so pin the full ID (`gpt-5.6-sol`) in production.
- Caching nuance (5.6+ only): a cache-WRITE now costs ~1.25x uncached input (reads still ~90% off), so short-lived prefixes are less worth caching than on 5.5. See `model-lineup.md`.

### OpenAI GPT-6 Astra
> Current flagship, GA 2026-09-03. Use the Responses API for tools; it supports the GPT-5.6 capability set plus async tools, mid-turn steering, and mid-conversation `configuration_update` items for changing reasoning effort without breaking the cached prefix.
- Migrate `none` or `minimal` effort to `low`: Astra does not support `none`. Remove `temperature`, `top_p`, `top_logprobs`, and Chat Completions `logprobs`.
- Astra can ask for clarification more readily, format output heavily, delegate less than desired, and test more broadly than a small task needs. State the desired autonomy, response shape, delegation triggers, and test scope explicitly.
- Source: [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model); [OpenAI changelog](https://developers.openai.com/api/docs/changelog)

### OpenAI GPT-4.1 / 4.1 mini / 4.1 nano
> Status: retired from ChatGPT 2026-02-13; API live. `gpt-4.1-nano` deprecates 2026-10-23 (-> `gpt-5.6-luna`, per the OpenAI deprecations page 2026-09-23). New work targets GPT-5.x unless cost-constrained.

Markdown headers (`# Purpose / # Instructions / # Constraints / # Examples / # Output Format`). `# Purpose` > `# Role`. Few-shot works very well (3-5). Prompt caching automatic - static content at top, dynamic at bottom. `temperature: 0` for deterministic tasks. **Tends to wrap JSON in markdown - instruct against it explicitly.** n8n: native nodes support structured output; for nano classification `responseFormat: "json_object"` is enough.

### OpenAI o3 / o4-mini (reasoning)
> Status: o4-mini retired from ChatGPT; o3 still toggle-accessible. API sunsets: o3 2026-12-11, o3-mini/o4-mini 2026-10-23 -> GPT-5.x. Prefer GPT-5.5 with `reasoning.effort: high`/`xhigh` for new builds.

Minimal, goal-oriented prompts; use the `developer` role not `system`. **Simpler is better** - treat as a senior colleague who needs a goal. Do NOT add "think step by step" (built in, hurts). Few-shot often counterproductive - remove. No `temperature` / `top_p`. Control depth via `reasoning.effort`.

### Anthropic Claude (Fable 5 / Opus 5.5 / Opus 5 / Opus 4.8 / 4.7 / Sonnet 5 / Sonnet 4.6)

**Prompt structure:** XML tags.
```markdown
<purpose>Extract structured product data with high accuracy. Return clean JSON matching the schema.</purpose>
<input>{{product_text}}</input>
<constraints>
- Use null for missing values. Never fabricate.
- Preserve original language of product names. Max 5 categories.
</constraints>
<examples><example>
Input: "iPhone 15 Pro, 128GB, vesmirne cerna, 29 990 Kc"
Output: {"name":"iPhone 15 Pro","storage":"128GB","color":"vesmirne cerna","price":29990,"currency":"CZK"}
</example></examples>
<output_format>Return ONLY valid JSON matching the schema. No other text.</output_format>
<constraints>Repeat the critical constraints here (top AND bottom).</constraints>
```

**Core tips (all current Claude):**
- XML tags are Claude's primary structuring mechanism - trained on them.
- Anthropic's priority order: **clarity first, examples second, identity/role third.** Don't skip `<purpose>`.
- **Explain WHY** behind rules ("Never fabricate - output feeds a production database" beats "Never fabricate").
- Constraints in the middle get ignored - put them **top AND bottom**.
- Claude trends verbose - explicit "ONLY [format], no other text" helps.
- **Prefill (starting the assistant turn with `{`) returns 400** on all current models - use `output_config.format` / `messages.parse()` instead.
- Extended thinking is **adaptive only** on the frontier: `thinking:{type:"adaptive"}` + `output_config.effort`. Do NOT set `budget_tokens` (400 on Fable 5 / Opus 4.7 / 4.8; deprecated on 4.6 / Sonnet 4.6). Do NOT set `temperature`/`top_p`/`top_k` on Fable 5 / Opus 4.7 / 4.8 (400).
- **Re-baseline old prompts (the single biggest change):** remove `"double-check before returning"`, `"give interim status updates"`, `"don't generalize"`, `"think step by step"` - the model does this natively; leaving them in causes verbosity and over-validation.
- **Avoid aggressive CAPS language** ("CRITICAL: You MUST use this tool") - it overtriggers on 4.5/4.6+; calm positive framing ("Use this tool when...") is better.

**Opus 4.7 behavioral shifts (baseline for 4.8):** more literal instruction-following (won't silently generalize); verbosity calibrates to task complexity (instruct length explicitly if you depend on it); more direct/opinionated tone, fewer emoji; `effort` matters more than any prior Opus (use `xhigh` for coding/agentic, min `high` for intelligence-sensitive; at `xhigh`/`max` set `max_tokens` >= 64K); uses tools / subagents less by default (add explicit "when to use" triggers); persistent cream/serif design house style.

**Opus 4.8 specifics (previous-gen, still supported):** same request surface as 4.7. **Narrates MORE** (remove forced-progress scaffolding; add a silence-default if a coding agent is too chatty). **More deliberate - asks more often** (add "for minor choices pick a reasonable option and note it; ask first only for scope changes / destructive actions"). **Under-reaches for search / subagents / file-memory / custom tools** - steer with explicit triggers in the system prompt AND each tool's own `description`. Warmer, less hedged writing (re-evaluate style prompts added to counter 4.7). **Mid-conversation system messages (4.8 only):** append `{"role":"system",...}` to `messages[]` to inject operator context mid-session without invalidating the prompt cache.

**Opus 5.5 (current default Opus, GA 2026-09-22):** four breaking changes versus Opus 5. (1) Thinking is **always on**: `thinking: {"type": "disabled"}` or `{"type": "enabled", "budget_tokens": N}` returns 400 - omit `thinking` (or send `{"type": "adaptive"}`) and lower `effort` where you used to disable thinking. (2) **Forced tool use returns 400** (`tool_choice` `any` / `tool`) - keep `auto` and use strict tool use or structured outputs; to make it call a tool, say in the prompt when the tool applies. (3) Thinking blocks are tied to the model and the conversation - pass them back unmodified and select content blocks by `type`, not position. (4) On the Claude API and Google Cloud the old `computer_20251124` tool is rejected - use the `computer_toolset_20260801` toolset. Text between tool calls now arrives in `thinking` blocks, empty at the default `display: "omitted"`, so a UI that streams progress goes quiet until it sets `display`. **Effort defaults to `medium`** (Opus 5: `high`) and the model thinks more per turn at a given level, so set `effort` explicitly, re-run your effort sweep instead of carrying the Opus 5 value over, reserve `xhigh` / `max` for measured gains, and leave `max_tokens` room for thinking. In Claude Code it starts at `medium` too, and a top-level `effortLevel` in the user settings file does not apply to it (choose a level with `/effort` or the `/model` picker). Prompt cache minimum 512 tokens. Sources: [What's new in Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5); [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5); [Claude Code model config](https://code.claude.com/docs/en/model-config) (all verified 2026-09-23)

**Opus 5 (previous default Opus, GA 2026-07-24; superseded by Opus 5.5 on 2026-09-22, still Active):** thinking is **ON by default** - omitting `thinking` runs adaptive (unlike Opus 4.8 where omitting meant OFF). `thinking: {"type": "disabled"}` returns **400 when combined with effort `xhigh` or `max`** - set effort to `high` or below if you need thinking off. `max_tokens` budget now covers thinking + response text together; revisit on migration from 4.8. Behavioral shifts versus 4.8: default responses run **longer** (add explicit length constraints if needed); narrates more in agentic sessions (add a silence-default if too chatty); delegates to subagents more readily; **self-verifies work without being told to** - remove any "include a final verification step" or "use a subagent to verify" instructions from prompts ported from 4.8, as they cause over-verification. Knowledge cutoff: May 2026. Source: platform.claude.com/docs/en/about-claude/models/whats-new-opus-5

**Claude Fable 5 (disabled by policy - reference only):** thinking always on (omit the param); raw chain of thought never returned (read `display:"summarized"`); single hard-task requests can run many minutes; handle `stop_reason:"refusal"` before reading content + opt into server-side `fallbacks`; requires 30-day retention. **Fable 5.1** (`claude-fable-5-1`, GA 2026-09-01) succeeds it and remains disabled by the same policy: it retains always-on adaptive thinking, but `tool_choice: "any"` and `"tool"` return 400; use `auto`/`none` or strict tool use/structured outputs. Source: [Claude Platform release notes](https://platform.claude.com/docs/en/release-notes/overview)

**Sonnet 5 (current default Sonnet):** near-Opus quality on coding + agentic at Sonnet cost, 1M context. **Adaptive thinking ON by default** (omitting `thinking` runs adaptive - different from 4.6); non-default `temperature`/`top_p`/`top_k` -> 400 (omit); `effort` defaults to `high`, supports `xhigh`. New tokenizer -> ~30% more tokens for the same text than 4.6 (re-baseline `max_tokens` + cost). More literal instruction-following - state scope explicitly ("apply to every section, not just the first"). High-res vision (2576px). Recommended default for agents with 5+ tools; escalate to Opus 5.5 only for the hardest work.

**Sonnet 4.6 (previous-gen):** still supported, 1M context, best value in that tier. Adaptive thinking recommended (but OFF when `thinking` omitted), sampling params allowed, effort low/medium/high/max. More concise than 4.5 - may skip post-tool summaries (ask if you want one).

### Google Gemini 3 / 3.1

**Prompt structure:** Markdown or plain text, no strong preference.
- **Direct, concise prompts.** Gemini 3 responds best to clear instructions; verbose prompt engineering and hand-written CoT are LESS necessary - `thinking_level: high` replaces hand-crafted CoT.
- **Temperature handling:** For Gemini 3.1 Pro / 3.5 Flash / 3 Flash / 3.1 Flash-Lite, keep temperature at the default 1.0 - lowering can cause unexpected behavior on complex tasks. **For Gemini 3.6 Flash, 3.5 Flash-Lite, and 3.7 Flash: `temperature`, `top_p`, and `top_k` are deprecated and must be stripped from all requests** - sending them returns an error. These models control generation entirely through `thinking_level`. Source: ai.google.dev/gemini-api/docs/changelog; ai.google.dev/gemini-api/docs/latest-model (verified 2026-08-31)
- **Context placement:** put the question AFTER long content ("Based on the preceding information...").
- **System-instruction hygiene:** insert the current date/year for time-sensitive tool calls; state the knowledge cutoff (January 2025 for Gemini 3).
- Gemini 3.1 Pro is concise and may guess when info is missing - mitigate with "If information is missing, return null for that field".

### Perplexity Sonar
Search-augmented (RAG), not pure generation. **Don't ask it to "search the web" - just ask the question;** Sonar retrieves sources automatically. For structured output: explicit schema + "Return ONLY JSON" + always validate (native structured output less reliable than OpenAI/Claude). `sonar-deep-research` is slow - always async; results stored ~7 days. n8n: no native node, use HTTP Request. Best for current events / fact-grounded outputs with citations; not for extraction from known documents or deterministic classification.

### Qwen 3.5 / 3.6 (self-hosted, vLLM)
Markdown headers with explicit examples. Size selection: 9B basic, 27B / 35B-A3B production, 122B-A10B best tool calling, 397B-A17B frontier (prefer Qwen3.6-27B / 3.6-35B-A3B for agentic coding). Hybrid thinking: `/think` and `/no_think` per turn. **Temperature: thinking 0.6 / top_p 0.95 / top_k 20; non-thinking 0.7 / 0.8 / 20. Never greedy decoding with thinking** (loops). 0.8B/2B default non-thinking, 4B+ default thinking. vLLM (>=0.19.0): `--enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3`. Native multimodal from 4B up; 201 languages. DashScope offers an Anthropic-API-compatible endpoint (drops into Claude Code).

---

## API call parameters per endpoint / use-case

The "read one file and know exactly how to call it" layer - the per-endpoint specifics that are easy to get wrong. (Pure model-agnostic JSON discipline is in `ai-prompt-guidelines.md`; this is the per-vendor mechanism.)

### Gemini - audio transcription (MP3 / MP4)
- **Set `thinking_budget: 0`** to disable thinking for transcription - this is a legacy-generation parameter and it must be the integer `0`. **There is no `thinking: false` / `thinking: "off"`** - the only way to switch thinking off is the numeric budget `0`. (On Gemini 3.x the parameter is `thinking_level`, not `thinking_budget`; setting both in one request returns 400.)
- **Temperature is irrelevant for transcription** - do not bother tuning it; transcription is not a creativity task.
- Audio is uploaded inline (base64) or via the Files API; audio input is tokenized at 32 tokens/second (see `model-lineup.md` for the audio-token price - it is higher than text on several models).
- For a structured transcript, set `responseMimeType: "application/json"` + `responseSchema`.

### Gemini - classification
- Use the enum response type: `response_mime_type: "text/x.enum"` + a STRING enum schema. Cleaner and cheaper than prompting for a label.

### Gemini - structured output (general)
- Legacy `generateContent`: `responseMimeType: "application/json"` + `responseSchema` in `generationConfig`. Newer Interactions API: `response_format` with `mime_type` + `schema` (or `{type:"json_object"}` for schema-free JSON). The parameter is **NOT** `responseJsonSchema`. Property order in the prompt must match the schema; very large / deeply nested schemas may be rejected.

### Gemini - reasoning (`thinking_level`)
- Gemini 3 uses `thinking_level` (NOT `thinking_budget`, which is the legacy-generation parameter). Levels: low/med/high on 3.1 Pro, 3.7 Flash, and 3.8 Flash (no `minimal`); `minimal` additionally accepted on 3.5 Flash, 3 Flash, 3.1 Flash-Lite, 3.6 Flash, and 3.5 Flash-Lite. Even `minimal` still generates and requires thought signatures.
- **Gemini 3.6 Flash accepts the full `minimal`/`low`/`medium`/`high` range** (default `medium`) - not restricted to medium/high as an earlier pass of this doc stated. **Gemini 3.7 Flash (GA 2026-08-13) accepts `low`/`medium`/`high` only** (default `medium`, no `minimal`) and, like 3.6 Flash, deprecates `temperature`/`top_p`/`top_k`. For agentic work with tool calls or multi-step reasoning, prefer `thinking_level: "medium"` or higher to avoid premature tool termination. Source: ai.google.dev/gemini-api/docs/thinking; ai.google.dev/gemini-api/docs/latest-model (both verified 2026-08-31)

### Gemini - function calling
- Modes `auto` (default) / `any` / `none` / `validated` (Preview). AUTO may skip tool calls in long agentic conversations - switch to `any` for deterministic tool use. **`thought_signature` continuity:** in stateless mode return all thought blocks exactly as received; in stateful Interactions mode (`store: true` + `previous_interaction_id`) the server manages signatures (the official SDKs handle it when you append the full model response).

### Claude - structured output & thinking
- Structured output: `output_config.format` (`{type:"json_schema", schema:{...}}`) on `messages.create()`, or `client.messages.parse()` with a Pydantic/Zod model (validates automatically). **Prefill is gone (400)** - do not start the response with `{`.
- Thinking: `thinking:{type:"adaptive"}` + `output_config:{effort:"low|medium|high|xhigh|max"}`. Default thinking display is `"omitted"` on Fable 5 / Opus 4.8 / 4.7 - set `display:"summarized"` if you surface reasoning to users. Do NOT send `budget_tokens` or sampling params on Fable 5 / Opus 4.7 / 4.8 (400).
- Web search server tool: `web_search_20260209` (built-in dynamic filtering) on Opus 4.8 / 4.7 / 4.6 + Sonnet 4.6; do NOT also declare `code_execution` alongside it. (Billing: see `model-lineup.md`.)
- Prompt caching: `cache_control:{type:"ephemeral"}` on the last stable block; verify hits via `usage.cache_read_input_tokens`.

### OpenAI - Responses API & reasoning
- Prefer the **Responses API** over Chat Completions; pass `previous_response_id` to persist reasoning traces across turns. `reasoning.effort` (none/low/medium/high/xhigh) and `text.verbosity` (low/medium/high) are the two main knobs. Structured output via the Structured Outputs API (schema with `additionalProperties:false` + all properties `required`). GPT-4.1 needs an explicit "no markdown / no code blocks" instruction for JSON.
- **`reasoning.mode`** (Responses API, GPT-5.6 only): `"standard"` (default) or `"pro"` - pro mode does more work before returning the final answer; independent of `effort` (combine `mode:"pro"` + `effort:"max"` for hardest tasks).
- **`reasoning.context`** (Responses API, GPT-5.6 only): `"auto"` / `"current_turn"` / `"all_turns"` - controls reuse of reasoning traces across multi-turn conversations; `"all_turns"` improves quality and cache efficiency. Full payload: `{"reasoning":{"effort":"max","mode":"pro","context":"all_turns"}}`. Source: developers.openai.com/api/docs/guides/reasoning

---

## Per-model JSON reliability

Prefer API-level enforcement over prompting wherever it exists.

| Provider | Reliability | Best practice |
|----------|-------------|---------------|
| OpenAI GPT-5.6 / 5.5 / GPT-4.1 | High | `responseFormat:"json_object"` or the Structured Outputs API |
| OpenAI o3 / o4-mini | High | Structured Outputs API; prompt-only less reliable |
| Claude (all current) | High | `output_config.format` / `messages.parse()`. Prefill is gone (400). XML `<output_format>` + "ONLY JSON" as backstop |
| Gemini 3.x | Medium | Enforce via API: `responseSchema` (`generateContent`) or `response_format.schema` (Interactions). NOT `responseJsonSchema`. Always validate |
| Perplexity Sonar | Lower | Schema in prompt + "ONLY JSON" - always validate |

---

## Model selection for tasks

| Task | Best model | Why |
|---|---|---|
| Simple extraction | GPT-5.6 Luna / 5.5 (low effort), Gemini 3.5 Flash / 3 Flash, Qwen 3.5-9B | Fast, cheap, reliable with schema |
| Complex extraction (OCR, messy) | GPT-5.6 Sol, Claude Sonnet 5, Gemini 3.x (document/OCR) | Better on ambiguous inputs |
| Agent (< 5 tools) | GPT-5.6 (low/med), Claude Sonnet 5 | Good tool calling, reasonable cost |
| Agent (5-20 tools) | GPT-5.6 Sol (Responses API), Claude Sonnet 5, Qwen 3.6-27B | Best tool-selection accuracy |
| Agentic coding (hardest) | GPT-6 Astra; Claude Opus 5.5 (set `effort` explicitly; default `medium`, `xhigh` / `max` only where measured); GPT-5.6 Sol / 5.5 Pro | Frontier long-horizon execution |
| Complex reasoning step | GPT-6 Astra; GPT-5.6 Sol (high/xhigh), Claude Opus 4.8 (adaptive, `xhigh`) | Built-in reasoning |
| Content generation | Claude Sonnet 5, GPT-5.6 (verbosity: medium) | Best natural-language quality |
| Localization / transcreation | Claude Opus 4.8 | Best cultural nuance |
| Real-time / web search | Perplexity sonar / sonar-pro | Only models with live retrieval + citations |
| Audio transcription | Gemini 3.5 Flash-Lite (flat $0.30/1M incl. audio) for bulk; Gemini 3.5 Flash where the transcript feeds attribution | Cheapest audio path; OpenAI's `gpt-transcribe` is ~8x dearer and returns text only, with no understanding of the audio |
| High-volume, cost-sensitive | GPT-5.6 Luna, Gemini 3.6 Flash, Gemini 3.1 Flash-Lite, Qwen 3.5-35B-A3B | Lowest cost per token; 3.6 Flash has improved token efficiency over 3.5 Flash |
| Classification | Gemini Flash-Lite (`text/x.enum`), GPT-5.4-nano / 5.6 Luna | Fastest, cheapest |
| Self-hosted production | Qwen 3.6-27B / 3.6-35B-A3B | Best open-weight for tool use + agentic coding |

(The bottom-up-and-escalate selection philosophy is out of scope here.)

---

## Per-model anti-patterns & symptom -> fix

Only the MODEL-SPECIFIC ones. The model-agnostic anti-patterns (placeholder examples, negative-only constraints, "think step by step" on reasoning models, etc.) are in `ai-prompt-guidelines.md`.

### Anti-patterns
| Anti-pattern | Fix |
|---|---|
| `temperature`/`top_p`/`top_k` on Fable 5 / Opus 4.7 / 4.8 | Remove - returns 400; steer via prompt |
| `budget_tokens` on Fable 5 / Opus 4.7 / 4.8 | Remove - 400; use `thinking:{type:"adaptive"}` + `effort` |
| `{type:"disabled"}` thinking on Fable 5 | Remove - 400; omit the `thinking` param entirely |
| `thinking: {"type": "disabled"}` with effort `xhigh` or `max` on Opus 5 | 400 - allowed only when effort is `high` or below; remove the `thinking` field to keep adaptive thinking enabled |
| Assistant prefill (`{`) on any current Claude | 400 - use `output_config.format` |
| Aggressive CAPS tool language on Claude 4.5/4.6+ | Calm positive framing ("Use this tool when...") - CAPS overtriggers |
| `thinking_budget` on Gemini 3 | Remove - it is the legacy-generation param; use `thinking_level` (both in one request = 400) |
| `thinking: false` / `"off"` for Gemini transcription | There is no off switch - set `thinking_budget: 0` (integer) |
| `temperature`/`top_p`/`top_k` on Gemini 3.6 Flash / 3.5 Flash-Lite / 3.7 Flash / 3.8 Flash | Deprecated for these models - must strip from generation config (returns error) |
| `responseJsonSchema` on Gemini | Wrong key - use `responseSchema` / `response_format.schema` |
| JSON without "no code blocks" on GPT-4.1 | GPT-4.1 wraps JSON in markdown - forbid it explicitly |
| Greedy decoding with Qwen thinking mode | Loops/repetition - use temp 0.6 / top_p 0.95 / top_k 20 |
| `reasoning.mode` / `reasoning.context` in Chat Completions API | Responses API only - not available in `/v1/chat/completions` |

### Symptom -> fix
| Symptom | Fix |
|---|---|
| Output too verbose (Opus 4.8 narrates a lot) | Silence-default: "default to silence between tool calls; write only on a find, change of direction, or blocker" |
| Claude asks too many small questions (Opus 4.8) | "For minor choices pick a reasonable option and note it; ask first only for scope / destructive actions" |
| Claude under-uses search / subagents / memory (4.8) | Explicit "when to use X" in the system prompt AND each tool's `description` |
| `refusal` stop reason on Fable 5 | Handle `stop_reason:"refusal"` before reading content; opt into server-side `fallbacks` |
| Long Gemini agent sessions break tool calling | Switch AUTO -> `any` mode |
| GPT-5.x overthinks at high effort | Lower `reasoning.effort`; it is a last-mile knob, not the quality lever |
| Opus 5 response too long / narrates too much in agentic sessions | Add explicit length constraints; add silence-default ("default to silence between tool calls; write only on a find, change of direction, or blocker") |
| Opus 5 over-verifies work (verification loops, excessive subagent spawning) | Remove "include a final verification step" / "use a subagent to verify" instructions from prompts ported from Opus 4.8 - Opus 5 self-verifies natively |

---

## Change log

| Date | Added | Source | Removed |
|------|-------|--------|---------|
| 2026-09-23 (2nd edit) | **Follow-up fixes (v2.2.5), so this file agrees with `model-lineup.md`.** `claude-opus-4-1` replacement corrected to Anthropic's listed `claude-opus-4-8` (was "migrate to `claude-opus-5`"), and "fully retired" for Opus 4 / Sonnet 4 narrowed to the Claude API. Added GPT-6 Sol and GPT-6 Luna (2026-09-22) next to GPT-6 Astra with their `none`-effort and Chat Completions function-calling rule. `gpt-4.1-nano`, `o3-mini` / `o4-mini` and `o3` replacements corrected to the GPT-5.6 models the OpenAI deprecations page now lists. | [Anthropic deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations); [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing); [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol); [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna); [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations) (all verified 2026-09-23) | "migrate to `claude-opus-5`"; `gpt-5.4-nano` / `gpt-5.5` as the listed replacements |
| 2026-09-23 | **Anthropic-only refresh (v2.2.4): Claude Opus 5.5 (`claude-opus-5-5`, GA 2026-09-22) is the current default Opus.** New Opus 5.5 column in the Claude comparison table and a dedicated prompting paragraph: thinking always on (disabled / manual budget -> 400), forced tool use -> 400, thinking blocks tied to model and conversation, `computer_20251124` rejected on the Claude API and Google Cloud, text between tool calls in `thinking` blocks, effort default `medium` with more thinking per level, Claude Code ignores a top-level user `effortLevel` for it. Opus 5 relabelled previous-gen; `opus` alias, Sonnet 5 escalation target and the hardest-agentic-coding task-picker row now point at Opus 5.5. OpenAI and Gemini untouched. | [Models overview](https://platform.claude.com/docs/en/models/overview); [What's new in Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5); [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5); [Opus 5.5 migration guide](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide); [Claude Code model config](https://code.claude.com/docs/en/model-config) (all verified 2026-09-23) | Opus 5 as "current default Opus" |
| 2026-09-11 | **Surgical refresh (v2.2.3).** Added GPT-6 Astra as the current OpenAI flagship and its prompting/API migration specifics: use Responses for tools; replace unsupported `none`/`minimal` effort with `low`; remove sampling and logprob parameters; state autonomy, formatting, delegation, and test scope explicitly. Added Gemini 3.8 Flash as current Flash: 1M context, 64K output, low/medium/high thinking with medium default, and stripped sampling/legacy-thinking parameters. Noted Claude Fable 5.1 as Fable 5's successor, still policy-disabled, with its `tool_choice` restrictions. | [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model); [OpenAI changelog](https://developers.openai.com/api/docs/changelog); [Google Gemini 3.8 Flash guide](https://ai.google.dev/gemini-api/docs/latest-model); [Gemini release notes](https://ai.google.dev/gemini-api/docs/changelog); [Claude Platform release notes](https://platform.claude.com/docs/en/release-notes/overview) | - |
| 2026-08-31 | **Surgical refresh (v2.2.2).** Verified Anthropic/OpenAI/Gemini/Qwen/Perplexity docs for deltas since the 2026-08-24 pass; only Gemini had prompting-relevant changes. (1) **Gemini 3.7 Flash API attributes confirmed** (previously "to verify"): 1M context, 64K max output, `thinking_level` low/med/high only (default medium, no `minimal`), `temperature`/`top_p`/`top_k` deprecated - added as a full column in the Gemini comparison table and resolved the pending-verification note. (2) **Correction: Gemini 3.6 Flash `thinking_level` accepts the full minimal/low/medium/high range**, not "medium/high only" as stated in the 2026-07-31/08-13 passes - the official thinking-controls table lists all four levels. (3) **Correction: Gemini 3.5 Flash also accepts `minimal`** (was previously documented as low/med/high only). Anthropic: no changes since 2026-08-24 (next release-notes entry as of this check is 2026-08-27, unrelated to prompting/thinking/sampling). OpenAI: no changes to `reasoning.effort`/`reasoning.mode`/`reasoning.context` or the Responses API since 2026-08-24 (only transcription-model deprecations and Assistants API sunset, out of this doc's scope). Qwen/Perplexity: no change to the documented vLLM flags or Sonar API surface; a new Qwen3.8-Flash-Next model exists but is out of scope (not yet tracked in `model-lineup.md`). | ai.google.dev/gemini-api/docs/thinking (verified 2026-08-31); ai.google.dev/gemini-api/docs/latest-model (verified 2026-08-31); platform.claude.com/docs/en/release-notes/overview; developers.openai.com/api/docs/changelog | - |
| 2026-08-13 | **Surgical refresh (v2.2.1).** (1) **Claude Opus 4.1 confirmed retired 2026-08-05** - updated from "retires" to "retired; API now returns error". (2) **`chat-latest` alias updated 2026-08-06** - no longer guaranteed to point to gpt-5.5; added recommendation to pin `gpt-5.6-sol` for production. (3) **Gemini 3.7 Flash GA 2026-08-13** (`gemini-3.7-flash`) - added note below Gemini table; technical API specs not yet in changelog, marked as to-verify. | platform.claude.com/docs/en/release-notes/overview (Aug 5 entry); developers.openai.com/api/docs/changelog (Aug 6 entry); ai.google.dev/gemini-api/docs/changelog (Aug 13 entry) | - |
| 2026-07-31 | **Refresh for the July 14-31 deltas (v2.2.0).** Added **Claude Opus 5** (GA 2026-07-24) as current/default Opus: new column in comparison table, dedicated Opus 5 prompting section (thinking ON by default, `{type:"disabled"}` 400 with xhigh/max, behavioral shifts - longer output, more narration, self-verifies), updated section headers + task-picker + anti-patterns. Added **Gemini 3.6 Flash** and **Gemini 3.5 Flash-Lite** (GA 2026-07-21): new columns in Gemini table; noted that `temperature`/`top_p`/`top_k` are deprecated for these models, `thinking_level` on 3.6 Flash narrows to `medium`/`high`. Added OpenAI **`reasoning.mode`** (`standard`/`pro`) and **`reasoning.context`** (`auto`/`current_turn`/`all_turns`) to Responses API section. Updated aliases (bare `opus` -> Opus 5). | platform.claude.com/docs/en/about-claude/models/overview; platform.claude.com/docs/en/about-claude/models/whats-new-opus-5; ai.google.dev/gemini-api/docs/changelog; ai.google.dev/gemini-api/docs/thinking; developers.openai.com/api/docs/guides/reasoning | - |
| 2026-07-14 | **Refresh for the lineup deltas (v2.1.0).** Added the **GPT-5.6 (Sol/Terra/Luna)** generation - new-model note above the OpenAI comparison table, a dedicated GPT-5.6 prompting subsection (re-tune effort, `minimal` gone, `max`/`ultra` added, 5.6-only cache-write), updated lineup-clarifications + task-picker + JSON-reliability rows. Added **Claude Sonnet 5** as the current default Sonnet - swapped it into the Claude comparison table (adaptive-on-by-default, non-default sampling 400s, new tokenizer, high-res vision) and split Sonnet 4.6 out as previous-gen. | 2026-07-14 research pass + live platform.claude.com / developers.openai.com | - |
| 2026-06-26 | **Restructured into a pure per-model + per-endpoint reference.** Added the new **"API call parameters per endpoint / use-case"** layer (Gemini audio transcription `thinking_budget=0` not `false`, Gemini classification `text/x.enum`, Gemini structured-output / function-calling params, Claude `output_config.format` + thinking + web-search tool, OpenAI Responses API + reasoning/verbosity). Trimmed model-comparison tables to technical attributes (pricing moved entirely to `model-lineup.md`). Kept per-model prompting guide, per-model JSON reliability, the task-picker, and the model-specific anti-patterns. | `claude-api` skill (Anthropic, authoritative); prior research-refreshed content; official OpenAI / Gemini docs | **Pricing rows/columns** (now only in `model-lineup.md`); the two Core Principles, the single-call/agent scaffolds, the generic JSON discipline, and the generic anti-patterns / symptom->fix / pre-deploy checklist (now in `ai-prompt-guidelines.md`); the **Claude Code Skills and Cowork Plugins** sections (the Claude tooling is out of scope for this file; the Codex equivalents are in `codex-cli-reference.md`) |
| 2026-06-26 (earlier) | Merged `ai-prompt-guidelines.md` in + research-refreshed (Fable 5 / Opus 4.8, OpenAI 5.5 family, Gemini 3.5 Flash, Perplexity, Qwen). | Anthropic `claude-api` ref + provider docs | - |
| 2026-05-13 | OpenAI GPT-5.5 family, Anthropic Task Budgets / Fast Mode, Gemini 3.1 Flash-Lite GA, Qwen 3.6. | provider docs | - |
