# pi-quant-toolkit

[![CI](https://github.com/nealcaren/pi-quant-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/nealcaren/pi-quant-toolkit/actions/workflows/ci.yml)

An AI research assistant for **quantitative social science**. You describe a task
in plain English — "run a difference-in-differences on this data," "find recent
papers on protest and add them to my Zotero" — and it does the work.

Built for students. No coding experience needed. Never used a terminal? This
guide walks you through every step.

---

## What you need before you start

1. **Node.js** — free software this runs on. Download the **"22 LTS"** button
   from [nodejs.org](https://nodejs.org), open the installer, and click through
   it (keep every default). That's it — no typing.
2. **An OpenRouter account** — this is what pays for the AI, a few cents at a
   time. Make one at [openrouter.ai](https://openrouter.ai) and add a few dollars
   of credit. You'll connect it at the end.

That's all for the main tools. (Literature search needs two more things — see
[Literature search setup](#literature-search-setup) below.)

---

## Install it (one command)

**Step 1 — open a terminal.** A terminal is a window where you type commands.

- **Mac:** press `Cmd` + `Space`, type `Terminal`, press `Enter`.
- **Windows:** click the Start menu, type `PowerShell`, press `Enter`.

**Step 2 — copy the line for your computer, paste it into that window, press
`Enter`.** (Paste is `Cmd`+`V` on Mac, right-click on Windows.)

**Mac:**
```bash
curl -fsSL https://raw.githubusercontent.com/nealcaren/pi-quant-toolkit/main/setup.sh | bash
```

**Windows:**
```powershell
irm https://raw.githubusercontent.com/nealcaren/pi-quant-toolkit/main/setup.ps1 | iex
```

It installs everything and picks a cheap AI model for you. Wait for it to finish
(about a minute) and print "All set!"

**Step 3 — connect OpenRouter.** In the same window, type:
```
pi
```
Pi opens. Type `/login openrouter` and press `Enter`, then follow the prompt to
sign in. Done — you only do this once.

---

## Use it

1. Put the files you're working with in a folder (e.g. a folder for your paper).
2. Open a terminal **in that folder**:
   - **Mac:** right-click the folder → *Services* → *New Terminal at Folder*.
   - **Windows:** open the folder, click the address bar, type `powershell`, `Enter`.
3. Type `pi` and press `Enter`.
4. Describe what you want. Pi picks the right tool automatically:

> *"Set up a new project for my dissertation chapter."*
> *"Run a difference-in-differences on this panel in R."*
> *"Find recent work on protest and social media and add the best to my Zotero."*

Stuck on a hard analysis? Type `/model deepseek/deepseek-v4-pro` to switch to a
smarter (slightly pricier) model for that session.

---

## What's inside

| Tool | What it does |
|------|--------------|
| `r-analyst` | Statistical analysis in R (DiD, IV, matching, panel, etc.) |
| `stata-analyst` | The same, in Stata |
| `text-analyst` | Text analysis (topic models, sentiment, classification) in R or Python |
| `project-scaffold` | Sets up a tidy research-project folder for you |
| `lit-search` | Finds papers via OpenAlex/Crossref and files them into Zotero |
| `tidy-r` | Modern-tidyverse conventions so your R code isn't dated base R |
| `review-r` | Reads your R code and reports problems (doesn't change it) |

---

## Always review your code — and switch models to do it

The AI writes code fast, but **you should never trust an analysis you haven't
checked.** Two habits that catch most mistakes:

**1. Ask for a review.** When a script is done, say:

> *"Review this R script for correctness and reproducibility."*

That runs `review-r`, which reports problems (wrong clustering, non-reproducible
paths, numerical bugs) **without changing your code** — you decide what to fix.

**2. Review with a *stronger, different* model than wrote the code.** A model
checking its own work tends to bless its own mistakes. Before reviewing, switch:

```
/model deepseek/deepseek-v4-pro
```

Even better, if you have access, review with a **different** model family than
you wrote with — a fresh set of eyes catches what the original missed. Switch
back to the cheap model (`/model deepseek/deepseek-v4-flash-0731`) for routine
work afterward.

---

## Good to know

**It acts on its own.** Pi runs commands and edits files without asking first.
That's normal, but:

- Work **inside a project folder**, not your whole computer.
- Glance at what it's doing; if something looks wrong, press `Esc` to stop it.
- Keep your work backed up (or in version control) so anything is easy to undo.

**It costs money per use** — cheap, but real. Watch your credit on
[openrouter.ai](https://openrouter.ai). The default model is very inexpensive.

---

## Literature search setup

`lit-search` needs two extra things:

- **[uv](https://docs.astral.sh/uv/)** — runs a small helper. Install it by
  pasting one line into your terminal:
  - Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `irm https://astral.sh/uv/install.ps1 | iex`
- **Zotero desktop** — your reference library.

When adding references, **quit Zotero first** (Pi won't write while it's open, to
protect your library) and it makes a timestamped backup before its first change.
New references show up next time you open Zotero.

---

<details>
<summary>Advanced: manual install & troubleshooting</summary>

**Install without the one-line script:**
```bash
npm install -g @earendil-works/pi-coding-agent@latest
pi install git:github.com/nealcaren/pi-quant-toolkit@main
```

**"undici" / `markAsUncloneable` crash on startup** — your Node.js is too old.
Pi needs **22.19+**. Reinstall the 22 LTS from [nodejs.org](https://nodejs.org),
open a new terminal, and try again.

**Tool "…" conflicts errors** — you're running `pi` from *inside* the toolkit's
own source folder. Run it from your project folder instead.

**An extension didn't load** — check with `/extensions` inside pi, then:
```bash
pi install npm:pi-web-access
pi install npm:@juicesharp/rpiv-ask-user-question
pi install npm:@plannotator/pi-extension
```

**Run read-only** (no edits or commands) for a task:
`pi --tools read,grep,find,ls`

**Change your default model** anytime with `/model` inside pi, or by editing
`~/.pi/agent/settings.json`.

</details>

## License

MIT. The bundled skills derive from the `sociology-skillset` project.
