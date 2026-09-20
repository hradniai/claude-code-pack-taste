---
title: "Prompting rules"
summary: "Prompting rules tied to one model family, checked or deliberately adopted by you."
status: TODO
version: "0.1.0"
---

# Prompting rules

Only rules that depend on the model family belong here: what works with one provider and not another. General Taste writing rules belong in the project instructions, not in this file.

## How to fill this in

Each rule carries the family it applies to, the rule itself, why it holds, where you read it, and the date you checked.

Here is the shape, written with a made-up family. Delete it and write your own:

```text
### provider/model-family
- Rule: <what to do, or avoid, when prompting this family>
- Why: <what goes wrong otherwise>
- Source: <link to the provider guide, or "own test">
- Checked: 2026-01-31
```

A rule you reached through your own testing counts. Say so in the source line, so that later you can tell it apart from something the provider documents.

Once the file holds real rules, change `status: TODO` in the header to `status: active`. That marker is what keeps the plugin closed.
