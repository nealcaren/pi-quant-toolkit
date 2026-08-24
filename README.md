# pi-quant-toolkit

A [Pi](https://pi.dev) coding-agent package for **quantitative social science**.
It bundles analysis skills (R, Stata, computational text analysis, project
scaffolding) plus a literature-search skill that finds work through OpenAlex /
Crossref and files chosen references directly into your **local Zotero library**.

Built for grad students: install once, run against a cheap pay-as-you-go model.

---

## What's inside

| Skill | What it does |
|-------|--------------|
| `r-analyst` | Publication-ready statistical analysis in R (DiD, IV, matching, panel, etc.), phased workflow |
| `stata-analyst` | The same, in Stata |
| `text-analyst` | Computational text analysis (topic models, sentiment, classification, embeddings) in R or Python |
| `project-scaffold` | Initialize a standard research-project directory + metadata files |
| `lit-search` | Search OpenAlex/Crossref, then add chosen references straight into local Zotero |

These are analysis + capture tools. There are no writing skills in this bundle.

---

## Prerequisites

1. **Node.js 20+** — Pi runs on Node. <https://nodejs.org>
2. **[uv](https://docs.astral.sh/uv/)** — runs the Python helper scripts
   (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
3. **R and/or Stata** — only if you use those analysis skills.
4. **Zotero desktop** — only for `lit-search`. Default library path
   `~/Zotero/zotero.sqlite`.
5. **An [OpenRouter](https://openrouter.ai) account + API key** — this is what
   you pay per token. Add a few dollars of credit to start.

---

## Install

The quick path — run the setup script (installs Pi, this package, and the
recommended extensions):

```bash
./setup.sh          # edit the PKG line first to point at your repo URL
```

Then connect OpenRouter (this is what you pay per token, via OAuth or a key):

```bash
pi   # then run:  /login openrouter
# ...or:
export OPENROUTER_API_KEY=sk-or-...
```

<details>
<summary>Or install by hand</summary>

```bash
npm install -g @earendil-works/pi-coding-agent      # the `pi` command
pi install git:github.com/<your-org>/pi-quant-toolkit@main
pi install npm:pi-web-access                        # web search + PDF/URL fetch
pi install npm:rpiv-ask-user-question               # structured clarifying questions
```
</details>

> Replace `<your-org>` with wherever this repo is hosted.

## Recommended extensions

Pi ships with a deliberately minimal core (`read`, `write`, `edit`, `bash`,
`grep`, `find`, `ls`) — no web access. The setup script adds two extensions that
matter for research work:

- **`pi-web-access`** — adds `web_search` and web/PDF fetching. Zero-config (uses
  Exa, no API key). Lets the agent look things up and read papers/pages by URL,
  which complements the OpenAlex/Crossref lookups in `lit-search`.
- **`rpiv-ask-user-question`** — makes the agent ask you a structured question at
  decision points instead of guessing. Helps the cheap default model respect the
  "confirm before searching / before adding to Zotero" checkpoints in the skills.

Both are optional — the skills work without them — but they noticeably improve
the experience on a budget model.

---

## Which model to use

This bundle assumes two OpenRouter models — a cheap default for everyday work and
a stronger one for hard analysis:

| Role | Model | When |
|------|-------|------|
| **Default (cheap)** | `deepseek/deepseek-v4-flash-0731` | Literature search, adding to Zotero, project setup, routine coding |
| **Escalate (smarter)** | `deepseek/deepseek-v4-pro` | Tricky econometrics, debugging a failing model, careful specification work |

```bash
# start cheap
pi --provider openrouter --model deepseek/deepseek-v4-flash-0731

# switch models mid-session when you hit something hard
/model deepseek/deepseek-v4-pro
```

Heads-up: these skills were originally written and tuned against Claude models.
They work on DeepSeek, but the Flash tier can stumble on the most involved
analysis steps — that's what the escalate model is for. Watch your OpenRouter
usage; agentic coding is cheap per action but token-hungry per session.

---

## Using it

Start Pi in your project directory and just describe the task — Pi loads the
matching skill automatically:

- *"Set up a new quantitative project for my dissertation chapter."* → `project-scaffold`
- *"Run a difference-in-differences on this panel in R."* → `r-analyst`
- *"Find recent work on protest and social media, then add the good ones to my Zotero 'Dissertation' collection."* → `lit-search`

### Adding to Zotero — read this once

`lit-search` writes references **directly into your Zotero database**. So:

- **Quit Zotero completely before adding items.** The script refuses to write
  while Zotero is open (the database is locked), to protect your library.
- It takes a **timestamped backup** of `zotero.sqlite` before its first write
  (look for `zotero.sqlite.pi-backup-*` next to your library if you ever need it).
- New references appear the next time you open Zotero and sync up normally.
- Reading your library (dedup checks, listing collections) is safe while Zotero
  is open; only *adding* needs it closed.

---

## A note on safety

Pi runs its tools **without asking permission first** — when the agent decides to
run a shell command or edit a file, it just does it. There's no sandbox by
default. That's normal for coding agents, but worth understanding:

- **Work in your project directory**, not your home folder or system files.
- **Skim what it's about to do.** The agent shows the commands it runs; if
  something looks destructive (deleting files, `sudo`, anything outside your
  project), stop it (Esc) and redirect.
- **Use version control.** `git init` your analysis project so any unwanted change
  is easy to undo.
- The `lit-search` Zotero step is the one place the agent writes outside your
  project — it edits your Zotero library, but only through the guarded script
  (Zotero must be closed, and it backs up the database first).

If you'd rather run read-only for a task (no editing or shell), start Pi with a
restricted tool set: `pi --tools read,grep,find,ls`.

## License

MIT. The bundled skills derive from the `sociology-skillset` project.
