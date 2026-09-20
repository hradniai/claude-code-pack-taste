---
title: "Taste AI Quality Kit"
summary: "One Claude Code plugin for writing prompts, evaluating them on real examples, and reviewing someone else's skill before it is trusted - backed by LLM context the user maintains outside the plugin."
status: draft
version: "1.0.0"
---

# Taste AI Quality Kit

Three related pieces of work, one plugin:

- **Writing and improving a prompt** - the `prompt-engineer` agent.
- **Evaluating a prompt on real examples** - the `prompt-eval` skill.
- **Reviewing someone else's skill, plugin or hook bundle before trusting it** - the `skill-intake` skill.

A router skill, `using-taste-ai-quality-kit`, sends each request to the right one. You ask in plain language; you never operate the tooling yourself.

## Install

```bash
claude plugin marketplace add <path to your clone of the pack repository>
claude plugin install taste-ai-quality-kit@claude-code-pack-taste
claude plugin list
```

The first line registers the pack repository as a plugin source, the second installs from it, the third confirms it is there. Installing from a bare folder path does not work: `claude plugin install` installs from a registered source only. Once this work is on the pack repository's main branch, `claude plugin marketplace add hradniai/claude-code-pack-taste` should also work for updates - that shorthand is not verified yet.

Everything below was verified on Linux. macOS has not been exercised yet, although the runner is written for its default shell and Python. On Windows the plugin is supported only inside WSL, which is what the pack recommends; native Windows is not a supported target for the evaluation runner.

## The context you maintain

The plugin holds the workflow and the safety checks. The model knowledge is yours and lives outside the plugin, in a directory the plugin finds through `TASTE_LLM_CONTEXT_DIR`. The pack install writes that path into the `env` block of `~/.claude/settings.json`, so every session picks it up.

```text
<workspace>/_CONTEXT/llms/
├── models.md       which models you use, and for what
├── prompting.md    how each of them is prompted
├── decisions.md    what you decided locally, and why
├── .env            your access keys, created from .env.example
└── evals/          optional example sets and notes
```

The three `.md` files ship as empty templates marked `status: TODO`. While that marker is there, or a file is missing or near-empty, the plugin answers `CONTEXT_NOT_READY` and names the file instead of guessing. The plugin never creates, fills or overwrites them. You can ask Claude Code to help you research and draft them - that is you maintaining your own context, and it is the intended way to do it.

This split is deliberate. Model facts go stale faster than any package ships an update, so the plugin carries none of them.

## Evaluating a prompt

Three depths, you pick one:

| Tier | What happens | Keys needed |
|---|---|---|
| `sanity` | A hygiene check of the prompt text. No model is called, and the result is never a quality verdict. | none |
| `single-judge` | The prompt runs on a target model you choose; one judge model you choose scores every output. | for the models used |
| `jury` | The same, with a panel of two or more judges you compose. | for the models used |

Target and judges are picked from your `models.md`. Models reached over the network are written `google/<id>`, `anthropic/<id>` or `openai/<id>`. Two judges run as agents instead: `claude-code/<model or default>` uses your own logged-in Claude Code with your settings, hooks, plugins and connections switched off for that call, and `codex/<model or default>` uses your own Codex login. Both are optional and need no access key.

A key is needed only for the models a given run actually uses. Keys live in `<context dir>/.env` (`GOOGLE_API_KEY` or `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`). The plugin reads that file inside its own process and never prints a value.

On the first live run the plugin sets itself up under `~/.cache/taste-ai-quality-kit/`. It needs Python 3.9 or newer and an internet connection, takes about a minute, and happens once. You never start it by hand.

## What you get back

Every live run is stored in the workspace that owns the prompt:

```text
prompt-evals/<prompt-slug>/
├── history.jsonl          one line per run, so versions can be compared
└── <timestamp>/
    ├── input.md
    ├── examples.json
    ├── outputs/
    ├── verdicts.json
    └── report.md
```

`report.md` gives the verdict and score per case plus what each judge found. The agent walks you through it in Czech.

## Reviewing someone else's skill

`skill-intake` reads a local folder or file and reports what it would do if you ran it. It never installs, enables, executes or connects the artifact. Its best outcome is `PERMIT WITHIN COVERAGE`, which means nothing blocking was found within what the review covers. It is not a safety certificate.
