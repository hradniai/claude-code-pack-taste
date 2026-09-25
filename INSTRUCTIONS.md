---
type: notes
title: "Instructions for Claude - Pack Installation"
status: approved
summary: "You are reading this because the user just cloned the Claude Code Pack and ran `claude` in the repo root."
created: 2026-06-16 00:52
updated: 2026-09-25 10:50
owner: Šimon Hradní
client: ~
path: INSTRUCTIONS.md
tags: [note]
version: "1.0.0"
release: latest
---

# Instructions for Claude - Pack Installation

You are reading this because the user just cloned the Claude Code Pack and ran `claude` in the repo root. Your job is to walk them through installation **safely and interactively**, with explicit confirmation at every major step. Treat the user as a smart power-user who hasn't done this before - explain what each step does, ask before touching anything outside the repo, and respect their preferences (path, OS, names).

**Hard rules for this install session:**
- Do not silently run install commands. Show the command, get approval, then execute.
- After running, report the result in one line.
- Terse, no narration. The user can read.
- If the user says "skip this", skip it and note what was skipped.
- If anything fails, stop. Don't continue to the next step.
- Never use `rm -rf` during install - use `mv` to a backup path instead.
- Never use `sudo`. If something requires it, instruct the user to run that one command manually.

---

## Step 0 - Greet, confirm intent, set the frame

Open with:

> Připravím tvůj Claude Code podle Pack. Ujistím se předem, co budu měnit a kam to půjde. Žádný krok neprovedu bez tvého potvrzení. OK pokračovat?

Wait for explicit yes.

Then explain what's coming, in one paragraph:

> Instalace má dvě části:
> 1. **Kernel** - globální nastavení do `~/.claude/` (settings, hooks, rules, skills, statusline). Pravidla pro to, co Claude smí a nesmí, plus pomocné nástroje.
> 2. **Workspace** - adresářová struktura pro tvou práci (klienti, vlastní projekty, nástroje, kontext). Tu si umístíš kam chceš.
>
> Před každou částí se zeptám na tvé preference. Pokud někde už máš svůj setup, zálohujeme ho, nepřepisujeme.

---

## Step 0.5 - Vyzvi uživatele k plan modu a napiš plán

Než cokoli zkopíruješ, zálohuješ nebo upravíš na stroji, **napiš plán** a získej souhlas. Nejčistší cesta je plan mode, který tě nutí plán prezentovat dřív než exekvuješ.

**Vyzvi uživatele, ať přepne:**

> „Pro nejbezpečnější instalaci stiskni v terminálu **Shift+Tab** a přepni se do plan modu. V něm můžu jen prezentovat plán - nic nespustím, dokud ho neschválíš. Jakmile Shift+Tab stiskneš, řekni mi, a napíšu plán."

Počkej, až uživatel potvrdí, že přepnul. (Sám plan mode nemusíš spolehlivě detekovat - spolehni se na jeho potvrzení.)

**Pak spusť Krok 1 (read-only pre-flight) a napiš plán.** Dobrý plán shrnuje:
- Výsledky OS + dependency kontroly (z Kroku 1 - čistě read-only, smí běžet i bez schváleného plánu)
- Jestli zálohovat stávající `~/.claude/` a kam
- Workspace location a názvy adresářů
- Které soubory se zkopírují, kam, a co zůstává netknuté
- Které credential / personalizační otázky zbývají
- Přesný seznam příkazů, které spustíš, v pořadí

V plan modu prezentuj plán přes `ExitPlanMode`. Uživatel ho tam schválí, plan mode skončí, ty vykonáš. **Neimprovizuj mimo plán.** Když se objeví něco neočekávaného, zastav, aktualizuj plán, znovu potvrď.

