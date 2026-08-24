# IPUMS

IPUMS delivers harmonized microdata: **IPUMS USA** (decennial + ACS PUMS),
**IPUMS CPS**, **IPUMS International**, **NHGIS** (aggregate + GIS), and more. You
define an *extract* (samples + variables), IPUMS builds it server-side, and you
download it with a DDI codebook. There is a real API, so this is scriptable.

## Prerequisites

1. A free IPUMS account at <https://www.ipums.org> (per-collection registration).
2. An **API key**: account → *API keys* → create. Store as an env var:
   - **macOS/Linux:** `export IPUMS_API_KEY="..."`
   - **Windows (PowerShell):** `setx IPUMS_API_KEY "..."` (reopen terminal)
3. R users: the `ipumsr` package. Python users: `ipumspy` (via `uv` — see
   `sources/dataverse.md` for installing `uv`).

## R: ipumsr (recommended)

```r
# scripts/cleaning/00_acquire.R
library(ipumsr)
set_ipums_api_key(Sys.getenv("IPUMS_API_KEY"))

ext <- define_extract_micro(
  collection  = "usa",
  description = "ACS 2019-2022 age, sex, income",
  samples     = c("us2019a", "us2020a", "us2021a", "us2022a"),
  variables   = c("AGE", "SEX", "INCTOT", "EDUC")
)

submitted <- submit_extract(ext)
wait_for_extract(submitted)                    # IPUMS builds it server-side
download_extract(submitted, download_dir = "data/raw/ipums-usa-acs/")
# Produces a .dat.gz (or .csv) PLUS a .xml DDI codebook — keep BOTH.
```

## Python: ipumspy

```bash
uv run --with ipumspy scripts/cleaning/00_acquire.py   # equivalent flow via the API
```

## What lands, and provenance

- Keep the **DDI codebook** (`.xml`) alongside the data — it carries variable and
  value labels and is how the fixed-width/`.dat` file is parsed. Copy it into
  `data/codebooks/<dataset>/`.
- Record the **exact extract definition** in `PROVENANCE.md`: collection, sample
  IDs, variable list, and the extract number IPUMS assigns. That definition *is*
  the reproducibility contract — anyone can rebuild the identical extract from it.
- IPUMS extracts can be large. Plan `.gitignore` from the start (Phase 2).

## Handoff note

IPUMS microdata needs the right **weights** (e.g. `PERWT`/`HHWT`, or replicate
weights for correct SEs) and, for pooled ACS, careful treatment of the multi-year
design. Do not set those up here — flag them for `r-analyst`/`stata-analyst`
phase 1 and its survey-weighting technique.
