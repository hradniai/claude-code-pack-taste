---
title: "LLM context"
summary: "The model knowledge you maintain yourself; the Taste AI Quality Kit reads it and never writes it."
status: draft
version: "0.1.0"
---

# LLM context

This directory is yours. It holds what you know about the models you work with, and the Taste AI Quality Kit reads it through `TASTE_LLM_CONTEXT_DIR` instead of carrying model facts of its own. Model facts go stale faster than any package ships an update, which is why they live here and stay current by your hand.

Three files, plus your keys:

- `models.md` - which models you use and what for;
- `prompting.md` - how each of them is prompted;
- `decisions.md` - what you decided locally, and why;
- `.env` - your access keys, copied from the example file next to it and never committed anywhere.

Each of the three starts as an empty template marked `status: TODO` in its header. While that marker is there, or a file is missing or nearly empty, the plugin stops and tells you which file it is waiting for. That is deliberate: no advice at all beats advice from half-year-old records.

You do not have to fill them alone. Ask Claude Code to go through one with you - look up what is current, weigh it, write it down. The records stay yours either way; the plugin never writes, fills or replaces them.

## Reference documents

Four maintained reference documents ship next to your records, as a starting point when you fill them in:

- `model-lineup.md` - model catalog and prices across providers;
- `model-reference-prompting.md` - how each model family is prompted and called;
- `ai-prompt-guidelines.md` - prompting techniques that hold regardless of model;
- `codex-cli-reference.md` - reference for the OpenAI Codex CLI.

They are a snapshot with the date of each check written inside, so they age like any model fact. The plugin does not read them; what you take from them goes into your own three files, checked and dated by you.

Keep example sets and evaluation notes in `evals/`. Use safe, representative data there - never real credentials, and no client personal data the examples do not need.
