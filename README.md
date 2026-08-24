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

```bash
# 1. Install Pi
npm install -g @earendil-works/pi-coding-agent   # provides the `pi` command

# 2. Point Pi at OpenRouter (either OAuth or an API key)
pi   # then run:  /login openrouter
# ...or set a key in your shell:
export OPENROUTER_API_KEY=sk-or-...

# 3. Install this package
pi install git:github.com/<your-org>/pi-quant-toolkit@main
```

> Replace `<your-org>` with wherever this repo is hosted.

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

## License

MIT. The bundled skills derive from the `sociology-skillset` project.