**Pokud uživatel plan mode odmítne** (řekne, že nechce přepínat, neumí najít Shift+Tab, nebo prostě „jeď bez něj"):

1. Vytvoř `./INSTALL-PLAN.md` v aktuálním adresáři (klonovaný Pack folder).
2. Napiš tam stejný plán.
3. Uživateli ho ukaž v terminálu (vypiš obsah nebo shrň a odkaž).
4. Počkej na explicit schválení: „ano", „OK", „pokračuj", „approve", nebo podobně.
5. Teprve po souhlasu začni vykonávat.
6. Po dokončení instalace (Krok 11) `./INSTALL-PLAN.md` smaž - pracovní artefakt, ne výstup.

V obou cestách: **žádná destruktivní akce ani kopírování neproběhne, dokud uživatel neschválí písemný plán.** Krok 1 (read-only kontroly) je jediná věc, která smí běžet před plánem.

---

## Step 1 - Pre-flight check

Run these checks and report results in a single message.

### 1a. Detect OS

```bash
uname -s
```

- **Darwin** → macOS, all instructions apply as written.
- **Linux** → adjust paths if user uses non-standard `~/Documents/` location; otherwise same as macOS.
- **MINGW / MSYS / CYGWIN** or PowerShell → **Windows.** Stop and tell the user:

  > Tento Pack předpokládá Unix-like shell. Na Windows je nejčistší cesta **WSL2** (Ubuntu z Microsoft Store, Claude Code uvnitř WSL, Pack pak funguje jako na Linuxu).
  >
  > Nativní Windows je možný, ale vyžaduje ruční úpravy cest (`%USERPROFILE%` místo `$HOME`, zpětná lomítka, žádné symlinks bez admin), Bash hooky se musí přepsat na PowerShell nebo spouštět přes Git Bash. Pro první instalaci to nedoporučuju.
  >
  > Co chceš: (a) ukončit a nainstalovat WSL2, (b) pokračovat na nativním Windows i tak?

  Pokud volí (b), pokračuj podle Windows addendum na konci tohoto souboru.

### 1b. Detect required binaries

```bash
for tool in python3 node git jq curl; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s ✓ (%s)\n' "$tool" "$("$tool" --version 2>&1 | head -n1)"
  else
    printf '%s ✗ MISSING\n' "$tool"
  fi
done
```

If **all present**, continue.

If **anything is missing**, stop and give the user OS-specific install commands. Do NOT install dependencies yourself - that's a system change that needs the user's explicit choice of how to manage their package manager.

**macOS - recommended via Homebrew:**
```bash
# If brew itself is missing:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then:
brew install python3 node git jq curl
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install -y python3 nodejs git jq curl
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install -y python3 nodejs git jq curl
```

After the user installs missing tools, run the check again. Do not proceed until all five pass.

### 1c. Detect existing setup

Run in parallel:

```bash
ls -la ~/.claude/ 2>/dev/null | wc -l
ls -la ~/.claude/settings.json 2>/dev/null
ls -la ~/.claude/.env 2>/dev/null
```

Report: does `~/.claude/` exist, is there a `settings.json`, is there a `.env`. These all matter for the backup step.

---

## Step 2 - Workspace location interview (BEFORE touching ~/.claude/)

This is the most important preference question. The Pack ships with four workspace directories - `_CONTEXT`, `_CLIENTS`, `_BUSINESS`, `_APPS` - and you must NOT assume where they go. Different users want them in different places. **Frame it as a proposal, not a fixed layout** - present the structure as the pack's suggestion and explicitly invite the user to shape it: "tohle je navrhovaná struktura, pojďme ji probrat a nastavit, jak to chceš mít ty."

Ask the user:

> Pack obsahuje čtyři workspace adresáře:
> - `_CONTEXT/` - tvůj osobní profil, poznámky, best-practices a povinný `llms/` kontext pro agentní práci
> - `_CLIENTS/` - per-klient složky
> - `_BUSINESS/` - vlastní byznys (projekty, vzdělávání, interní)
> - `_APPS/` - nástroje a appky, které stavíš
>
> **Kam je chceš umístit?**
> 1. `~/Documents/` (default - viditelné ve Finderu, snadné mít přes ruku)
> 2. `~/` (přímo v home directory)
> 3. `~/Documents/Work/` nebo jiná podsložka - řekni jakou
> 4. Mimo home, např. `/Volumes/Work/` (externí disk) nebo `~/Code/`
>
> Cesty s mezerami fungují, ale doporučuju je nepoužívat - Bash je nemá rád.

Store the chosen base path. **Use it for the rest of the install.** Never fall back to `~/Documents/` after they chose something else.

### 2a. Optional renaming

```
Chceš některý z adresářů přejmenovat?
- Některým lidem podtržítkový prefix (_CLIENTS/) pomáhá vizuální sort. Jiným vadí.
- Někdo preferuje plain anglické: clients/, business/, apps/, context/.
- Někdo česky: klienti/, byznys/, appky/, kontext/.

Pošli mi čtyři jména oddělená mezerou pro CONTEXT CLIENTS BUSINESS APPS - nebo Enter pro defaults.
```

Use whatever they say. From this point on, refer to directories by the user's chosen names - not by the defaults.

### 2b. Conflict check

For each chosen directory, check if it already exists at the chosen base path:

```bash
for dir in <name1> <name2> <name3> <name4>; do
  if [ -e "<base-path>/$dir" ]; then echo "EXISTS: $dir"; else echo "free: $dir"; fi
done
```

If any exist: **never overwrite.** Tell the user, and offer:
1. Skip that one (don't copy from the Pack, keep the user's existing content)
2. Rename the Pack's version (e.g. add `-new` suffix) so the user can merge manually
3. Abort and let the user move/rename their existing dir first

---

## Step 3 - Backup existing `~/.claude/`

If `~/.claude/` exists from Step 1c, propose:

```bash
cp -r ~/.claude ~/.claude.bak-$(date +%Y%m%d-%H%M%S)
```

Get user approval. After backup, report the backup path.

If `~/.claude/` does not exist, skip this step and tell the user.

---

## Step 4 - Install kernel

Show the user what will be copied:

```
kernel/ → ~/.claude/
```

Contents going in:
- `settings.json` - restrictive baseline; bypass mode locked off
- `AGENTS.md` + `CLAUDE.md` (symlink)
- `statusline.sh` - 3-line status bar (model · cost / project · ctx / 5h · 7d rate limits)
- `rules/` - four rules (documentation, respect-denies, subagents, language)
- `reference/frontmatter-standard.md` - the frontmatter standard, read on demand, not auto-loaded
- `scripts/list-env-keys.sh` - lets Claude see *names* of credential env vars without values
- `hooks/`:
  - `bash-safety-extended.py` (PreToolUse Bash and Read) - blocks bypass patterns and reads of protected env files
  - `context-bloat-guard.py` (PreToolUse Read) - soft brake on huge file reads
  - `inject-current-time.sh` (UserPromptSubmit) - current time in every prompt
- `skills/setup/`, `skill-creator/`, `prd-creator/`, `dr-prompt/`, `client-data-check/`, `idea-file-creator/`
- `templates/` - five scaffolding templates (klient, dev, business, app, general), the `.env.example` files the setup skill copies, and `claude-env.example` for Step 8
- `agents/` - `research-analyst` + README

**Critical - existing setup: analyze, recommend, don't overwrite.** If `~/.claude/settings.json` (or a `rules/`/`hooks/` directory) already existed in the backup, do NOT blindly replace it. First read the user's existing config - permissions, hooks, env, rules - and compare it against what this pack ships. Then present a tailored, area-by-area recommendation: what of theirs is worth keeping, what the pack adds that's worth adopting, where the two overlap or conflict, and a suggested result tuned to how this user actually works (ask briefly if it's not obvious). The user decides per area; then write the agreed result. Replace wholesale only if there is nothing meaningful there or they ask for it. The backup protects the original either way - the install never auto-merges JSON, so the merged result is written explicitly.

