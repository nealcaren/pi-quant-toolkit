# Replication package: <PAPER TITLE>

<Author(s)>. <Journal / working paper>, <year>.
Corresponding author: <name, email>.

## What this is

Code and (where licensing permits) data to reproduce every table and figure in
the paper from raw inputs.

## How to run

1. Install the software listed under **Software** below.
2. Obtain any data not bundled here — see **Data** and `data/DATA_ACCESS.md`.
3. From the top of this folder, run the master script:

   - **R:** `Rscript code/00_run_all.R`  (first: `renv::restore()` to install pinned packages)
   - **Stata:** `stata -b do code/00_run_all.do`  (Windows: `StataMP-64 /e do code/00_run_all.do`)
   - **Python:** `uv run code/00_run_all.py`

   All outputs are regenerated into `output/tables/` and `output/figures/`.

**Expected runtime:** <e.g. ~12 minutes on a 2023 laptop; the bootstrap in
`04_robustness` is ~8 of those>. <Note any GPU/large-memory needs.>

## Software

| Tool | Version | Notes |
|------|---------|-------|
| <R / Stata / Python> | <x.y.z> | see `environment/` for the full package snapshot |
| key packages | | `renv.lock` / `uv` lockfile / `which` output in `environment/` |

## Data

| Dataset | Source & DOI | Version | Bundled here? | If not, how to get it |
|---------|--------------|---------|---------------|-----------------------|
| <name> | <DOI / archive> | <version> | yes / no | see `data/DATA_ACCESS.md` |

Restricted data is **not** included; `data/DATA_ACCESS.md` explains how to obtain
it and where to place the files so the code finds them.

## Output → exhibit map

Every exhibit in the paper and the script that produces it:

| Exhibit | Produced by | Output file |
|---------|-------------|-------------|
| Table 1 (Descriptives) | `code/02_descriptives.*` | `output/tables/table1.tex` |
| Table 2 (Main results) | `code/03_analysis.*` | `output/tables/table2.tex` |
| Figure 1 | `code/03_analysis.*` | `output/figures/fig1.pdf` |
| Table 3 (Robustness) | `code/04_robustness.*` | `output/tables/table3.tex` |
| ... | ... | ... |

## Directory layout

```
README.md            this file
code/                master runner + numbered stage scripts
data/                raw data (if licensing permits) + DATA_ACCESS.md
output/tables/       regenerated tables
output/figures/      regenerated figures
codebook/            variable definitions (source + constructed)
environment/         software version + package snapshot
MANIFEST             checksums for every file in the archive
```

## Contact / license

<Data license and code license (e.g. code MIT, data per source terms).>
<Contact for questions about replication.>
