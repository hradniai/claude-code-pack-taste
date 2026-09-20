---
name: prompt-eval
description: Use when a Taste prompt or agent artifact is ready for a hygiene check or evaluation - prepare and run the plugin-managed evaluation without asking a non-technical user to operate tooling.
---

<purpose>
Produce evidence about a Taste prompt without making a non-technical user learn evaluation tooling.
</purpose>

<constraints>
- Run `${CLAUDE_PLUGIN_ROOT}/scripts/check_llm_context.py --context-dir "$TASTE_LLM_CONTEXT_DIR"` first. Stop on `CONTEXT_NOT_READY`.
- Always run `${CLAUDE_PLUGIN_ROOT}/scripts/sanitize_prompt.py --prompt <path>` before a live evaluation.
- A sanitizer pass is a hygiene result, not a quality verdict.
- Run a live evaluation only through `${CLAUDE_PLUGIN_ROOT}/scripts/run_live_eval.sh`. The plugin installs and runs its own isolated evaluation runtime. Never ask the user to run a command, and never substitute your own single-message run for the evaluator.
- Runtime keys stay in `$TASTE_LLM_CONTEXT_DIR/.env`. Do not read, print, copy, or place values in reports.
- Require keys only for the target and judge models selected for this run.
</constraints>

## Workflow

1. Resolve the prompt file and intent from the maintained context. Ask whether the user wants `sanity`, `single-judge`, or `jury`.
2. For `single-judge`, ask which single model should judge the run. For `jury`, ask which exact maintained models belong in the panel. API models use `google/...`, `anthropic/...`, or `openai/...`; optional agent judges use `claude-code/...` or `codex/...`. Do not force one model from every provider family.
3. Check the context and run the sanitizer. `sanity` ends here.
4. For `single-judge` or `jury`, select the target model that runs the prompt and write a small JSON array of representative user inputs (three to five strings). Include an incomplete-input case and a case whose text states that the input is empty, for example `"The input is empty. Return the defined fallback only."`. An empty string is rejected by the providers, so never use one. Use safe, representative data: no credentials and no client personal data the example does not need, because inputs, outputs and judge findings are stored in the workspace under `prompt-evals/`.
5. Run the plugin-managed evaluator without exposing its implementation detail:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/run_live_eval.sh" \
  --context-dir "$TASTE_LLM_CONTEXT_DIR" \
  --prompt <prompt-path> \
  --intent "<what good output looks like>" \
  --tier <single-judge|jury> \
  --model "<model API id from models.md>" \
  --examples <examples.json> \
  --judge "<selected provider/model API id from models.md>" \
  --workspace <current-workspace>
```

6. For `jury`, repeat `--judge` for every selected model. The run is stored under `<workspace>/prompt-evals/<prompt-slug>/<timestamp>/`; read its `report.md` and relay verdict, score and the judges' findings in plain Czech. The first live run installs the runtime and takes about a minute longer. If a prerequisite is missing (`EVAL_NOT_CONFIGURED` on stderr), explain it in plain Czech and offer to set it up. Do not name Python, SDK, or CLI unless the user explicitly asks for technical detail.

Claude Code and Codex judges are optional agent channels. They run in an isolated temporary workspace and store their transcript with the judge verdict. Claude Code uses the user's own logged-in Claude Code in headless mode with settings, hooks, plugins and MCP servers disabled for that call; it needs no API key. Codex uses its own local login.

**REQUIRED BACKGROUND:** When either agent channel is selected, read `${CLAUDE_PLUGIN_ROOT}/references/agent-judge-runtimes.md` before starting the run. It defines the authentication, sandbox, model-identity and transcript limits that must appear in the result.

<output_format>
Return: context status, sanitizer result, live-eval status, evidence paths, and residual limits. Never call a prompt "validated" from sanitizer output alone.
</output_format>