**Leftover from an older pack version.** If the existing `settings.json` still has a `PostToolUse` entry that runs `notes-research.sh`, it comes from an earlier version of this pack, which has since dropped that hook: it did not work on a fresh install, and a working version would send the text of every note to the Anthropic API at a cost. Include it in the recommendation: remove that entry, and move `~/.claude/hooks/notes-research.sh` and `~/.claude/rules/notes-convention.md` (if present) to a backup path, because the copy below does not delete old files. The user decides, as with every other area. Their `notes.md` files stay as they are.

Execute the copy:

```bash
cp -r kernel/. ~/.claude/
chmod +x ~/.claude/scripts/*.sh ~/.claude/hooks/*.{sh,py} ~/.claude/statusline.sh
```

Re-create the `~/.claude/CLAUDE.md` symlink (it may not have copied as a symlink):

```bash
cd ~/.claude && ln -sfn AGENTS.md CLAUDE.md
```

Verify:

```bash
ls -la ~/.claude/CLAUDE.md
```

Should show `CLAUDE.md -> AGENTS.md`.

---

## Step 5 - Personal profile interview

The `user-profile.md` file in `<context-dir>/` is read by Claude in every session, through an import Step 7b adds to `~/.claude/AGENTS.md`. The more accurate it is, the more tailored the work.

