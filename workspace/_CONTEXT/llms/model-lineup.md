---
type: notes
title: "LLM model lineup (current)"
status: approved
summary: "Model catalog + pricing reference (standard, batch, caching, per-provider surcharges) plus a price-performance snapshot ranking the providers per tier. Not auto-loaded. The prompt-engineer agent and any model-choice decision read it. How to prompt lives in the sibling files."
created: 2026-06-16 00:00
updated: 2026-08-13 20:05
owner: Šimon Hradní
client: ~
path: workspace/_CONTEXT/llms/model-lineup.md
tags: [note]
version: "1.5.0"
release: latest
---

<llm_lineup>

# LLM model lineup (current)

> **Purpose: this file is the model CATALOG and PRICING only.** It does not say how to prompt these models. For that:
> - `ai-prompt-guidelines.md` (this folder) - model-agnostic prompt-engineering techniques.
> - `model-reference-prompting.md` (this folder) - per-model / per-endpoint prompting + API parameters.
>
> NOT auto-loaded into every session. The `prompt-engineer` agent and any model-choice decision read it. Always re-verify before a production model choice and pin versioned IDs in production (aliases like `-latest` silently drift). Models are listed newest-first per provider, with a few older ones kept for reference.
>
> Anthropic, OpenAI and Gemini pricing re-verified against their official pages on **2026-08-03** (Anthropic: `platform.claude.com/docs`; OpenAI: `developers.openai.com` pricing + changelog; Gemini: `ai.google.dev` pricing + changelog + models). **No provider changed a listed price between 2026-07-31 and 2026-08-03** - both the OpenAI and the Gemini changelog have zero August entries, so the last real move is still OpenAI's cut of 2026-07-30. What the 2026-08-03 pass DID change: several models that were simply missing from the OpenAI table (the whole GPT-5 base family, `gpt-4.1` / `-mini`), the corrected "cheapest OpenAI model" claim, the new transcription models, and confirmation of items previously flagged COMMUNITY. **Perplexity still rests on the 2026-07-14 pass** - not re-verified since. Findings are tier-labelled: OFFICIAL (provider's own page), COMMUNITY (multiple aggregators agree), UNVERIFIED (could not confirm at source).

## How to read the pricing

- **Standard in / out** = pay-as-you-go price per 1M input / output tokens, real-time.
- **Batch** = the same work submitted asynchronously (you are not waiting on it). Every provider here gives **-50 %** off standard. Use it for anything offline (nightly, ingest, bulk).
- **Caching** = re-using a repeated prompt prefix. A **cache read** is far cheaper than fresh input (roughly a tenth); a **cache write** carries a small premium. Per-provider details are in each provider's surcharge block.
- **Surcharges** = the costs that are NOT per-token: web search / grounding, image generation, audio, large-context premiums. They live in a "batch, caching & surcharges" block under each provider's table - that is where the easy-to-miss money is.

There is no "always start with the cheapest model" rule here on purpose: the catalog is a price list, not a selection policy. Sometimes you need quality regardless of price.

## Price-performance snapshot (2026-08-03): is Gemini still the value leader?

**Short answer: no longer across the board.** Gemini keeps the value crown on multimodal (above all audio), on the mid tier, and below the 5,000-free-searches grounding line. OpenAI's 2026-07-30 cut took the lead in the cheap CURRENT-GENERATION text tier, where **GPT-5.6 Luna ($0.20 / $1.20) now undercuts both Gemini Flash-Lites on input and output**.

**Read the tier labels literally.** The dollar tables below are MEASURED: they are arithmetic over the official list prices in this file, nothing else. The quality ordering is NOT measured here - this pass verified prices, not benchmarks, and only two third-party index points rendered on a fetch of `artificialanalysis.ai/models` (Claude Opus 5 max-effort at 61, the top-ranked entry; GPT-5.6 Sol max at 59; the Gemini rows did not render). So: **anything below about which model is BETTER is COMMUNITY-sourced or the author's judgment, never a measured benchmark.** Run your own 20-50-sample eval before betting a production pipeline on a quality claim.

### Cost of two representative workloads

Standard tier, no caching, no batch. **Workload A** = extraction / classification, input-heavy (10,000 input + 1,000 output tokens per call). **Workload B** = generation / chat, balanced (2,000 + 2,000). Both columns show **USD per 1,000 calls**, so the numbers are directly comparable.

| Model | Provider | A: 10k in + 1k out | B: 2k in + 2k out |
|---|---|---|---|
| `gpt-5-nano` | OpenAI | **$0.90** | **$0.90** |
| `gpt-4.1-nano` | OpenAI | $1.40 | $1.00 |
| **GPT-5.6 Luna** | OpenAI | **$3.20** | **$2.80** |
| `gpt-5.4-nano` | OpenAI | $3.25 | $2.90 |
| Gemini 3.1 Flash-Lite | Google | $4.00 | $3.50 |
| `gpt-5-mini` | OpenAI | $4.50 | $4.50 |
| Gemini 3.5 Flash-Lite | Google | $5.50 | $5.60 |
| `gpt-4.1-mini` | OpenAI | $5.60 | $4.00 |
| `gpt-5.4-mini` | OpenAI | $12.00 | $10.50 |
| Claude Haiku 4.5 | Anthropic | $15.00 | $12.00 |
| **Gemini 3.6 Flash** | Google | **$22.50** | **$18.00** |
| Claude Sonnet 5 (intro, to 08-31) | Anthropic | $30.00 | $24.00 |
| GPT-5.6 Terra | OpenAI | $32.00 | $28.00 |
| Gemini 3.1 Pro (<=200K, preview) | Google | $32.00 | $28.00 |
| Claude Sonnet 5 (from 09-01) | Anthropic | $45.00 | $36.00 |
| Claude Opus 5 | Anthropic | $75.00 | $60.00 |
| GPT-5.6 Sol | OpenAI | $80.00 | $70.00 |

### What that actually means, tier by tier

