---
title: "Prompt evaluation runner"
summary: "The evaluator the plugin runs for a live prompt evaluation, and the libraries it needs."
status: draft
version: "0.1.0"
---

# Prompt evaluation runner

`run_eval.py` is the evaluator behind a `single-judge` or `jury` run. It sends the prompt to the chosen target model on each example, asks every chosen judge to score the outputs, and writes the run into `prompt-evals/<prompt-slug>/` in the workspace that owns the prompt.

Nobody starts it by hand. The plugin's `scripts/run_live_eval.sh` is the only entry point: it checks the user's context directory, loads the keys from `<context dir>/.env` inside its own process, confirms that each selected model has a key, and then calls this file.

`requirements.txt` is the list of provider libraries the run needs (Anthropic, Google, OpenAI, plus the `.env` reader). They are installed once into `~/.cache/taste-ai-quality-kit/runtime`, which the first live run creates. Nothing is installed system-wide and nothing is added to the plugin directory.

Keys are read only into the running process. No key value is printed, logged or written into a report.
