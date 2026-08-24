# Census / ACS estimates

Use this when the user wants **published estimates** by geography (population,
income, education by tract/county/state) — tables, not microdata. For Census
*microdata* (PUMS, individual records), use `sources/ipums.md` instead.

## Prerequisite: a free Census API key

- Request one at <https://api.census.gov/data/key_signup.html> (instant, free).
- Store it as an env var, not in the script:
  - **macOS/Linux:** `export CENSUS_API_KEY="..."` (add to `~/.zshrc`/`~/.bashrc`)
  - **Windows (PowerShell):** `setx CENSUS_API_KEY "..."` then reopen the terminal
- In R, `tidycensus::census_api_key("...", install = TRUE)` saves it to `.Renviron`.

## R (recommended): tidycensus

```r
# scripts/cleaning/00_acquire.R
library(tidycensus)

acs <- get_acs(
  geography = "county",
  variables = c(median_income = "B19013_001",
                bachelors      = "B15003_022"),
  state     = "NC",
  year      = 2022,
  survey    = "acs5"          # 5-year; use "acs1" for large-area annual
)

# ACS estimates come WITH a margin of error (moe). Keep it — do not drop it.
saveRDS(acs, "data/raw/acs-nc-2022/acs_county.rds")
```

Pin `year` and `survey`. Note the vintage — ACS 5-year 2018–2022 is a different
universe than 2017–2021. Record which in `PROVENANCE.md`.

## Python alternative: uv + census/requests

If the user prefers Python (and has `uv` — see `sources/dataverse.md` for install),
a PEP-723 script hitting `https://api.census.gov/data/{year}/acs/acs5` works the
same. Use it only if they're already in a Python pipeline; `tidycensus` is less
error-prone for geography handling.

## Provenance notes specific to ACS

- Estimates are **survey estimates with sampling error** — the `moe` column is
  part of the data, not optional decoration.
- Record: dataset (ACS5/ACS1), vintage year, geography, variable IDs (the raw
  `B19013_001` codes, not just your friendly names), state/county filters.
- Geographies change over time (new counties, tract boundaries). If comparing
  across years, flag it for the cleaning phase — don't silently join.