- **Cheap current-generation text: OpenAI took the lead, and it is not close.** Before 2026-07-30 Luna cost $1 / $6; the 80 % cut put it at $0.20 / $1.20, which is **20 % cheaper on both input and output than Gemini 3.1 Flash-Lite** ($0.25 / $1.50) and **33 % cheaper on input, 52 % on output than Gemini 3.5 Flash-Lite** ($0.30 / $2.50). Luna is a July-2026 frontier-family tier, so this is a current-gen model beating a current-gen model, not an old model on a discount rack. [MEASURED on list prices; the claim that Luna's OUTPUT QUALITY matches a Flash-Lite is COMMUNITY only - untested here.]
- **The absolute cheapest token in this file is `gpt-5-nano` at $0.05 / $0.40**, a fifth of Gemini 3.1 Flash-Lite's input and a quarter of its output. Caveat that matters: `gpt-5-nano` is the August-2025 generation, so it is a generation behind the Flash-Lite family on capability. The file previously called `gpt-4.1-nano` the cheapest OpenAI model - that was wrong and is corrected in the OpenAI table below.
- **Mid tier: Gemini still wins on price.** Gemini 3.6 Flash ($1.50 / $7.50) is the cheapest frontier-ish workhorse; Sonnet 5 is close only while the introductory $2 / $10 lasts. **From 2026-09-01 Sonnet 5 goes to $3 / $15, which makes Gemini 3.6 Flash 50 % cheaper on input and 50 % on output.** If a Sonnet-5-based pipeline is being costed for the autumn, cost it at the September price, not today's.
- **Frontier: nobody is cheap, and Gemini's cheapest Pro is not GA.** Opus 5 ($5 / $25) is cheaper on output than GPT-5.6 Sol ($5 / $30) and, on the one third-party index that rendered, ranked above it. Gemini 3.1 Pro looks far cheaper at $2 / $12, but it is **still a `-preview` model** (IDs and prices change at GA) and it carries a >200K context tier at $4 / $18, so a long-context agentic run costs double what the headline says.
- **Audio and multimodal: Gemini wins, and this is the tier that matters for meeting and media work.** One hour of audio = 115,200 tokens at Gemini's 32 tokens/second. On **`gemini-3.5-flash-lite` (flat $0.30/1M, audio included) that is ~$0.035/hour**, ~$0.017 on batch; on `gemini-3.1-flash-lite` (audio $0.50/1M) ~$0.058/hour; on `gemini-3.5-flash` ~$0.17/hour if audio bills at the text rate [UNVERIFIED - no separate audio rate is published for 3.5 / 3.6 Flash]. OpenAI's `gpt-transcribe` is **$0.0045/minute = $0.27/hour** and returns only a transcript, with no understanding of the audio - summarizing or attributing speakers costs a second call into a text model on top. Anthropic does not accept audio input at all. Gemini also prices image and video generation, which Anthropic does not offer.
- **Search grounding flips depending on volume.** Anthropic and OpenAI both charge **$10 / 1,000** web-search calls. Gemini 3.x charges **$14 / 1,000 but gives 5,000 free prompts a month**. Under ~5,000 searches/month Gemini is free and therefore unbeatable; above it Gemini is 40 % more expensive per query than either competitor.
- **Caching changes the ranking on repeated prefixes.** Anthropic reads at 0.1x input but charges a 1.25x (5-min) or 2x (1-hour) write. OpenAI reads at 0.1x automatically, and on the GPT-5.6 family adds a ~1.25x cache-write charge that 5.5 and earlier do not have. Gemini reads cheap ($0.15/1M on 3.6 Flash) but adds **storage per hour the cache lives** ($1.00/1M/hr Flash tiers, $4.50/1M/hr Pro tiers) - on a long-lived cache that storage line, not the read line, is what shows up on the invoice.

### The practical call

Default recommendation: **keep Gemini as the default for anything multimodal, audio, long-context or batch, and for the mid-tier workhorse slot.** For high-volume cheap TEXT work (routing, classification, extraction, tagging) **GPT-5.6 Luna is now the price leader and deserves an eval against Gemini 3.1 Flash-Lite** before the next automation is wired - a 20-50-sample accuracy comparison, since the price gap is real but the quality gap is unmeasured. [AUTHOR'S JUDGMENT, built on the measured prices above, not on a benchmark anybody published.]

## Anthropic (Claude)

Pricing re-verified live on **2026-08-03** against `platform.claude.com/docs/en/about-claude/pricing` (**every rate unchanged since the 2026-07-31 pass; no new model**); deprecations and prompt-caching last read 2026-07-31, models-overview 2026-07-14. **Claude Opus 5 launched 2026-07-24.** Cache-hit (read) prices in dollars, since that is what actually lands on the invoice: Fable 5 / Mythos 5 $1.00, Opus 5 / 4.8 / 4.7 / 4.6 / 4.5 $0.50, Sonnet 5 $0.20 (intro) then $0.30 from 09-01, Sonnet 4.6 / 4.5 $0.30, Haiku 4.5 $0.10 per 1M.

| Model | API id | Context | In / Out per 1M | Use for |
|---|---|---|---|---|
| Opus 5 | `claude-opus-5` | 1M / 128K out | $5 / $25 | **Current default Opus (GA 2026-07-24).** Anthropic's own docs now lead with it for complex agentic coding + enterprise work, at the same price as Opus 4.8. Adaptive thinking; `effort` defaults to `high` on the Claude API and Claude Code. Replaces Opus 4.8 as the capability baseline; 4.8 still fully supported. [OFFICIAL - price + cache rows on `platform.claude.com/docs/en/about-claude/pricing`, verified 2026-07-31] |
| Fable 5 | `claude-fable-5` | 1M / 128K out | $10 / $50 | **CURRENTLY UNAVAILABLE / DISABLED BY POLICY - do not select.** Anthropic's most capable widely released model (hardest reasoning + long-horizon agentic), but priced above Opus and out of scope for routine automations. Thinking always on; no prefill; requires 30-day retention (no ZDR). Mythos 5 (`claude-mythos-5`) = same model, Project Glasswing invite-only. |
| Opus 4.8 | `claude-opus-4-8` | 1M / 128K out | $5 / $25 | Previous-gen Opus, still fully supported. Long-horizon agentic, knowledge work, memory. Adaptive thinking only. |
| Opus 4.7 | `claude-opus-4-7` | 1M / 128K out | $5 / $25 | Previous-gen Opus, still fully supported. Same request surface as 4.8. |
| Opus 4.6 | `claude-opus-4-6` | 1M / 128K out | $5 / $25 | Older Opus, still supported. Adaptive thinking; `budget_tokens` deprecated. |
| Sonnet 5 | `claude-sonnet-5` | 1M / 128K out | **$2 / $10** | **Current default Sonnet (GA).** Near-Opus quality on coding + agentic at Sonnet cost. Adaptive thinking ON by default; `effort` defaults to `high`; supports `xhigh`. New tokenizer (~30 % more tokens for the same text vs 4.6). High-res vision (2576px). **Introductory $2/$10 pricing is now permanent** - the originally planned increase to $3/$15 on 2026-09-01 is cancelled and will not occur. [OFFICIAL, verified 2026-08-13 against `platform.claude.com/docs/en/about-claude/pricing`] |
| Sonnet 4.6 | `claude-sonnet-4-6` | 1M / 128K out | $3 / $15 | Previous-gen Sonnet, still supported. Adaptive thinking, prompt caching. |
| Haiku 4.5 | `claude-haiku-4-5` (`-20251001`) | 200K / 64K out | $1 / $5 | Cheap routing, strict JSON/YAML schema, light coding. Best instruction-adherence in the cheap tier. |

Legacy still active: `claude-opus-4-5` ($5 / $25, 200K, retires >= 2026-11-24), `claude-sonnet-4-5` ($3 / $15, 200K, retires >= 2026-09-29). Deprecated: `claude-mythos-preview` (deprecated, migrate to `claude-mythos-5`; the deprecations table lists **no** retirement date - an earlier "retired 2026-06-30" note here was wrong). **Retired (2026-08-05; requests to API fail except on Bedrock and Google Cloud):** `claude-opus-4-1` ($15 / $75, i.e. triple current Opus rates; replacement `claude-opus-4-8`). [OFFICIAL, verified 2026-08-13 against `platform.claude.com/docs/en/about-claude/pricing`] **Fully RETIRED (requests now fail everywhere):** `claude-opus-4-0` + `claude-sonnet-4-0` (2026-06-15), `claude-3-haiku-20240307` (2026-04-20), `claude-3-7-sonnet` + `claude-3-5-haiku` (2026-02-19). Retirement FLOORS on current models: Fable 5 >= 2027-06-09, Opus 5 >= 2027-07-24, Opus 4.8 >= 2027-05-28, Opus 4.7 >= 2027-04-16, Opus 4.6 >= 2027-02-05, Sonnet 5 >= 2027-06-30, Sonnet 4.6 >= 2027-02-17, Haiku 4.5 >= 2026-10-15. Verify against `platform.claude.com/docs/en/about-claude/model-deprecations.md` before quoting to a client.

### Anthropic - community feedback (July 2026)

- **Opus 5 launch (2026-07-24):** positioned as a frontier-capability step at unchanged Opus pricing, and displacing Opus 4.8 as the default reasoning baseline. Note the Claude Code / `opus` alias now resolves to Opus 5 on Max, Team Premium, Enterprise pay-as-you-go and the raw API; on Pro and Team Standard the strongest reachable model is Sonnet 5. [COMMUNITY - several independent write-ups agree; the alias-resolution detail is not on a primary Anthropic page we could fetch 2026-07-31]
- **Sonnet 5 reception:** Highly praised by the developer community for codebase-wide refactoring and context-aware responses (giving short answers for simple lookups, detailed ones for complex bugs). Its "agentic endurance" for multi-step tasks is a major highlight.

### Anthropic - batch, caching & surcharges

- **Batch API: -50 %** on all token usage. Most batches finish within 1 h (max 24 h). [batch-completion timing not re-verified 2026-07-14, not contradicted]
- **Prompt caching:** a cache **write** costs ~1.25x normal input for the 5-minute TTL, ~2x for the 1-hour TTL; a cache **read** costs ~0.1x normal input (about a tenth). **Minimum cacheable prefix (re-verified live 2026-07-31):** 512 tokens on **Opus 5** / Fable 5 / Mythos 5 (Bedrock differs - see the AWS docs); 1024 tokens on Opus 4.8 / Sonnet 5 / Sonnet 4.6 / Sonnet 4.5; 2048 tokens on Opus 4.7; 4096 tokens on Opus 4.6 / 4.5 and Haiku 4.5 - shorter prefixes silently do not cache. (The bundled `claude-api` skill's cached table disagrees - lists Opus 4.8 at 4096, Sonnet 4.6 at 2048; the live docs page is primary. Re-verify if it is load-bearing.)
- **Web search (server tool `web_search_20260209`): $10.00 / 1,000 searches** PLUS the retrieved content billed as normal input tokens. One search call = one billed use regardless of result count; a search that errors is not billed. [OFFICIAL - fills the old UNVERIFIED flag.]
- **Web fetch (server tool `web_fetch_20260209`):** no extra per-call fee beyond the fetched content as input tokens; `max_content_tokens` caps a runaway fetch.
- **Code execution (server tool):** free when used together with web search / web fetch; otherwise $0.05 / hour per container after 1,550 free container-hours / month per organization (5-min minimum).
- **Fast mode** (research preview, premium latency): **Opus 5 and Opus 4.8 only, at $10 / $50 per 1M** - i.e. Fable-5 rates for Opus-class output, across the full context window including >200K prompts. Claude API (first-party) ONLY: not on Claude Platform on AWS or partner clouds, and **not combinable with Batch**. Caching and data-residency multipliers stack on top. Opus 4.7 now ERRORS on `speed:"fast"`; Opus 4.6 silently runs standard at standard billing. [OFFICIAL, verified 2026-07-31]
- **Claude Managed Agents:** billed on two axes - tokens at the normal model rates, PLUS **session runtime $0.08 / session-hour**, metered only while the session status is `running` (idle time is free). Batch, fast mode and data-residency modifiers do NOT apply to Managed Agents sessions, and runtime replaces container-hour billing for code execution. [OFFICIAL, verified 2026-07-31]
- **Data residency:** `inference_geo:"us"` applies a **1.1x** multiplier on every token category (input, output, cache writes, cache reads) for Claude 4.6 and later. Bedrock / Google Cloud regional and multi-region endpoints carry a separate **10 %** premium over global.
- No image generation (Anthropic does not generate images). [not re-verified 2026-07-14, unchanged]

## Google (Gemini)

> **HARD POLICY (2026-08-03): the Gemini 2.x family is BANNED and permanently removed from this file.** No `gemini-2.5-*` or `gemini-2.0-*` model may be listed here, recommended, priced, used in a comparison, or cited as evidence for anything - not as a cheap tier, not as an audio bargain, not "for reference". Rationale: they are unusable in practice and every mention of them pollutes a real decision. **This binds every future refresh too: if a refresh re-adds a 2.x row, that is a regression, delete it.** Gemini starts at 3.x here.

Verified via ai.google.dev/gemini-api/docs/pricing + changelog + models, **2026-08-03** (prior passes 2026-07-31, 2026-07-14). **Every listed rate unchanged since 2026-07-31**; the changelog has no August entries and its last release was robotics-only (`gemini-robotics-er-2-preview`, 2026-07-30, irrelevant to this catalog). **Gemini 3.6 Flash launched July 21, 2026.** Pro models are context-tiered (a higher rate kicks in above 200K input tokens). `-preview` models are NOT stable - their prices change at GA. **Neither Gemini 3.5 Pro nor 3.6 Pro exists** - re-confirmed on the models page 2026-08-03, there is no Pro above `gemini-3.1-pro-preview`; treat any 3.5/3.6 Pro claim as a rumour.

| Model | API id | Context | In / Out per 1M | Use for |
|---|---|---|---|---|
| Gemini 3.7 Flash | `gemini-3.7-flash` | 1M | **$0.75 / $3.75 (intro, through 2026-12-31); $1.50 / $7.50 (standard)** | **Latest flagship Flash (GA 2026-08-13).** Most capable Flash workhorse for coding, agentic, and reasoning-heavy workflows. Replaces 3.6 Flash as flagship. Introductory pricing through December 31, 2026. Batch $0.375 / $1.875 (intro); $0.75 / $3.75 (standard). [OFFICIAL - `ai.google.dev/gemini-api/docs/pricing`, verified 2026-08-13] |
| Gemini 3.6 Flash | `gemini-3.6-flash` | 1M | **$0.75 / $3.75 (intro, through 2026-12-31); $1.50 / $7.50 (standard)** | Previous flagship Flash (GA 2026-07-21). Still supported; being superseded by 3.7 Flash. Same pricing tier as 3.7 Flash for the intro period. Batch $0.375 / $1.875 (intro); $0.75 / $3.75 (standard). [OFFICIAL, verified 2026-08-13 - pricing changed from the 2026-07-31 $1.50/$7.50 rate] |
| Gemini 3.5 Flash | `gemini-3.5-flash` (alias `gemini-flash-latest`) | 1M | $1.50 / $9.00 | Previous-gen flagship Flash (GA 2026-05-19). Still supported; being superseded by 3.6 Flash. Frontier-level intelligence at Flash speed; agentic + complex coding. Computer Use tool in preview. |
| Gemini 3.1 Pro | `gemini-3.1-pro-preview` | 1M | $2.00 / $12 (<=200K); $4.00 / $18 (>200K) | PREVIEW (still not GA as of 2026-07-31). Most advanced Gemini 3.x reasoning + multimodal. No free tier. |
| Gemini 3 Flash | `gemini-3-flash-preview` | 1M | $0.50 / $3.00 | PREVIEW (not stable). Next-gen Flash. Still listed as a preview model on the models page 2026-08-03, but **its price row did not render on the 2026-08-03 pricing fetch** - the $0.50 / $3.00 above is carried over from 2026-07-31, re-check before use. |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | 1M | $0.30 / $2.50 | **Current Flash-Lite (GA 2026-07-21).** One flat input rate covering text / image / video / audio - no audio surcharge, unlike 3.1 Flash-Lite. Batch $0.15 / $1.25. [OFFICIAL, verified 2026-07-31] |
| Gemini 3.1 Flash-Lite | `gemini-3.1-flash-lite` | 1M | $0.25 / $1.50 (audio in $0.50) | Previous-gen low-cost, stable (GA 2026-05-07). Still the cheapest 3.x on text input. |

### Gemini - community feedback (July 2026)

- **3.6 Flash as new baseline:** 3.6 Flash is the new flagship (3.5 Flash now previous-gen). It delivers frontier coding/reasoning at Flash pricing, making it the primary choice for most agentic work unless Pro reasoning is genuinely required.
- **3.5 Flash vs 3.1 Pro (legacy comparison):** The community reported that 3.5 Flash delivered "near-Pro-level" coding capabilities, often beating 3.1 Pro on specific developer benchmarks like Terminal-Bench 2.1. However, 3.1 Pro remained vastly superior for "hard" reasoning and stability.
- **Cost Nuance:** Because Flash might require more iterative "turns" to solve a hard problem in an agentic loop, developers noted Pro can actually be more cost-effective for complex tasks despite its higher base price.

### Gemini - batch, caching & surcharges

- **Batch API: -50 %** across all listed models. (Flex inference = same rate, looser SLO.) Explicit batch rates, verified 2026-08-03: 3.6 Flash $0.75 / $3.75; 3.5 Flash $0.75 / $4.50; 3.5 Flash-Lite $0.15 / $1.25; 3.1 Flash-Lite $0.125 / $0.75; 3.1 Pro $1.00 / $6.00 (<=200K) and $2.00 / $9.00 (>200K).
- **Context caching:** billed at a per-model **cache-read** rate plus a **storage** charge per 1M cached tokens per hour while the cache lives. Full read rates verified 2026-08-03: 3.6 Flash and 3.5 Flash $0.15; 3.5 Flash-Lite $0.03; 3.1 Flash-Lite $0.025 (text/image/video) and $0.05 (audio); 3.1 Pro $0.20 (<=200K) / $0.40 (>200K). Storage is $1.00/1M/hr on the Flash tiers and $4.50/1M/hr on the Pro tiers. Implicit (automatic) and explicit (manual) caching bill at the same rate. **The storage charge is the trap:** a 200K-token cache held on a Pro tier for 24 h costs 0.2 x $4.50 x 24 = ~$21.60 in storage alone, before a single read.
- **Grounding with Google Search:** **5,000 free prompts/month** (shared across all Gemini 3 models), then **$14.00 / 1,000 search queries**.
- **Image generation ("nano banana"):** `gemini-3.1-flash-image` = resolution-tiered (~$60/1M output tokens std, $30 batch; ~$0.045/image at 512px). **`gemini-3.1-flash-lite-image` ("Nano Banana 2 Lite", GA 2026-06-30)** = $0.25/1M input, $1.50/1M text output, **$30/1M image output** (~$0.0336/1000 images at 512px). "Nano banana" is the community nickname.
- **Video generation:** **`gemini-omni-flash-preview` (public preview 2026-06-30)** = short video (3-10 s, 720p) generation/editing; $1.50/1M text input, $9.00/1M text output, **$17.50/1M video output**. (Deprecated gen: `veo-2.0` / `veo-3.0` families already shut down 2026-06-30; the `imagen-4.0-generate-001` / `-ultra` / `-fast` family shuts down 2026-08-17.)
- **Audio input** is tokenized at **32 tokens / second** (1 minute = 1,920 tokens, 1 hour = 115,200) and on some models priced ABOVE text: `gemini-3-flash-preview` and `gemini-3.1-flash-lite` audio = 2x text ($0.50/1M on 3.1 Flash-Lite). **`gemini-3.5-flash-lite` is the exception that matters: one flat $0.30/1M covers audio too**, so it is the cheapest audio input available anywhere. On 3.6 Flash / 3.5 Flash / 3.1 Pro no separate audio rate is published [UNVERIFIED - may equal the text rate]. **Practical, per hour of MP3/MP4: `gemini-3.5-flash-lite` ~$0.035 standard / ~$0.017 batch; `gemini-3.1-flash-lite` ~$0.058; `gemini-3.5-flash` ~$0.17 if audio bills as text.** Video frames count as image tokens (no separate per-second rate for the non-live models).

## OpenAI (GPT)

Verified via developers.openai.com pricing + changelog, **2026-08-03** (prior passes 2026-07-31, 2026-07-14; model + deprecation pages last read 2026-07-14). **No price moved between 07-31 and 08-03 - the changelog has no August entries.** The cut everyone is talking about is still the one from **2026-07-30: GPT-5.6 Luna -80 %, Terra -20 %**, already priced in below.

**GPT-5.6 (Sol / Terra / Luna) launched 2026-07-09.** A new naming scheme where the number is the generation and the name is a durable capability tier that advances independently. GPT-5.5 / 5.4 and the older GPT-5 base family remain live alongside it. Long-context surcharge and caching differ by model family - read the surcharge block. The **cached-input** column below is the price of a repeated prefix and is charged automatically; it is a flat 10 % of standard input on every GPT-5.x model.

| Model | API id | Context | In / Out per 1M | Use for |
|---|---|---|---|---|
| GPT-5.6 Sol | `gpt-5.6-sol` (alias `gpt-5.6`) | ~1.05M | $5 / $30 ($0.50 cached) | **Current frontier flagship (GA 2026-07-09).** Hardest reasoning + agentic + coding. Cutoff Feb 2026. |
| GPT-5.6 Terra | `gpt-5.6-terra` | ~1.05M | **$2 / $12** ($0.20 cached) - cut from $2.50 / $15 on 2026-07-30 | Balanced tier, competitive with GPT-5.5. 20 % price reduction. [OFFICIAL](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/) |
| GPT-5.6 Luna | `gpt-5.6-luna` | ~1.05M | **$0.20 / $1.20** ($0.02 cached) - cut from $1 / $6 on 2026-07-30 | **Cheapest current-generation frontier-family tier on any provider** after the 80 % cut - undercuts both Gemini Flash-Lites on input and output. Cheapest/fastest GPT-5.6 tier. [OFFICIAL](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/) |
| GPT-5.5 | `gpt-5.5` | ~1.05M | $5 / $30 ($0.50 cached) | Previous frontier flagship; still live (not deprecated). No cache-WRITE fee, unlike 5.6. |
| GPT-5.5 Pro | `gpt-5.5-pro` | ~1M | $30 / $180 (no cached rate) | Maximum compute for the hardest problems. Responses API only. |
| GPT-5.4 | `gpt-5.4` | ~1.05M | $2.50 / $15 ($0.25 cached) | Lower-cost frontier workhorse; still live. |
| GPT-5.4 Pro | `gpt-5.4-pro` | ~1M | $30 / $180 (no cached rate) | Deep-reasoning Pro (Responses API only), same rate as 5.5 Pro. |
| GPT-5.4-mini | `gpt-5.4-mini` | 400K | $0.75 / $4.50 ($0.075 cached) | Cheap-but-capable; strong mini for coding + agents. |
| GPT-5.4-nano | `gpt-5.4-nano` | 400K | $0.20 / $1.25 ($0.02 cached) | Ultra-cheap routing / extraction / high-volume backend. Now matched on input and beaten on output by GPT-5.6 Luna - prefer Luna. |
| GPT-5.3-Codex | `gpt-5.3-codex` | 400K | $1.75 / $14 ($0.175 cached) | Dedicated coding-agent flows (SWE-Bench / Terminal-Bench). [OFFICIAL, cutoff Aug 2025] |
| GPT-5 | `gpt-5` | 400K [not re-verified] | $1.25 / $10 ($0.125 cached) | Aug-2025 generation, still listed and live. Cheap frontier-ish input, but a full generation behind 5.4/5.5/5.6 on capability. |
| GPT-5-mini | `gpt-5-mini` | 400K [not re-verified] | $0.25 / $2.00 ($0.025 cached) | Older-gen mini; cheaper than `gpt-5.4-mini`, weaker. |
| GPT-5-nano | `gpt-5-nano` | 400K [not re-verified] | **$0.05 / $0.40** ($0.005 cached) | **Cheapest OpenAI model, and the cheapest input token of any model in this file** - a fifth of Gemini 3.1 Flash-Lite's input. Aug-2025 generation, so use it only where quality genuinely does not bind (dumb routing, dedup, boilerplate extraction). |
| GPT-4.1 | `gpt-4.1` | ~1M | $2.00 / $8.00 | Legacy non-reasoning flagship, still on the price list. |
| GPT-4.1-mini | `gpt-4.1-mini` | ~1M | $0.40 / $1.60 | Legacy mini, still listed. |
| GPT-4.1-nano | `gpt-4.1-nano` | ~1M | $0.10 / $0.40 | Legacy cheap tier. **NOT the cheapest OpenAI model** - `gpt-5-nano` is half the input price at the same output (this file claimed otherwise until 2026-08-03). Deprecates 2026-10-23 -> `gpt-5.4-nano`. |

`o3` (retires 2026-12-11) and `o4-mini` / `o3-mini` (2026-10-23) are legacy reasoning, superseded by GPT-5.x. Base `gpt-4.1` / `gpt-4.1-mini` are NOT on OpenAI's official API-deprecations table (the "Oct 2026 API shutdown" claim is UNVERIFIED; only the ChatGPT-UI retirement on 2026-02-13 is confirmed). **Deprecation wave 2026-07-23:** the `gpt-5.1-codex` / `gpt-5.1-codex-max` / `gpt-5.1-codex-mini` / `gpt-5.2-codex` family, `gpt-5.1-chat-latest`, and `o3-deep-research` all shut down -> `gpt-5.5` (or `gpt-5.4-mini` / `gpt-5.5-pro`). See `model-reference-prompting.md` for status detail.

### OpenAI - community feedback (July 2026)

- **Price-war acceleration:** The July 30 price cuts (Luna -80 %, Terra -20 %) signal aggressive cost competition from Claude Opus 5 and Gemini 3.6 Flash. Luna's new $0.20/$1.20 rate is now the cheapest frontier-quality routing tier available. [COMMUNITY](https://finance.yahoo.com/technology/ai/articles/openai-just-cut-gpt-5-6-173045044.html)
- **Cache-Write Fees Controversy:** The 1.25x cache-write fee on GPT-5.6 remains controversial. Many developers view it as a "hidden cost" compared to GPT-5.5's free caching, especially on the Luna tier for high-volume, low-margin tasks. It is generally offset only in long-running agent loops.
- **Tier Routing Strategy:** The community now recommends: Luna for basic / high-volume work (the new cost baseline), Terra for balanced generation, Sol for deep reasoning and context-heavy agentic work.

### OpenAI - batch, caching & surcharges

- **Batch API: -50 %** input and output, all models (24 h SLO). Flex tier matches batch pricing with variable latency. [not re-verified 2026-07-14, not contradicted]
- **Prompt caching:** a repeated static prefix bills the **cached input at 10 % of standard** on the GPT-5.x family (e.g. GPT-5.5 cached input $0.50/1M vs $5.00). On the image models cached inputs are 25 % of standard. Triggers automatically. **NEW on GPT-5.6+:** cache reads keep the 90 % discount but a **cache-write charge of ~1.25x uncached input** is added, with explicit cache breakpoints and a 30-min minimum cache life; this does NOT apply to 5.5 / 5.4 / 5.3. [OFFICIAL base + COMMUNITY detail]
- **Web search tool (built-in, Responses API):** **$10.00 / 1,000 calls**, flat across models, PLUS the retrieved content billed as normal input tokens.
- **Image generation (token-based, per 1M in / cached / out):** `gpt-image-2` (current flagship) $8 / $2 / $30, plus $5/1M text-input; `gpt-image-1.5` $8 / $2 / $32; `gpt-image-1-mini` $2.50 / $0.25 / $8. Per-image works out to ~$0.006 (low, 1024x1024) up to ~$0.21 (high). **`gpt-image-1.5` AND `gpt-image-1-mini` shut down 2026-12-01; `gpt-image-1` shuts down 2026-10-23** -> `gpt-image-2`. Batch applies (-50 %).
- **Transcription (per MINUTE of audio, verified 2026-08-03):** **`gpt-transcribe` $0.0045/min** and **`gpt-live-transcribe` $0.017/min** (streaming) - both NEW, shipped 2026-07-28; `gpt-4o-transcribe` $0.006/min; `gpt-4o-mini-transcribe` $0.003/min; `whisper-1` (legacy, still active) $0.006/min. **Per hour that is $0.27 / $1.02 / $0.36 / $0.18 / $0.36.** (The pricing page now quotes transcription per minute; the token-based `$2.50/1M in / $10/1M out` figure this file carried for `gpt-4o-transcribe` no longer appears there.) For comparison, the same hour on `gemini-3.5-flash-lite` costs ~$0.035 (flat $0.30/1M covers audio) - **Gemini is roughly 8x cheaper on bulk transcription and, unlike `gpt-transcribe`, actually understands the audio rather than only transcribing it**, which is why Gemini stays the default for media/meeting pipelines.
- **Realtime (per 1M tokens, verified 2026-08-03, now OFFICIAL - was COMMUNITY):** `gpt-realtime-2.1` and `gpt-realtime-2` = audio $32 in / $0.40 cached / $64 out, text $4 in / $0.40 cached / $24 out. **`gpt-realtime-2.1-mini` = audio $10 / $0.30 cached / $20 out, text $0.60 / $0.06 cached / $2.40 out** - about a third of the full model on audio. Legacy `gpt-realtime-1.5` = audio $32 / $64, text $4 / $16.
- **Large-context surcharge:** prompts over **272,000 input tokens** bill at **2x input / 1.5x output** for the whole request (Standard, Batch and Flex). Easy to miss on large-document / large-codebase workloads.
- **Priority processing was RENAMED "Fast mode" on 2026-07-30** - `service_tier: "priority"` and `service_tier: "fast"` are both accepted. **The 2x multiplier is now OFFICIAL** (the 2026-07-30 changelog entry: "up to 2.5x faster speeds than standard processing at twice the price"), so e.g. GPT-5.5 fast = $10 / $60, GPT-5.6 Sol fast = $10 / $60. [OFFICIAL, verified 2026-08-03 - upgraded from COMMUNITY.] Note the name collides with Anthropic's unrelated "fast mode" - do not conflate them.
- **Cached input, all GPT-5.x (verified 2026-08-03):** a flat 90 % off standard input, charged automatically on a repeated prefix. Sol $0.50, Terra $0.20, Luna $0.02, GPT-5.5 $0.50, GPT-5.4 $0.25, 5.4-mini $0.075, 5.4-nano $0.02, GPT-5 $0.125, 5-mini $0.025, 5-nano $0.005 per 1M. The Pro models (`gpt-5.5-pro`, `gpt-5.4-pro`) have no cached rate at all.
- **Data residency:** +10 % on all models released on/after 2026-03-05 when using data-residency endpoints (stacks on everything else; GPT-5.6 likely qualifies).
- Other hosted tools: code-execution container tiered ($0.03 at 1GB / $0.12 at 4GB / $0.48 at 16GB / $1.92 at 64GB per 20-min session); file search $2.50/1,000 calls + $0.10/GB/day vector storage (1GB free).

## Perplexity (Sonar) - search-augmented generation

A different category: the model retrieves live web sources and answers with citations. **Every call triggers a search, so the per-request search fee is billed ON TOP of tokens** - that is the part people miss. Verified via docs.perplexity.ai, 2026-07-14 - **no change since the prior pass.**

| Model | Context | In / Out per 1M | Use for |
|---|---|---|---|
| `sonar` | - | $1.00 / $1.00 | Quick factual lookups + summarization. |
| `sonar-pro` | 200K | $3.00 / $15.00 | Complex queries, 2x citations vs base. |
| `sonar-reasoning-pro` | 128K | $2.00 / $8.00 | Chain-of-thought reasoning with citations. |
| `sonar-deep-research` | - | $2.00 / $8.00 + citation $2/1M + reasoning $3/1M | Exhaustive multi-source synthesis (async; results ~7 days). |

### Perplexity - search fees (on top of tokens)

- **Per-1,000 requests**, scaling with context size (Low / Medium / High): `sonar` $5 / $8 / $12; `sonar-pro` $6 / $10 / $14; `sonar-reasoning-pro` $6 / $10 / $14. `sonar-pro` also has a "Pro Search" mode ($14-$22 / 1,000).
- **`sonar-deep-research`** additionally bills **internal search invocations at $5.00 / 1,000** - one user query can trigger 10-40+ of them, so per-query cost is variable (~$0.30-$1.30+).
- Perplexity Agent API (separate product): web_search $0.005 / invocation, fetch_url $0.0005 / invocation, people_search $0.005, finance_search $0.005.

## Sources

- Anthropic (pricing verified live **2026-08-03**): [`platform.claude.com/docs/en/about-claude/pricing`](https://platform.claude.com/docs/en/about-claude/pricing); `.../about-claude/model-deprecations` + `.../build-with-claude/prompt-caching` last read 2026-07-31; models overview 2026-07-14. API-shape (IDs, params) cross-checked against the bundled `claude-api` skill.
- OpenAI (pricing + changelog verified live **2026-08-03**): [`developers.openai.com/api/docs/pricing`](https://developers.openai.com/api/docs/pricing) (the old `platform.openai.com/docs/*` URLs now redirect here) and [`developers.openai.com/api/docs/changelog`](https://developers.openai.com/api/docs/changelog); `.../models`, `.../deprecations` last read 2026-07-14; GPT-5.6 launch `openai.com/index/gpt-5-6`, price cut [`openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6`](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/). Note `openai.com/api/pricing/` returns HTTP 403 to fetchers - use the developers.openai.com URL.
- Google Gemini (pricing + changelog + models verified live **2026-08-03**): [`ai.google.dev/gemini-api/docs/pricing`](https://ai.google.dev/gemini-api/docs/pricing), [`.../docs/changelog`](https://ai.google.dev/gemini-api/docs/changelog), [`.../docs/models`](https://ai.google.dev/gemini-api/docs/models); `.../docs/audio` last read 2026-07-14.
- Third-party quality index (2026-08-03, partial): [`artificialanalysis.ai/models`](https://artificialanalysis.ai/models) - only Claude Opus 5 (61, top rank) and GPT-5.6 Sol max (59) rendered; the Gemini, Sonnet 5 and Haiku rows did not. Treat as COMMUNITY and incomplete.
- Perplexity (verified 2026-07-14): `docs.perplexity.ai/getting-started/pricing`. **Not re-verified on either the 07-31 or the 08-03 pass** - token prices reported unchanged by a secondary pass only.

Flag before relying on in a public/production context:
- Anthropic min-cacheable-prefix: the live docs (used here) and the bundled `claude-api` skill's cached table DISAGREE (Opus 4.8: live 1024 vs skill 4096; Sonnet 4.6: live 1024 vs skill 2048). Live is primary; re-verify if load-bearing.
- OpenAI: the prices above were read off the pricing page on 2026-08-03, so they are current; the 2026-07-30 cut date is now confirmed by OpenAI's own changelog, and the fast-mode 2x multiplier is OFFICIAL from that same entry. **Still COMMUNITY/UNVERIFIED:** the GPT-5.6 cache-WRITE mechanic (~1.25x uncached input), and the context windows of the GPT-5 base family (`gpt-5`, `-mini`, `-nano`), which were not re-fetched. No official cost-multiplier table for GPT-5.6 reasoning effort exists yet (OpenAI states there is no GPT-5.5 -> 5.6 effort mapping).
- Gemini 3.6 Flash / 3.5 Flash-Lite: prices and GA date (2026-07-21) are OFFICIAL, but their **context window, max output and knowledge cutoff are COMMUNITY-sourced only** - Google's spec table did not render on three fetch attempts (twice 2026-07-31, once 2026-08-03; the models page now omits specs for every model). Do not quote those three numbers to a client without a fresh check.
- Gemini `-preview` models (`gemini-3.1-pro-preview`, `gemini-3-flash-preview`) are not GA - IDs and prices change at stable release, and `gemini-3-flash-preview`'s price row did not render on the 2026-08-03 pricing fetch. Gemini audio rates on 3.6 Flash / 3.5 Flash / 3.1 Pro are not separately published, so the "~$0.17/hour on 3.5 Flash" figure assumes audio bills at the text rate. **Neither Gemini 3.5 Pro nor 3.6 Pro exists** (re-confirmed 2026-08-03).
- Gemini item that is NOT pricing but bites anyway: `temperature`, `top_p` and `top_k` were **deprecated across the latest Gemini models on 2026-07-21**. It belongs in `model-reference-prompting.md`; flagged here so it is not lost.
- The price-performance section is a PRICE comparison. Its quality statements are COMMUNITY or the author's judgment - no benchmark was run or fetched in full, and the third-party index only returned two of the nine models asked for.

---

## Change log

| Date | Added | Source | Removed |
|------|-------|--------|---------|
| 2026-08-13 | **Gemini 3.7 Flash launched + 3.6 Flash pricing cut.** Added new `gemini-3.7-flash` row (GA 2026-08-13, $0.75/$3.75 intro through Dec 31); updated `gemini-3.6-flash` pricing from $1.50/$7.50 to intro $0.75/$3.75 through 2026-12-31, then $1.50/$7.50 standard. **Claude Sonnet 5 pricing made permanent:** changed from "$2/$10 intro, then $3/$15" to "$2/$10 (now standard)"; the Sept 1 price increase is cancelled. **Claude Opus 4-1 now fully retired on API** (retires as of 2026-08-05, except on Bedrock/GCP). | Anthropic: [`platform.claude.com/docs/en/about-claude/pricing`](https://platform.claude.com/docs/en/about-claude/pricing) (verified 2026-08-13); Google Gemini: [`ai.google.dev/gemini-api/docs/pricing`](https://ai.google.dev/gemini-api/docs/pricing) (verified 2026-08-13) | The outdated Sonnet 5 pricing that included a planned Sept 1 increase |
| 2026-08-03 (2nd edit) | **Gemini 2.x banned and purged from the file (v1.5.0).** Removed the `gemini-2.5-pro` / `-flash` / `-flash-lite` rows, their batch and cache-read rates, the 2.5 Google-Search grounding scheme, `gemini-2.5-flash-image`, and every comparison that leaned on a 2.x model (the audio and cheapest-token arguments were re-based on 3.x and still hold). Added a **HARD POLICY block at the top of the Gemini section** that also binds every future refresh, so a refresh cannot quietly re-add them. | Explicit policy ruling 2026-08-03: the 2.x models are unusable in practice and every mention of them pollutes a real decision | The entire Gemini 2.x family and all references to it |
| 2026-08-03 | **Pricing re-verification pass (v1.4.0) triggered by "GPT cut its prices" - it had NOT cut them again: no provider moved a listed rate between 07-31 and 08-03, and both the OpenAI and Gemini changelogs are empty for August. The 2026-07-30 cut (Luna -80 %, Terra -20 %) was already in the file.** What genuinely changed: **new "Price-performance snapshot" section** answering whether Gemini is still the value leader (two worked workloads costed across 19 models, verdict per tier). OpenAI: **added the entire missing GPT-5 base family** (`gpt-5` $1.25/$10, `gpt-5-mini` $0.25/$2, `gpt-5-nano` **$0.05/$0.40**) plus `gpt-4.1` ($2/$8) and `gpt-4.1-mini` ($0.40/$1.60); **corrected the false "gpt-4.1-nano is the cheapest OpenAI model" claim** (`gpt-5-nano` is half the input price); added cached-input rates for every GPT-5.x; **fast-mode 2x upgraded COMMUNITY -> OFFICIAL** (changelog wording "up to 2.5x faster ... at twice the price"); **added the new transcription models `gpt-transcribe` $0.0045/min and `gpt-live-transcribe` $0.017/min** (shipped 2026-07-28) and moved the whole transcription block to per-minute rates; `gpt-realtime-2.1-mini` upgraded COMMUNITY -> OFFICIAL with full audio+text rates. Gemini: added the complete batch and cache-read rate lists, a worked example of the cache STORAGE trap, and re-confirmed that **no Gemini 3.5 Pro or 3.6 Pro exists**. Anthropic: unchanged rates, added cache-hit dollar values and flagged that **`claude-opus-4-1` retires 2026-08-05, two days out**. | Live primary pages fetched 2026-08-03: `platform.claude.com` pricing; `developers.openai.com` pricing + changelog; `ai.google.dev` pricing + changelog + models. Partial third-party index: artificialanalysis.ai | The claim that `gpt-4.1-nano` is OpenAI's cheapest model; the token-based `gpt-4o-transcribe` rate (the page now quotes per-minute); the COMMUNITY flags on fast-mode 2x and `gpt-realtime-2.1-mini` |
| 2026-07-31 | **First automated pass (an automated updater, Haiku) plus a hand review.** Anthropic: **added Claude Opus 5** (`claude-opus-5`, GA 2026-07-24, $5/$25, current default Opus; min cacheable prefix 512), corrected its retirement floor to **2027-07-24** (the bot had guessed 2027-06-24), added floors for Fable 5 (2027-06-09) and Sonnet 5 (2027-06-30), corrected `claude-mythos-preview` from "retired" to **deprecated, no retirement date**, rewrote **fast mode** (Opus 5 + 4.8 at $10/$50, API-only, not with Batch), added **Managed Agents session runtime $0.08/session-hour** and the data-residency multipliers. OpenAI: **GPT-5.6 price cut** - Terra $2.50/$15 -> **$2/$12**, Luna $1/$6 -> **$0.20/$1.20**; added cached-input rates; **"Priority processing" renamed "Fast mode" 2026-07-30**. Gemini: **added Gemini 3.6 Flash** (GA 2026-07-21, $1.50/$7.50, replaces 3.5 Flash) and **Gemini 3.5 Flash-Lite** (GA 2026-07-21, $0.30/$2.50, flat rate incl. audio), plus 3.6 Flash caching rates; restored the "3.5 Pro has NOT shipped" flag the bot dropped. | Live primary pages fetched 2026-07-31: `platform.claude.com` pricing + deprecations + prompt-caching; `developers.openai.com/api/docs/pricing`; `ai.google.dev/gemini-api/docs/pricing`. OpenAI cut narrative: [openai.com/index](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/) | Bot-written [OFFICIAL] labels on two third-party blogs (axios.com, kie.ai) - replaced with the primary pages; the bot's invented "assumed" Opus 5 dates |
| 2026-07-15 | Added "Community feedback (July 2026)" sections for Anthropic, Gemini, and OpenAI detailing real-world experiences with Sonnet 5, GPT-5.6 cache fees, and 3.5 Flash vs 3.1 Pro nuances. | AI Web Research | - |
| 2026-07-14 | **Full refresh, all 4 providers live-verified (v1.2.0).** Anthropic now verified against `platform.claude.com` (not the cached skill): **added Claude Sonnet 5** (`claude-sonnet-5`, current default Sonnet, intro $2/$10 through 2026-08-31), moved Sonnet 4.6 to previous-gen, filled the **web-search rate ($10/1000)**, **corrected the min-cacheable-prefix numbers** (were wrong), added retirement floors + fully-retired list + fast-mode changes. OpenAI: **added GPT-5.6 Sol/Terra/Luna** (GA 2026-07-09) + `gpt-5.4-pro`, confirmed `gpt-5.3-codex` OFFICIAL, GPT-5.6 cache-write mechanic, token-based image pricing (`gpt-image-2`/`-1.5`/`-1-mini` + Dec-01 sunsets), `gpt-realtime-2.1`/`-mini`, priority-processing tier, tiered code-exec, the 2026-07-23 codex-family deprecation wave. Gemini: **added Nano Banana 2 Lite + `gemini-omni-flash-preview` video + imagen/veo deprecations** (no core price change). Perplexity: unchanged (added people/finance search to Agent API). | Live provider pages (2026-07-14 research pass); `claude-api` skill for Claude API-shape | UNVERIFIED web-search flag; wrong cache-minimum values |
| 2026-06-26 | **Restructured into catalog + pricing with per-provider "batch, caching & surcharges" blocks.** Added batch (-50 % all providers), prompt-caching read/write economics, Anthropic code-execution + web-search-billing notes, Gemini grounding (two schemes) + image ("nano banana") + audio-token pricing, OpenAI caching/web-search/image/audio/large-context-272K/data-residency surcharges. Added **Perplexity Sonar** table + search-fee block. Added **Opus 4.7 and Opus 4.6** rows; sorted every provider newest-first. **Flagged Fable 5 as currently unavailable / disabled by policy.** Removed the "Selection principle" section (the bottom-up rule is a selection policy, not part of the catalog). Added cross-references to the two prompting files. | `claude-api` skill (Anthropic, authoritative); official OpenAI / Gemini / Perplexity pricing pages (2026-06-26 research pass) | "Selection principle" section. |
| 2026-06-16 | Initial lineup (Anthropic / Gemini / OpenAI tables, selection principle). | claude-api skill; provider pages | - |

Last verified: 2026-08-13 (Anthropic, OpenAI, Gemini; Perplexity still 2026-07-14). Refresh manually before a production model choice.
</llm_lineup>