Quick interview - 4 questions, 1–2 sentences each, or "skip" to leave blank:

```
1. Tvoje role a hlavní zaměření?
   (např. „PPC specialista v agentuře, učím se Python automatizace" nebo „Strategist, vedu klientské transformace")

2. S jakými technologiemi / AI nástroji nejvíc pracuješ?
   (např. „Google Sheets, BigQuery, Claude Code, někdy n8n")

3. Jaký styl komunikace ode mě chceš?
   - terse / balanced / detailed
   - mám ti přímo říkat, když je tvůj plán špatný? (ano / ne)

4. Jaký jazyk pro vlastní práci?
   (např. „česky klientské dokumenty a poznámky, anglicky kód a systémové soubory")
```

Keep the answers; do not write any file yet. The context directory does not exist until Step 7 copies the workspace, and Step 7 skips every directory that already exists, so creating `user-profile.md` now would stop the whole context directory from being copied. Step 7b writes the file and makes every session load it.

---

## Step 6 - Example content choice

```
Pack obsahuje příklady, které můžeš nechat, přejmenovat nebo smazat:
- `_CLIENTS/_example-client/` - sample klientská struktura
- `_CLIENTS/taste/` - připravený scaffold pro Taste (klient autorů Packu)
- `_APPS/_example-app-transcribe/` - stub appka demonstrující `_APPS` layout

Co s nimi?
1. Nech vše (default - referenční)
2. Přejmenuj `_example-client` na reálné jméno klienta (řekni které)
3. Smaž příklady, ponech `taste/`
4. Smaž všechny příklady včetně `taste/` - začneš čistě
```

