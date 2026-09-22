---
title: "LLM decisions"
summary: "The local calls about how models are used here, each one kept with its reasoning."
status: TODO
version: "0.1.0"
---

# LLM decisions

The non-obvious calls you made: which provider for what, which prompting pattern you settled on, what you evaluate against, what data may leave your machine, and every exception you granted. A decision without its reasoning cannot be revisited later, so the reasoning is the point of the entry.

## How to fill this in

Each entry carries the decision, why you made it, what you turned down and why not, who owns it, and the date.

Here is the shape, written with a made-up identifier. Delete it and write your own:

```text
### 2026-01-31 - <short name of the decision>
- Decision: <what now applies>
- Why: <what led to it>
- Turned down: provider/model-id, because <reason>
- Owner: <name>
```

When a decision stops holding, leave the entry where it is and write the new one below it. The old reasoning is what makes the change readable a year later.

Once the file holds real decisions, change `status: TODO` in the header to `status: active`. That marker is what keeps the plugin closed.
