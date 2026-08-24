# GSS, ANES, and ICPSR

The three survey sources sociology students reach for most. GSS and ANES have
clean public downloads (and R packages); ICPSR is a login-gated archive where
some studies are restricted.

---

## GSS (General Social Survey)

The cumulative cross-sectional file (1972–present) is the usual target.

**Easiest — the `gssr` R package** (bundles the cumulative data + panels):
```r
# install.packages("gssr", repos = c("https://kjhealy.r-universe.dev"))
library(gssr)
data(gss_all)                       # cumulative cross-section
saveRDS(gss_all, "data/raw/gss-cumulative/gss_all.rds")
data(gss_doc)                       # variable documentation -> data/codebooks/
```

**Or direct download** from <https://gss.norc.org> (the Stata `.dta` or SPSS
`.sav` of the cumulative file). Land the file in `data/raw/gss-cumulative/` and
save the accompanying codebook.

Provenance: record the **release** (e.g. "1972–2022 release 2, dated 2023-11"),
not just "the GSS."

Handoff note: GSS **requires weights** (`wtssps`/`wtssall`) and design variables
(`vpsu`, `vstrat`) for correct point estimates and SEs. Set those up in the
analysis skill, not here.

---

## ANES (American National Election Studies)

Requires a **free account/login** at <https://electionstudies.org>; there is no
open download API. The Time Series Cumulative file is the common target.

Scripted step isn't possible through the login wall, so:
1. Direct the user to log in and download the cumulative (or a specific year)
   file (Stata/SPSS/CSV) plus its codebook.
2. Tell them the exact path to drop it: `data/raw/anes-cumulative/`.
3. Your `scripts/cleaning/00_acquire` script documents the manual step and then
   **verifies the file exists** at that path and records its checksum — so the
   provenance is complete even though the fetch was manual.

Handoff note: ANES also needs its weights and, for the cumulative file, careful
year/sample handling. Flag for the analysis skill.

---

## ICPSR

ICPSR (<https://www.icpsr.umich.edu>) hosts thousands of studies by **study
number**. Access ranges from open (with a free login) to **restricted** (DUA,
IRB, sometimes a secure enclave).

- **Open studies:** the user logs in and downloads the study bundle (data +
  codebook, usually Stata/SPSS/SAS/DDI). Land it in `data/raw/icpsr-<studynum>/`.
  The `icpsrdata` R package can automate the download for open studies using
  stored credentials — offer it if the user wants a scripted path.
- **Restricted studies:** do **not** attempt to access these programmatically or
  bypass the DUA. Surface exactly what's required (application, IRB approval,
  possibly a virtual data enclave) and let the user decide. If restricted data
  does land locally, it is **gitignored** in Phase 2, always.

Provenance: record the **study number and version/DOI** ICPSR assigns and the
access tier (open vs. restricted).

---

## Common handoff

All three are complex survey samples. Acquisition ends with raw data + codebook +
provenance; **weighting, design, missing-data, and recoding all belong to
`r-analyst`/`stata-analyst` phase 1.** Using any of these without the correct
weights and design is a frequent, avoidable desk-reject — say so in the handoff
note and point to `techniques/02_survey_resampling.md`.