Keep the choice (and, for choice 2, the client's name); do not move or rename anything yet. The examples do not exist under `<base-path>` until Step 7 copies the workspace. Step 7c applies the choice right after the copy.

---

## Step 7 - Workspace copy

Copy the workspace directories using the user's chosen paths and names from Step 2:

```bash
mkdir -p "<base-path>"
# For each: cp -r workspace/<default-name>/ → <base-path>/<chosen-name>/
```

**Never overwrite an existing top-level directory.** If `<base-path>/<chosen-name>` already exists, skip and tell the user (already flagged in Step 2b).

After copy, re-create AGENTS.md ↔ CLAUDE.md symlinks in each project subfolder. Symlinks may not survive `cp` cleanly:

```bash
# Find every AGENTS.md and ensure CLAUDE.md sibling is a symlink to it
find "<base-path>" -name 'AGENTS.md' -not -path '*/node_modules/*' | while read -r agents; do
  dir=$(dirname "$agents")
  if [ ! -L "$dir/CLAUDE.md" ]; then
    (cd "$dir" && ln -sfn AGENTS.md CLAUDE.md)
  fi
done
```

### 7a - Tell the git safety net where the workspace lives

`~/.claude/scripts/git-autosave.sh` (the local git safety net `/setup` turns on) works only inside the workspace root and does nothing anywhere else. It reads that root from `PACK_WORKSPACE_ROOT`, falling back to `~/Documents`. Write the base path from Step 2 into the `env` block of `~/.claude/settings.json`. **Merge, never overwrite** - the file already holds permissions, hooks and the statusline:

```bash
python3 - "<base-path>" <<'EOF'
import json, os, sys
from pathlib import Path
root = os.path.abspath(os.path.expanduser(sys.argv[1]))
p = Path.home() / ".claude" / "settings.json"
s = json.loads(p.read_text()) if p.exists() else {}
s.setdefault("env", {})["PACK_WORKSPACE_ROOT"] = root
p.write_text(json.dumps(s, indent=2))
print("PACK_WORKSPACE_ROOT ->", root)
EOF
```

The value applies from the next session, which the Step 9 restart covers.

### 7b - Write the user profile and load it in every session

Write the Step 5 answers into `<base-path>/<context-dir>/user-profile.md` (the copy Step 7 just made), replacing the empty placeholders in the template. If Step 2b kept the user's own context directory, merge the answers into their existing file only after they confirm; never overwrite it.

Then make every session load the profile. Nothing else reads it: append an `@` import of the file to `~/.claude/AGENTS.md` (Claude Code reads it through the `CLAUDE.md` symlink), plus one line that points Claude at the user's best practices. The snippet turns the context directory into an absolute path (resolving `~`) and adds each line only if it is not there yet, so a re-run never duplicates it:

```bash
python3 - "<base-path>/<context-dir>" <<'EOF'
import os, sys
from pathlib import Path
ctx = os.path.abspath(os.path.expanduser(sys.argv[1]))
p = Path.home() / ".claude" / "AGENTS.md"
wanted = [
    f"@{ctx}/user-profile.md",
    f"Before generic advice on a recurring topic, check {ctx}/best-practices/ for the user's own approach.",
]
text = p.read_text()
missing = [line for line in wanted if line not in text.splitlines()]
if missing:
    p.write_text(text.rstrip("\n") + "\n\n" + "\n".join(missing) + "\n")
print("added:" if missing else "already present:", *(missing or wanted), sep="\n")
EOF
```

### 7c - Apply the example content choice

The workspace now exists, so apply the Step 6 choice. Choice 1 needs nothing. Skip any directory Step 2b kept as the user's own: its examples were never copied.

Choice 2 renames the example client to the real name, only if that name is still free:

```bash
if [ -e "<base-path>/<clients-dir>/<client-name>" ]; then
  echo "EXISTS: <client-name> - ask the user for another name"
else
  mv "<base-path>/<clients-dir>/_example-client" "<base-path>/<clients-dir>/<client-name>"
fi
```

Choices 3 and 4 remove examples by moving them to a backup path, never `rm -rf`. Run the lines for the examples the user dropped; the `taste` line belongs to choice 4 only. Each line skips an example that is already gone, so a re-run does not fail:

```bash
mkdir -p "<base-path>/.removed-examples"
[ -e "<base-path>/<clients-dir>/_example-client" ] && mv "<base-path>/<clients-dir>/_example-client" "<base-path>/.removed-examples/$(date +%Y%m%d-%H%M%S)-example-client"
[ -e "<base-path>/<apps-dir>/_example-app-transcribe" ] && mv "<base-path>/<apps-dir>/_example-app-transcribe" "<base-path>/.removed-examples/$(date +%Y%m%d-%H%M%S)-example-app-transcribe"
[ -e "<base-path>/<clients-dir>/taste" ] && mv "<base-path>/<clients-dir>/taste" "<base-path>/.removed-examples/$(date +%Y%m%d-%H%M%S)-taste"
true
```

Tell the user where the removed examples went (`<base-path>/.removed-examples/`).

---

## Step 7.5 - Install Taste AI Quality Kit

Optional. Three workflows ship as one plugin: help with writing a prompt, evaluation of a prompt on real examples, and a read-only review of someone else's skill before it is trusted. The plugin is installed from the plugin source declared in this repository - it is never copied into the kernel. Run this step after Step 7, because the plugin needs the context directory the workspace copy just created.

Explain the split before installing anything:

> Tahle část je volitelná a přidá ti tři věci: pomoc s psaním promptů, vyhodnocení promptu na reálných příkladech, a kontrolu cizího skillu dřív, než ho pustíš k sobě do počítače.
>
> Rozdělené je to takhle: plugin drží postup a bezpečnostní kontroly. Tvoje složka `llms/` drží znalost o modelech - které používáš, jak se který promptuje a co sis u sebe rozhodl. Tu složku si vedeš ty a průběžně ji aktualizuješ, protože znalost o modelech zastarává rychleji než jakýkoli balíček. Plugin do ní nikdy nesahá.
>
> Mám to nainstalovat?

Wait for a yes. Then run the three commands:

```bash
claude plugin marketplace add hradniai/claude-code-pack-taste
claude plugin install taste-ai-quality-kit@claude-code-pack-taste
claude plugin list
```

The first line registers the public GitHub repository as a plugin source named `claude-code-pack-taste`, the second installs the plugin from it, the third confirms it is there. Because the source is GitHub, later updates need no clone (see Step 11). `claude plugin install ./plugins/taste-ai-quality-kit` does not work - `claude plugin install` installs from a registered source only, never from a bare folder path.

Fallback, only when GitHub is unreachable or the user installs from a fork or a locally changed clone: run `claude plugin marketplace add "$(pwd)"` from the cloned Pack folder instead of the first line, then the same two remaining lines. That source reads from the clone, so the clone must stay on disk.

### 7.5a - Point the plugin at the user's context directory

The plugin finds the context directory through `TASTE_LLM_CONTEXT_DIR`. Write it into the `env` block of `~/.claude/settings.json`, which Step 4 installed. Claude Code applies that block to every session, including the scripts a session runs, so nothing in a shell profile needs editing. **Merge, never overwrite** - the file already holds permissions, hooks and the statusline:

```bash
python3 - "<base-path>/<chosen-context-dir>/llms" <<'EOF'
import json, sys
from pathlib import Path
p = Path.home() / ".claude" / "settings.json"
s = json.loads(p.read_text()) if p.exists() else {}
s.setdefault("env", {})["TASTE_LLM_CONTEXT_DIR"] = sys.argv[1]
p.write_text(json.dumps(s, indent=2))
print("TASTE_LLM_CONTEXT_DIR ->", sys.argv[1])
EOF
```

Verify the one key:

```bash
python3 -c "import json,pathlib;print(json.load(open(pathlib.Path.home()/'.claude'/'settings.json'))['env']['TASTE_LLM_CONTEXT_DIR'])"
```

The value applies from the next session, which the Step 9 restart covers.

### 7.5b - Tell the user what is theirs to maintain

> Ve složce `llms/` máš tři soubory: `models.md` (modely, které používáš), `prompting.md` (jak se který z nich promptuje) a `decisions.md` (co sis u sebe rozhodl a proč). Teď jsou prázdné a plugin to pozná - dokud je nevyplníš, práci odmítne a řekne ti, který soubor mu chybí. Je to schválně: radši nic než rada podle půl roku starých informací.
>
> Vedle nich leží ještě čtyři referenční dokumenty: `model-lineup.md`, `model-reference-prompting.md`, `ai-prompt-guidelines.md` a `codex-cli-reference.md`. Každý má uvnitř datum poslední kontroly a při vyplňování z nich můžeš vycházet. Plugin je nečte, řídí se jen tvými třemi soubory.
>
> Vyplnit je můžeme spolu. Kdykoli mi řekni „pojďme dopsat `models.md`", společně dohledáme aktuální informace a zapíšeme je. Vedeš si je ale ty, plugin ti je nikdy nepřepíše ani nedoplní.

Each of the three files starts with `status: TODO` in its header. That marker is what keeps the plugin closed (it reports `CONTEXT_NOT_READY`), so it stays there until the user replaces the placeholder text with real records. The four dated reference documents ship beside them only as a starting point; the plugin reads the three records and nothing else.

### 7.5c - Keys, only when the user wants a live evaluation

A live evaluation sends the prompt to a model, which needs an access key. The keys live in `llms/.env`, next to the three files. Create it from the template only when the user asks for a live run:

```bash
[ -f "<base-path>/<chosen-context-dir>/llms/.env" ] || cp "<base-path>/<chosen-context-dir>/llms/.env.example" "<base-path>/<chosen-context-dir>/llms/.env"
chmod 600 "<base-path>/<chosen-context-dir>/llms/.env"
```

Then:

> Do souboru `.env` si vlož přístupové klíče k modelům, které chceš používat - je to dlouhý kód, kterým se u poskytovatele modelu prokážeš. Otevři si ho v editoru a vlož je tam sám. Do chatu mi je neposílej, já se do jejich hodnot nedívám a v žádném výstupu se neobjeví.
>
> Klíč potřebuješ jen pro ty modely, které v daném běhu opravdu použiješ. První ostrý běh si plugin sám připraví, co potřebuje - trvá to asi minutu a nic přitom nespouštíš ručně.

On Linux or WSL2 only: Claude Code and Codex as evaluation judges need the `bubblewrap` package (`sudo apt install bubblewrap` on Debian and Ubuntu). Tell the user in one Czech sentence and let them run it themselves; without it those two judges refuse to run and the report says why (the model judges over the network keep working). On macOS nothing is installed.

---

## Step 8 - Credential store (`~/.claude/.env`)

`~/.claude/.env` is the optional central store for the user's own account-level keys: the ones that scripts and automations they add later need across workspaces. Nothing the Pack ships needs a key from it. The Quality Kit keeps its keys in `<context-dir>/llms/.env` (Step 7.5c), and a project's runtime keys go in that project's `.env`. The `list-env-keys.sh` helper lets Claude see the *names* of keys stored here (not values) when needed.

If `~/.claude/.env` doesn't exist, create it from the starter template Step 4 copied into `~/.claude/templates/` (an existing file is left as it is):

```bash
[ -f ~/.claude/.env ] || cp ~/.claude/templates/claude-env.example ~/.claude/.env
chmod 600 ~/.claude/.env
```

The template holds commented example key names only, no values.

Claude never reads or echoes the values in this file, so the user fills in any key themselves. Tell them:

> Do souboru `~/.claude/.env` si můžeš ukládat vlastní přístupové klíče, které budou potřebovat skripty a automatizace, co si časem přidáš. Pack sám z něj nic nepotřebuje, takže ho klidně nech prázdný. Až tam budeš klíč vkládat, otevři si soubor v editoru (na Macu třeba příkazem `open -e ~/.claude/.env`) a vlož ho sám. Do chatu mi ho neposílej, do hodnot v tomhle souboru se nedívám.

Show how the env-keys helper works:

```bash
~/.claude/scripts/list-env-keys.sh
```

Any credentials the user added appear by name. Values never appear in the output.

### The one readable env file - `.env.shared`

`~/.claude/.env` above is the GLOBAL credential store for the user's account-level keys; Claude never reads its values. The model has three tiers: the global `~/.claude/.env` and every project `.env` / `.env.local` / `.env.production` / `.env.*` are HARD - Claude never reads their values (`.env.local` is HARD on purpose; the JS ecosystem treats it as the live-secret file, so live keys land there). The single readable env file is **`.env.shared`** - the soft tier for low-risk values safe to surface (a notify webhook, a contact email). The deny rules plus the `bash-safety-extended.py` hook block reading every HARD `.env` / `.env.*` (via `cat`, `source`, redirection, `python -c`, docker bind-mount, or the Read tool). A real secret is never read by Claude - a program uses it without revealing the value. To see only the key NAMES of any HARD env file, Claude runs `~/.claude/scripts/list-env-keys.sh --from <path>` (add `--classify` for each key's state). Scope note: only commands that read the *values* into view are blocked (`cat`, `source`, redirection, `python -c ...read()`); passing the file as config (`--env-file`), copying a template, or mentioning it in text all pass, so deploys and setup are not blocked.

