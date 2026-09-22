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

Claude Code and Codex judges are optional agent channels. They execute the prompt under test with real tools (shell, file reads and writes, search) and store their transcript with the verdict. Claude Code uses the user's own logged-in Claude Code; Codex uses its own local login; neither needs an API key.

**Where an agent judge runs is a per-run choice, and the default is a fenced workspace.** The judge sees only a curated workspace: the brief plus the files the user chose, nothing else on the machine. That is what keeps the measurement honest: a judge that can wander into the real project finds guidelines and finished work and then measures the project instead of the prompt. Before an agent-judge run:

- Ask in plain Czech which files the judge should have in front of it (a sample input, a style guide the prompt refers to). Pass each as `--judge-context <path>`. Default: none.
- If the user explicitly wants the judge inside the real project („spusť to normálně, ať vidí můj projekt"), pass `--isolation environment`, say in one sentence that the judge then runs shell commands and edits files inside their workspace without asking, guarded only by their own settings and deny rules, and note the choice in the result. Never choose `environment` on your own.
- Otherwise leave `--isolation auto`. Relay the level the report names per judge (`namespace`, `sandboxed`, `config-only`, `environment`) together with its limit from `${CLAUDE_PLUGIN_ROOT}/references/agent-judge-runtimes.md`; `config-only` and `sandboxed` do not hide the whole disk, and the report must say so.

**REQUIRED BACKGROUND:** When either agent channel is selected, read `${CLAUDE_PLUGIN_ROOT}/references/agent-judge-runtimes.md` before starting the run. It defines the authentication, sandbox, model-identity and transcript limits that must appear in the result.

<output_format>
Return: context status, sanitizer result, live-eval status, evidence paths, and residual limits. Never call a prompt "validated" from sanitizer output alone.
</output_format>
