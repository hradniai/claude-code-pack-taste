---
type: notes
title: "AI Prompt Engineering Guidelines (model-agnostic)"
status: review
summary: "Model-agnostic prompt-engineering techniques and principles: what each technique is, its purpose, when to use it, when not to. Plus the two core principles, high-level per-family headlines, the single-call/agent scaffolds and JSON discipline. NOT pricing (see model-lineup), NOT per-model detail (see model-reference-prompting)."
created: 2026-06-12 00:00
updated: 2026-06-26 14:15
owner: Šimon Hradní
client: ~
path: workspace/_CONTEXT/llms/ai-prompt-guidelines.md
tags: [note]
version: "2.0.0"
release: latest
---

# AI Prompt Engineering Guidelines (model-agnostic)

> **Purpose: HOW to prompt, the techniques - independent of any one model.** Each technique is given as what it is / why / when to use / when not. For the model catalog + pricing see `model-lineup.md`; for how a SPECIFIC model wants to be prompted (Anthropic likes XML tags, the per-endpoint API parameters, etc.) see `model-reference-prompting.md`. The three files cross-reference and stay deliberately non-overlapping.
>
> Rebuilt 2026-06-26 from a research pass.

---

## Core principles

### Optimal, not minimal

**Quality over quantity. Add what is needed, skip what is not.** The single rule that governs every prompt regardless of model.

- **Add more** when an example covers a genuinely different variant, an explanation prevents a mistake the model actually makes, context demonstrably changes output quality, or error handling covers a failure that will really occur.
- **Skip** redundant examples (same pattern, different data), obvious explanations, instructions that do not change the output, and verbose framing that could be one sentence.
- **Golden rule:** if removing it makes the prompt worse, keep it; if not, cut it. Recent frontier models do natively what older prompts scaffolded by hand, so the optimal prompt for a 2026 model is shorter than the one you wrote for its predecessor (see the per-model "re-baseline" notes in `model-reference-prompting.md`).

### Prompt language vs output language

**The prompt body is always English. The output language is a constraint you state INSIDE that English prompt - never a reason to switch the prompt's language.** Two independent decisions:

- **Prompt language = English, always.** Every instruction, system prompt, agent rule, classifier prompt, and inline f-string scaffold handed to an LLM is English. Reason: token cost (English tokenizes shorter) and consistency with the rest of the prompt tooling. Holds even when the deliverable must be Czech.
- **Output language / tone = stated explicitly.** If the result must be Czech, add one line: `"Write the output in native Czech, conversational tone"`. The model reads an English instruction and produces Czech.
- **The trap:** conflating "the user-facing output must be Czech" with "the prompt must be Czech." Writing the prompt in the output language costs tokens and buys nothing. Check BOTH the named prompt body AND any inline f-string wrappers in code. Output-format markers the parser keys on (`### A`, a JSON key) stay verbatim - they are a machine contract, independent of language.

---

## Prompt-engineering techniques

The most-used techniques, each with when-to and when-not. Two universal conditionals run through several of them and matter more than any single technique: **on reasoning models (any vendor) do NOT prompt explicit chain-of-thought, and add few-shot examples only for format control, not to improve reasoning.** Those models reason internally; explicit scaffolding duplicates the work and can constrain their search. See each technique below.

### Zero-shot
Issue the instruction with no examples. Fastest and cheapest - **always try this first.** Good for simple, well-defined tasks (translation, summarization, general Q&A, basic classification). The token cost of examples is only justified once zero-shot quality is insufficient. Avoid for specialized-domain tasks with weak pre-training coverage, or where a specific output structure is required. Fully agnostic.