---

## Step 8.5 - Pre-trust the workspace (optional, stops the folder-trust nag)

On first launch in any directory, Claude Code shows **"Do you trust the files in this folder?"** and the user must accept. This is a deliberate safety gate; there is no `settings.json` key or safe env var to disable it (bypass mode would skip it, but it is locked off here on purpose). The supported way to stop the repeated prompt for directories the user already trusts is to pre-write the per-directory trust flag into `~/.claude.json`. The kernel ships `~/.claude/scripts/trust-workspace.sh` for exactly this.

Offer to pre-trust the workspace base path from Step 2 and each directory created in the workspace copy:

```bash
~/.claude/scripts/trust-workspace.sh <base-path>/<chosen-dir-1> <base-path>/<chosen-dir-2>
```

- It backs up `~/.claude.json`, merges (never overwrites), and validates JSON before saving.
- It weakens nothing else: normal permission prompting and `disableBypassPermissionsMode` stay fully in force. It only persists "yes, I trust this folder" up front, exactly as clicking Yes would.
- Brand-new directories opened later still prompt once - correct for a safety baseline. Re-run the script for those, or just accept once.
- The install session is itself a Claude Code session, so if the prompt persists after the Step 9 restart, have the user run the command once more from a plain terminal (a running session can overwrite `~/.claude.json` on exit).

