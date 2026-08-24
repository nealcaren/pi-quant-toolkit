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