### Few-shot (in-context examples)
Put 3-8 input-output example pairs in the prompt so the model learns the pattern in one call. Calibrates format, tone and task interpretation without fine-tuning (40-70 % improvement on structured tasks vs zero-shot). Use when output format is critical, style is nuanced, or classification needs anchored categories. Use **diverse** examples, not a uniform cluster (unintended patterns propagate); place statically-reused examples early to maximize prompt caching. **Reasoning-model conditional:** on models that reason internally (see the list under CoT), few-shot can suppress the internal search - start without examples and add them only if format control specifically needs them. (The example-wrapping syntax differs by model; Claude's `<example>` tags are in `model-reference-prompting.md`.)

### Chain-of-thought (CoT)
Tell the model to produce intermediate reasoning before the answer ("think step by step", or worked example chains). Improves multi-step math / logic / commonsense accuracy 15-40 % on **non-reasoning** models (Claude Haiku, Gemini Flash, GPT mini-tier). **CRITICAL universal rule: do NOT prompt explicit CoT on reasoning models** - Claude Opus 4.6 / 4.7 / 4.8 and Fable-class (adaptive thinking on), OpenAI o-series, Gemini Thinking Mode. On those it (a) duplicates internal work, raising cost and latency for no gain, and (b) can constrain the internal search, producing WORSE results. Correct approach there: set the reasoning-effort parameter and give high-level goals, not steps. This conditional is endorsed by all three major vendors.

### Role vs purpose / goal framing
Role framing assigns an identity ("You are a senior auditor"); goal framing states what must happen and why. Both work, but **goal/constraint framing is more reliably instruction-following.** Keep a one-sentence role to set tone and domain, then let explicit goal + constraints do the heavy lifting. Drop elaborate personas when they conflict with the task ("creative like a novelist" pulls against "precise like an analyst"). The warning that aggressive persona language ("CRITICAL: You MUST") overtriggers is model-specific (Claude) - see the reference.

### Prompt chaining / task decomposition
Break a complex task into a sequence where each step's output feeds the next, orchestrated in code or multi-turn. Lets each call focus on one subtask so errors are caught before they cascade. Use for clearly separable stages, tasks beyond reliable single-call accuracy, or where intermediate outputs need programmatic review. Skip for simple tasks (adds latency/cost); if subtasks are tightly interdependent with non-linear data flow, an orchestrated agent with tools fits better. Fully agnostic.

### Self-consistency
Run the same prompt several times at temperature > 0 and majority-vote the answer. Averages out individual reasoning errors on tasks with discrete correct answers (math, logic, multiple-choice). Skip for open-ended generation, latency- or cost-sensitive pipelines, and largely redundant on reasoning models (they already search multiple paths internally).

### ReAct (reason + act)
For tool-using agents: interleave Thought -> Action (tool call) -> Observation (result), cycling to completion. Combines reasoning with retrieval - the standard production agent pattern. Use for any tool-augmented agent where the next step depends on what the last step retrieved. Skip for single-call no-tool tasks or extremely latency-sensitive flows. On reasoning models the explicit Thought step is less necessary to prompt, but the Action/Observation structure still applies. Agnostic.

### Structured output / JSON discipline
Constrain the model to schema-valid JSON. **Always prefer API-level schema enforcement over prompt-only** when available (OpenAI / Anthropic / Google all offer it; the mechanism differs per vendor). When prompt-only, use both "output ONLY JSON" and a complete inline schema example, plus a parse-and-retry loop. Skip for conversational UX; for a single-field extraction a regex post-processor is cheaper. (Full JSON discipline below.)

### Output constraints and positive-over-negative framing
Specify what the output must look like (length, prose vs list vs table, markdown or not). **Phrase constraints positively:** "write in flowing prose paragraphs" beats "do not use markdown" - the positive form gives a concrete target. Negative instructions are legitimate as guardrails ("do not invent citations") but should accompany a positive statement of what you DO want. Agnostic.

### Delimiters / structural tags
Use explicit markers (XML tags, markdown headers, fences) to separate instructions, context, examples, input and output schema - models misread an undifferentiated block. Use for any prompt with more than one type of content; wrap multiple documents each in its own tag. The **principle** is agnostic; the specific syntax is model advice (Claude favors XML - see the reference).

### Retrieval grounding / context placement (RAG-in-prompt)
Inject retrieved documents into the prompt so the model grounds its answer in them rather than parametric memory. **Placement rule (documented by Anthropic AND Google): documents FIRST, question/instruction LAST** - up to 30 % improvement on complex multi-document tasks. Wrap documents in tags and ask the model to quote relevant passages before answering (reduces long-context distraction). Pre-summarize or re-rank chunks when they will not fit. Agnostic.

### Self-evaluation / verification loop
Have the model (or a separate evaluator) check its output against a rubric and correct it. Catches plausible-but-wrong answers. **A SEPARATE evaluation call is far more reliable than same-call self-critique** (a model rationalizes its own wrong answer). Use for high-stakes outputs with checkable criteria; useless for open-ended creative work with no ground truth. Agnostic.

### Eagerness / persistence controls
Instructions (prompt- or API-level) that bound how proactive an agent is: max tool calls, stop conditions, confirmation before irreversible actions. Prevent runaway loops and cost explosions. Gate irreversible actions (send email, delete, pay) behind confirmation; leave read-only tools (search, file reads) ungated - "ask before every action" negates the point of an agent. The principle is agnostic; the specific knobs (`effort`, `max_tokens` as a hard cap) are per-vendor (reference).

---

## High-level per-family headlines

Just the headline per family - the detail (behavioral shifts, exact API params, per-endpoint calls) lives in `model-reference-prompting.md`.

- **Anthropic (Claude):** XML tags as the primary structure; explain WHY behind a rule; constraints at top AND bottom; avoid aggressive CAPS language (overtriggers). Reasoning is adaptive - set `effort`, do not hand-write CoT. Prefill is gone on 4.6+ (use structured outputs).
- **OpenAI (GPT-5.x):** outcome-first markdown; minimal scaffolding (the model self-reasons); use the Responses API; tune `reasoning_effort` and `verbosity` rather than prompt length.
- **Google (Gemini 3.x):** direct, concise prompts; keep default temperature; put the question after long content; use `thinking_level` instead of hand-written CoT.
- **Reasoning models (any vendor):** give the goal, not the steps; set the reasoning-effort param; drop few-shot and "think step by step".

---

## Use-case frameworks (agnostic scaffolds)

Combine these with the per-provider structure from the reference (XML for Claude, markdown for GPT/Qwen). Include only the sections that affect output quality - a 3-field prompt is fine for a simple task.

### Single model call (classic automation)
For a single-step task with no tool calls or branching.
```
ROLE:         [identity - skip if Purpose is enough]
CONTEXT:      [business context, input characteristics, audience]
TASK:         [clear objective - one sentence]
REQUIREMENTS: [must-haves]
FORMAT:       [structure + length]
EXAMPLE:      [realistic input -> expected output]
CONSTRAINTS:  [key limits]
```

### AI agent
For a multi-step task with tool calls, branching, or state across turns.
```
ROLE & MISSION: [identity + purpose]
SOP:            [decision flow with explicit IF/THEN]
TOOLS:          [one doc block per tool: Purpose + DO NOT use for + params + errors]
DECISION RULES: [explicit branching]
MEMORY:         [what to track across steps]
OUTPUT:         [final format]
CONSTRAINTS:    [repeat at end]
```
A prescriptive `Purpose` + `DO NOT use for:` per tool is the single most effective fix for wrong-tool selection. State error handling per tool (timeout -> retry N, 500 -> queue, 400 -> return code). Track state only when genuinely needed across turns, and never carry PII/payment data in state.

---

## JSON output (agnostic discipline)

Prefer API-level enforcement over prompting wherever it exists - it is strictly more reliable than asking nicely.

1. **Schema first.** Define the schema in the prompt with one example covering the key case: `Return ONLY valid JSON matching this schema - no markdown, no code blocks: { ... }`.
2. **Escape rules.** Quotes inside strings `\"`, newlines `\n` (not literal breaks), backslash `\\`, no trailing commas, all strings double-quoted.
3. **Null handling.** `null` = cannot determine; `""` = explicitly empty; `[]` = empty array; `0` = zero count. Never the strings `"N/A"` / `"unknown"` / `"null"`.
4. **Validation.** "Before outputting: verify schema match, required fields present, correct types; fix silently, then output ONLY JSON."

Per-model JSON reliability and the exact enforcement parameter per vendor are in `model-reference-prompting.md`.

---

## Anti-patterns and symptom -> fix (agnostic)

### Anti-patterns
| Anti-pattern | Fix |
|---|---|
| `"Make it good"` | concrete success criteria (e.g. "logical flow + 3 supporting examples + conclusion with next step") |
| Placeholder examples (`[your data here]`) | realistic data matching actual input |
| `"If necessary, handle errors"` | explicit per-error behavior (timeout -> retry 2x; 500 -> queue; 400 -> return error_code) |
| `"Think step by step"` on a reasoning model | remove - it hurts; set the reasoning-effort param instead |
| Few-shot examples to improve a reasoning model's reasoning | remove - add examples only for format control |
| Constraints phrased only as negatives | add the positive target ("write in prose", not just "no markdown") |
| Role-heavy framing (`"You are an expert..."`) | purpose-first framing ("Your task is to...") + constraints |
| Writing the prompt in the output language | prompt body is English; output language is a one-line constraint |
| Prompt-only JSON when the API enforces schema | use the API-level structured-output / controlled-generation feature |

### Symptom -> fix
| Symptom | Fix |
|---|---|
| Inconsistent output | add specific format requirements with an example |
| JSON wrapped in markdown | "ONLY JSON, no code blocks, no markdown" (or enforce via API) |
| Fields sometimes null, sometimes missing | explicit null policy in the prompt |
| Agent picks the wrong tool | add `DO NOT use for:` + a "call this when..." trigger per tool |
| Reasoning model ignoring detailed instructions | simplify to a goal statement; remove step-by-step |
| Hallucination on long context | put documents first, question last; ask it to quote sources before answering |
| Runaway agent loop | set a tool-call budget + stop condition; gate irreversible actions |

---

## Change log

| Date | Added | Source | Removed |
|------|-------|--------|---------|
| 2026-06-26 | **Full rebuild from a stale per-model file into a model-agnostic techniques reference.** 13 techniques (zero/few-shot, CoT, role-vs-goal, decomposition, self-consistency, ReAct, structured output, output constraints, delimiters, RAG/context-placement, self-evaluation, eagerness controls) each with when / when-not and the two universal reasoning-model conditionals (no explicit CoT; few-shot for format only). Kept the two Core Principles, the single-call + agent scaffolds, JSON discipline, agnostic anti-patterns / symptom->fix. Added high-level per-family headlines that point into `model-reference-prompting.md`. Status set to `review`. | Anthropic / OpenAI / Google official prompting docs + DAIR PromptingGuide.ai + ReAct paper (2026-06-26 research pass) | The entire prior content (stale: recommended GPT-4.1 / Opus 4.7 as flagship; per-model detail now consolidated in `model-reference-prompting.md`; pricing belongs in `model-lineup.md`) |
| 2026-04-19 | (historical) Opus 4.7 section, model-selection table, per-provider prompting, use-case frameworks, JSON output, quick reference. | Anthropic news + platform docs | - |

**End of Guidelines**