---

## Step 9 - Verification

Tell the user to **restart their Claude Code session** so the new `settings.json` takes effect. After restart, they can verify:

- `~/.claude/scripts/list-env-keys.sh` returns env var names without values
- A denied command (e.g. asking Claude to `cat .env`) gets blocked, but a deliberate `.env.shared` is readable (the single readable soft tier)
- Bypass mode is off - `claude --permission-mode bypassPermissions` should refuse
- The current-time injection works - at session start, Claude should know the actual time
- Statusline appears at the bottom with model · cost · context · rate-limit info
- If Step 7.5 ran: `claude plugin list` shows `taste-ai-quality-kit@claude-code-pack-taste` as enabled, and asking Claude „pomoz mi napsat prompt" answers with which `llms/` file still needs filling in (that refusal is the plugin working as designed)

---

## Step 10 - Confirm the settings lock

`settings.json` already ships `Edit(~/.claude/settings*)` in `permissions.ask`, so Claude asks the user before its Edit or Write tool changes `~/.claude/settings.json`. Confirm the rule survived the install (a hand-merged file from Step 4 could have dropped it):

```bash
jq '(.permissions.ask // []) | any(. == "Edit(~/.claude/settings*)")' ~/.claude/settings.json
```

It should print `true`. If it prints `false`, the Step 4 merge lost the rule: put it back into `permissions.ask` with the user's approval.

