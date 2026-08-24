---
name: repro-package
description: Turn a finished analysis into a submission-ready replication archive — prove it rebuilds from raw in a clean session, then assemble the master runner, README, codebook, environment snapshot, data-access statement, and an output→exhibit map that journals now require. Works for R, Stata, or Python projects. Use when the analysis is done and the user is preparing to submit, deposit replication files, or says "make a replication package", "build the reproducibility archive", "get this ready for submission".
---

# Reproducibility packaging

You take a completed analysis and produce the artifact a journal, a data
repository, and a skeptical replicator all need: a self-contained archive that
regenerates every table and figure **from raw data, in one command, on a clean
machine** — plus the documentation that makes it usable.

This is the *final* packaging step. The per-stage handoff audits inside
`r-analyst` / `stata-analyst` / `text-analyst` (their `handoff_audit` technique)
are what make this step cheap: if each stage was already reproducible, you're
assembling and verifying, not rescuing. Do not duplicate those audits here — build
on them.

## Project Integration

Reads `project.yaml` paths; writes the archive under a `replication/` (or
`submissions/`) directory. Updates `progress.yaml`:

```yaml
status:
  replication_check: done
checks:
  results_reproducible: true
artifacts:
  replication_archive: replication/
```

## Core Principles

1. **From raw, not from clean.** The archive must rebuild starting from the raw
   inputs (or a documented data-access step), not from a mid-pipeline `.rds`/`.dta`
   you happen to have. If a step can't run from raw, it isn't reproducible yet.
2. **One command.** A single master script runs every stage in order. If a human
   has to "also run this by hand," document it or script it — don't leave it implicit.
3. **Respect data licenses.** Never bundle restricted microdata (GSS/ANES weights
   aside, ICPSR-restricted, DUA data) into a shareable archive. Ship a **data-access
   statement** instead — the DOI/version and how to obtain it — drawn from the
   `PROVENANCE.md` the `data-acquisition` skill wrote. This is both a legal and an
   ethical line.
4. **Every exhibit is traceable.** Each table and figure in the paper maps to the
   script (and ideally line) that produces it. A reviewer should never wonder where
   Table 3 came from. Every *number* in the report must likewise trace to the
   results ledger — run the `stat-check` reconciliation and confirm it's clean (no
   orphans) before archiving the write-up.
5. **Capture the environment.** Record software versions and packages so the code
   still runs in two years. Reproducibility that depends on "whatever was installed
   that day" isn't reproducibility.

## Workflow

### Phase 1 — Clean-room rebuild (prove it works)

Run the whole pipeline from raw in a fresh session and confirm every output
regenerates. Use the analysis skill's final reproducibility check as the engine.

- **R:** `Rscript replication/code/00_run_all.R` from a clean session; ideally under
  `renv::restore()` so package versions are locked.
- **Stata:** `stata -b do replication/code/00_run_all.do` (Mac/Linux) or
  `StataMP-64.exe /e do ...` (Windows), starting each stage with `clear all`.
- **Python:** `uv run replication/code/00_run_all.py` (uv resolves the pinned deps).

Then confirm the regenerated tables/figures match the ones in the paper. Compare
**values**, not bytes (PDF/PNG timestamps differ) — check the numbers and the
figure content. Any mismatch is a blocker: fix it (or the paper) before packaging.
If a stage is slow (bootstraps, big text models), note expected runtime; don't
silently skip it.

> If this fails, stop and route back to the analysis skill's handoff audit — the
> package can't be built on an analysis that doesn't reproduce.

### Phase 2 — Assemble the archive

Lay out a clean, self-contained tree (see `templates/README_archive.md` for the
README to drop in):

```
replication/
  README.md              # how to run, expected runtime, software versions, exhibit map
  data/
    raw/                 # raw data IF licensing permits; else a DATA_ACCESS.md
    DATA_ACCESS.md       # DOI/version + how to obtain any data not bundled
  code/
    00_run_all.(R|do|py) # master: runs every stage from raw, in order
    01_...               # stages
  output/
    tables/  figures/    # regenerated exhibits
  codebook/              # variable definitions (from the source + any constructed vars)
  environment/           # version + package snapshot (see below)
```

Assemble each piece:

- **Master runner** (`00_run_all.*`) that sources/does/imports every stage in order
  from raw to final output. No manual steps between stages.
- **README** from the template: one-command run instructions, per-stage description,
  **expected total runtime**, software + version, and the **output→exhibit map**.
- **Codebook** for both source variables and every constructed variable (the recodes
  live in the cleaning scripts — summarize them here).
- **DATA_ACCESS.md** for anything not bundled: pull the source, DOI, version, and
  retrieval instructions straight from `data/raw/<dataset>/PROVENANCE.md`. State
  clearly which files a replicator must obtain themselves and where they go.
- **Environment snapshot:**
  - **R:** `renv::snapshot()` (commit `renv.lock`), or at minimum save
    `sessionInfo()` / `sessioninfo::session_info()` to `environment/R_session.txt`.
  - **Stata:** record the Stata version (`about`) and installed user commands with
    their versions (`which reghdfe`, `which esttab`, …) to `environment/stata_env.txt`;
    note the `version XX` line each do-file uses.
  - **Python:** ship the `uv` PEP-723 headers / lockfile; also write `uv pip freeze`
    (or `pip freeze`) and `python --version` to `environment/py_env.txt`.

### Phase 3 — Verify the archive is self-contained

The archive must reproduce **on its own**, not because the rest of your project is
lying around.

- Copy `replication/` to a fresh location (outside the project) and run the master
  script there. It must find every input via relative paths and regenerate outputs.
- Grep the code for absolute paths (`/Users/`, `C:\\`, `~/`), leftover interactive
  state, and reads from files outside the archive — fix any hit.
- Confirm no restricted data slipped in (check against the licenses noted in
  `PROVENANCE.md`); confirm large/restricted files are excluded and documented in
  DATA_ACCESS.md instead.
- Build a `MANIFEST` with a checksum per file so the archive's integrity is verifiable.

## Output — handoff note

Report to the user:
1. Reproduced from raw in a clean session: yes / the blocker.
2. Every paper exhibit maps to a script (list any that don't).
3. What's bundled vs. what a replicator must obtain (the data-access story).
4. Environment captured (which lockfile/version file).
5. Archive verified self-contained from a fresh location.
6. Where the archive is and what to deposit (Dataverse/OSF/journal system).

> Depositing on Dataverse? The archive you built here is exactly what goes up;
> cite the resulting DOI in the paper.
