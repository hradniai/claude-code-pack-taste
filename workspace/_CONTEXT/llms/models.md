---
title: "Model records"
summary: "The models you are allowed to pick for Taste work, each one checked against a source."
status: TODO
version: "0.1.0"
---

# Model records

One record per model you may select, whether it runs a prompt or judges the output. Never write a model name from memory: look it up, then record where you looked and when.

## How to fill this in

Each record carries the identifier, what you use it for, what it costs or what your plan allows, the source you checked, and the date you checked it.

Identifiers follow how the model is reached:

- over the network: `google/<model-id>`, `anthropic/<model-id>`, `openai/<model-id>`;
- as a local agent: `claude-code/<model or default>`, `codex/<model or default>`.

Here is the shape, written with a made-up identifier. Delete it and write your own:

```text
### provider/model-id
- Use for: longer Czech drafts; not for anything with numbers in it.
- Cost or quota: <what you pay, or what your plan allows>
- Source: <link to the provider page you read>
- Checked: 2026-01-31
```

Once the file holds real records, change `status: TODO` in the header to `status: active`. That marker is what keeps the plugin closed.