Tell the user plainly what the lock covers: it gates the Edit and Write tools only. A script run through Bash can still write the file, exactly as Steps 7a and 7.5a did with the user's approval of the plan, which is why the `respect-denies` rule forbids that route for any settings change the user has not approved.

---

## Step 11 - Hand off

Tell the user:

> Hotovo. Doporučuju:
> - Nainstalovat **[Warp](https://www.warp.dev/)** jako terminál - přehlednější a přívětivější příkazová řádka. Výhody: file explorer hned vedle terminálu, normální zadávání textu (píšeš jako v editoru, bez terminálových výstředností), přehlednější organizace oken a snazší navigace ve složkách. Claude Code v něm běží úplně stejně. Ve free verzi v úvodním nastavení **vypni vlastní AI Warpu** - když používáš Claude Code, AI od Warpu nepotřebuješ.
> - Přečíst `docs/safety-model.md` - co všechno se blokuje a proč.
> - Přečíst `docs/customization.md` - jak Pack rozšiřovat.
> - Přečíst `docs/prompting-claude.md` - tipy na práci s Claude.
>
> Tento repo můžeš teď smazat - všechno je nainstalováno v `~/.claude/` a tvých workspace adresářích. Jestli sis nainstaloval i plugin (krok 7.5), nové verze stáhneš dvěma příkazy, `claude plugin marketplace update claude-code-pack-taste` a `claude plugin update taste-ai-quality-kit@claude-code-pack-taste`. Naklonované repo k tomu nepotřebuješ.

If Step 7.5 used the local-folder fallback, drop the "smazat" advice instead: that plugin source reads from the clone, so the user keeps it and, for an update, runs `git pull` in it before the same two commands.

The Warp recommendation is written Mac-first (Warp's original ecosystem). Warp also ships a Windows build, so if the user is on Windows, point them at the Windows download and adapt - do not present it as Mac-only.

End the install session. Do not proceed to other tasks unless the user asks.

---

## Error handling - global rules

- If any step fails, stop. Do not continue to the next step.
- If a permission denial occurs during install (e.g. user runs from a path that doesn't allow writes), surface it clearly and propose a fix.
- Never run `rm -rf` during install. Use `mv` to a backup path.
- Never use `sudo`. If something requires it, instruct the user to run that one line manually.

---

## Windows native (without WSL) - addendum

If the user chose Windows native despite the WSL recommendation:

- Replace `~/.claude/` with `%USERPROFILE%\.claude\` (`$env:USERPROFILE\.claude\` in PowerShell)
- Replace `~/Documents/` similarly
- Symlinks require admin rights - instead of `ln -s AGENTS.md CLAUDE.md`, create a hard link or just copy the file (two files to keep in sync - flag this to the user)
- `chmod +x` is a no-op on Windows. PowerShell scripts need `Unblock-File` before first run
- Bash hooks (`*.sh`) won't run natively - they need Git Bash, WSL, or a PowerShell rewrite
- `~/.claude/.env` is a regular file. PowerShell env loading differs; the user will need to source it manually or via a profile script

Strongly recommend WSL2. The Pack assumes Unix conventions throughout - fighting Windows native is more work than installing WSL.
