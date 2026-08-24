# Phase 2 — Verify & hand off

Confirm the download is intact and complete, do a read-only sanity pass, protect
restricted/large files from git, and tell the downstream skill exactly what it's
inheriting.

## Tasks

### 1. Verify integrity
- Confirm every expected file arrived and every checksum in `MANIFEST.json`
  matches the downloaded bytes. The bundled `dataverse_get.py` verifies md5 on
  download; for other sources, compute and record checksums now.
- If a checksum can't be verified (e.g. a source that reingested a tabular file),
  say so explicitly in `PROVENANCE.md` rather than implying verification happened.

### 2. Read-only sanity pass
Open the data **only to inspect**, not to change it. Confirm the shape is what the
source advertised — this catches truncated downloads and wrong-file mistakes
before they poison the analysis.
- Row and column counts. Does N match the dataset's documented N? If the source
  says ~72,000 GSS respondents and you have 400, the download is partial.
- Are variable and value labels present (for .dta/.sav originals)?
- Spot-check a few known quantities against the codebook (a year range, a category).
- Note anything off in `PROVENANCE.md` under a `## Sanity check` heading. Do not
  fix it here — flag it for the cleaning phase.

### 3. Protect restricted / large files from git
- Add restricted microdata and large binaries to `.gitignore` (e.g.
  `data/raw/<dataset>/`), keeping `PROVENANCE.md` and `MANIFEST.json` tracked so
  the provenance is in the repo even when the bytes aren't.
- For restricted data, double-check nothing sensitive is already staged before any
  commit. State plainly to the user that the raw data is gitignored and why.

### 4. Update project state
```yaml
# progress.yaml
status:
  data_acquisition: done
artifacts:
  raw_data: data/raw/<dataset>/
  acquisition_script: scripts/cleaning/00_acquire.(sh|R|py)
  provenance: data/raw/<dataset>/PROVENANCE.md
  codebook: data/codebooks/<dataset>/
```

### 5. Handoff note
Return to the user / orchestrator:
1. What landed, where, and at which version (with DOI).
2. Integrity result (checksums verified? any file that couldn't be verified).
3. Sanity-pass result — shape matches source, or the discrepancy to resolve.
4. Restriction/git status (what's gitignored and why).
5. **What cleaning still has to happen** — this is the explicit handoff to
   `r-analyst` / `stata-analyst` phase 1: raw is immutable; recoding, missing-data
   handling, sample restriction, and survey-weight setup all belong there. For
   survey data, point them at the survey-weighting technique in the analysis skill
   (`techniques/02_survey_resampling.md`) — using GSS/ANES/ACS without the correct
   weights and design is a common desk-reject error.

> The next skill reads `data/raw/…` and does the cleaning you deliberately left
> undone. Do not pre-clean to "help" it.
