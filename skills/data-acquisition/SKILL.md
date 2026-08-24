---
name: data-acquisition
description: Acquire the data a quantitative sociology analysis starts from — Dataverse replication packages, IPUMS/Census (ACS), GSS, ANES, ICPSR, OSF, and generic archives — and land it as immutable, provenanced raw data with a codebook and a re-runnable fetch script. Use at the very start of a quantitative project, before r-analyst / stata-analyst. Triggers on "get the replication data for this paper", "download this Dataverse dataset", "pull ACS / GSS / IPUMS", "grab the data from this DOI/OSF link".
---

# Data Acquisition

You get the data into the project **reproducibly, with provenance, and without
touching it after it lands**. Journal-level analysis fails at the front end more
often than at the model: wrong dataset version, wrong universe, a silently
re-encoded file, restricted data pushed to a public repo, or a number nobody can
trace back to a source. Your job is to make the first mile boring and auditable.

You do **not** clean, recode, or subset here. That is `r-analyst` /
`stata-analyst` phase 1. You deliver raw data plus enough provenance that the
next skill — and a replication reviewer — can trust where it came from.

## Project Integration

Reads `project.yaml` when present and uses its canonical paths:

```yaml
type: quantitative        # or mixed
paths:
  raw_data: data/raw/       # <- immutable landing zone (you write here)
  codebooks: data/codebooks/
  scripts_cleaning: scripts/cleaning/   # <- the re-runnable fetch script lives here
```

If there is no `project.yaml`, offer to run `project-scaffold` first, or fall
back to `data/raw/`, `data/codebooks/`, `scripts/`.

Updates `progress.yaml` when complete:

```yaml
status:
  data_acquisition: done
artifacts:
  raw_data: data/raw/<dataset>/
  acquisition_script: scripts/cleaning/00_acquire.(sh|R|py)
  provenance: data/raw/<dataset>/PROVENANCE.md
  codebook: data/codebooks/<dataset>/
```

## Connection to Other Skills

| Skill | Relationship | Handoff |
|-------|--------------|---------|
| `project-scaffold` | Upstream | Creates the canonical paths you write into |
| `r-analyst` phase 1 | **Downstream** | Reads `data/raw/…` you produced; does the cleaning you deliberately did *not* do |
| `stata-analyst` phase 1 | **Downstream** | Same handoff for Stata projects |
| `text-analyst` phase 0 | Downstream | For corpora acquired as raw text |

## Core Principles

1. **Raw is immutable.** Everything you download goes to `data/raw/` and is
   never edited, recoded, or filtered in place. Fixes happen later, in a
   cleaning script that reads raw and writes `data/processed/`. If you must
   change a byte, you are in the wrong skill.
2. **Provenance is mandatory.** Every acquisition records: source + persistent
   identifier (DOI/handle), **exact version**, retrieval date, the URL or API
   call used, and a checksum per file. "The GSS" is not provenance; "GSS 1972–2022
   Cross-Sectional Cumulative, release 2023-11, from gss.norc.org, md5 …" is.
3. **Prefer a script over a click.** If the source has an API (Dataverse, IPUMS,
   Census, OSF), fetch through it so re-acquisition is one command. When a source
   *requires* a manual login/DUA step (ICPSR restricted, ANES login), script
   everything you can and document the manual step precisely — including the
   exact path the file must land at.
4. **Respect access terms — surface, don't bypass.** Restricted files, Data Use
   Agreements, and login walls are the user's decision and legal responsibility.
   Tell them what's restricted; never attempt to circumvent authentication.
5. **Restricted / large data never goes to git.** Before finishing, ensure
   microdata under a DUA and large binaries are in `.gitignore`. A grad student
   accidentally pushing restricted respondent data to a public GitHub is a real
   harm; you are the backstop.
6. **Never fabricate.** If a codebook, variable, DOI, version, or checksum wasn't
   provided by the source, leave it blank and say so. Do not infer an N or a
   variable label the source didn't return.

## Source Router

Pick the guide that matches what the user has. When in doubt, ask for the DOI or
URL and read it.

| The user has… | Source | Guide |
|---------------|--------|-------|
| A DOI or Dataverse URL (`doi:10.7910/DVN/…`, `dataverse.harvard.edu/…`) — **the common case for replication packages** | Dataverse (any installation) | `sources/dataverse.md` |
| Census microdata / harmonized samples (CPS, ACS PUMS, decennial, NHGIS, international) | IPUMS | `sources/ipums.md` |
| Census/ACS *estimates* by geography (tables, not microdata) | Census API / ACS | `sources/census_acs.md` |
| GSS, ANES, or an ICPSR study number | Survey archives | `sources/survey_archives.md` |
| An OSF link, a journal "supplementary/replication" zip, or a bare file URL | Generic archives | `sources/replication_package.md` |

Many replication packages live **on** Dataverse even when a paper links to a
journal page — resolve the DOI first; it usually points to Dataverse.

## Workflow

Three short phases. Pause for the user between plan and acquire.

### Phase 0 — Plan the acquisition
See `phases/phase0-plan.md`. Identify the source and persistent ID, the exact
version to pin, the license/restriction status, and *what* to fetch (whole
dataset vs. specific files). Confirm with the user before downloading anything
large or restricted.

### Phase 1 — Acquire
See `phases/phase1-acquire.md`. Fetch through the source's API/script into
`data/raw/<dataset>/`, capturing a `PROVENANCE.md`, a per-file `MANIFEST.json`
with checksums, and the codebook. Save the exact command as a re-runnable
`00_acquire` script. Do not open the data to "tidy" it.

### Phase 2 — Verify & hand off
See `phases/phase2-verify-handoff.md`. Verify checksums, do a **read-only** sanity
pass (row/column counts, does N match the source's advertised N, are labels
present), update `.gitignore` for restricted/large files, update `progress.yaml`,
and write the handoff note telling `r-analyst`/`stata-analyst` where raw lives and
what cleaning still has to happen.

## Bundled helper

`scripts/dataverse_get.py` — a `uv` PEP-723 script (run with `uv run`) that lists
and downloads Dataverse datasets by DOI/URL, pins a version, fetches **original**
(un-reingested) tabular files, verifies checksums, and writes the provenance
manifest. See `sources/dataverse.md` for usage.
