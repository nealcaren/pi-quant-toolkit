# Project conventions for the agent

You are helping a social scientist with **quantitative analysis and literature
capture**. Follow these rules on top of whatever a loaded skill says.

## Analysis

- **Python scripts use `uv` with PEP-723 inline dependencies.** Every standalone
  script starts with a `# /// script` block; run it with `uv run <script.py>`.
  Do not call system `python` directly or `pip install` into the environment.
- **Reproducibility first.** Prefer scripts that can be re-run end to end over
  one-off interactive commands. Set seeds. Keep data, code, and output separate
  (the `project-scaffold` skill sets up canonical paths).
- **Never invent data, results, coefficients, or citations.** Report what the
  analysis actually produced, including when it fails or is inconclusive. If a
  model doesn't converge or an assumption is violated, say so.
- **Show the specification.** When you fit a model, state the estimator, sample,
  and key choices so the researcher can check them.
- **Output defaults: Word tables + colorblind-safe figures.** Unless the user or
  their target journal asks for LaTeX, produce tables in **Word format by default**
  (`.docx` via `modelsummary`/`flextable` in R; `.rtf`/`putdocx` via `esttab` in
  Stata) — most sociology journals want Word. Also write a `.tex` when it's cheap.
  **Every figure uses a colorblind-safe palette by default** — Okabe–Ito for
  categorical color, viridis for continuous/ordered (R); a colorblind-safe scheme
  (`blindschemes`/`stcolor`) in Stata. Don't hand-pick arbitrary colors. See each
  analysis skill's visualization technique guide for the how-to.
- **Raw data is immutable.** Anything under `data/raw/` is never edited, recoded,
  or subset in place — cleaning reads raw and writes `data/processed/`. Acquisition
  (the `data-acquisition` skill) lands raw data with a `PROVENANCE.md` (source DOI,
  version, retrieval date, per-file checksums); keep that record intact. Never
  commit restricted microdata or large binaries to git — add them to `.gitignore`
  and keep only the provenance tracked.

## Literature + Zotero

- OpenAlex for discovery, Crossref for authoritative DOI metadata (see the
  `lit-search` skill's `api/` references). Don't fabricate a DOI or a field
  neither source returned — leave it blank.
- Zotero writes go through `lit-search/scripts/zotero_db.py`, which edits the
  local `zotero.sqlite` directly. **Adding items requires Zotero to be closed.**
  Reading (dedup, listing collections) is safe anytime. The script always backs
  up the database before writing — do not disable that (`--no-backup`) unless the
  user explicitly insists.

## Model use

- Default model is a cheap tier (`deepseek/deepseek-v4-flash-0731`). If a task
  needs careful multi-step reasoning (involved econometrics, debugging a broken
  analysis), suggest the user switch to the stronger model
  (`deepseek/deepseek-v4-pro`) with `/model` rather than pushing the cheap one
  past its limits.

## General

- The researcher is the domain expert. Surface choices and trade-offs; don't
  quietly decide screening/inclusion or specification questions for them.
