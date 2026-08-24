# Reproducibility & Handoff Audit

**Every stage must end reproducible-ready.** Treat each phase (cleaning, descriptives, main findings, robustness, output) as something you are handing to another person — a coauthor, a replicator, a reviewer, or the next phase agent — who has *only* your inputs and your script, not your memory of what you clicked. Before you close a phase, run a **handoff audit**: confirm that someone starting from your inputs could reproduce your outputs exactly. At the very end, run a **final reproducibility check** that rebuilds everything from raw data in a clean session.

This is a gate, not a suggestion. Do not mark a phase done until its handoff audit passes.

## Why per-stage, not just at the end

If every stage is independently reproducible, a break is local and cheap to fix. If reproducibility is only checked at the end, a single undocumented manual step buried in cleaning can invalidate everything downstream and be nearly impossible to find. Auditing at each handoff keeps the failure surface small.

---

## The per-stage handoff audit (definition of done)

At the end of **each** phase, verify all of the following. Every "no" must be fixed or explicitly documented before proceeding.

**1. Runs top-to-bottom, unattended.**
- The stage's script runs clean from a fresh R session with `Rscript code/NN_stage.R` — no manual edits, no console-only commands, no "run this line first."
```r
# A stage script should start self-sufficient:
set.seed(12345)                      # any randomness is seeded
library(here); library(tidyverse)    # explicit, loaded at top
input  <- readRDS(here("data/clean/prev_stage.rds"))
```

**2. Inputs and outputs are explicit and canonical.**
- Reads only from declared inputs (raw or a prior stage's saved output), writes only to the canonical paths from `project.yaml` (`data/clean/`, `output/tables/`, `output/figures/`).
- No absolute/personal paths (`/Users/you/...`); use `here()` or project-relative paths.
- Output filenames are stable and descriptive (no `final2`, `_v3`, `temp`).

**3. Sample and row counts are logged.**
- Print N at entry and exit, and log every row-dropping step so the sample is auditable. An unexplained change in N is a *tell* that something is wrong — reconcile it before proceeding (see the Tells section in `techniques/09_plausibility_checks.md`).
```r
cat("rows in:",  nrow(input), "\n")
clean <- input |> filter(!is.na(outcome))
cat("dropped missing outcome:", nrow(input) - nrow(clean), "\n")
cat("rows out:", nrow(clean), "\n")
```

**4. No hidden state.**
- No dependence on objects left in the environment from another script, on working-directory quirks, or on options set interactively. Each stage stands alone given its inputs.

**5. Decisions are documented where they happen.**
- Every non-obvious choice (a filter threshold, a recode, a winsorization cutoff, dropping a unit) has a one-line comment saying *why*, next to the code.

**6. Environment is capturable.**
- Package loads are explicit at the top. The final stage records versions (see below); ideally the project uses `renv` so versions are locked.

**7. Committed.**
- The stage's script and outputs are committed to git with a clear message (`r-analyst: Phase N complete`) before the next phase modifies anything. Git history is the version trail — no `-v2` copies.

### Handoff audit block for the memo

Append to `memos/analysis-memo.md` at each phase, right after the Plausibility Check:

```markdown
### Handoff Audit
- **Runs clean from fresh session**: [yes / fixed X]
- **Inputs → outputs**: [input files] → [output files], canonical paths only
- **Row-count reconciliation**: [N in → N out, drops logged]
- **Decisions documented**: [yes / list any still needing a rationale]
- **Committed**: [commit hash / message]
- **Ready for handoff**: [yes / blockers]
```

---

## The final reproducibility check (Phase 5)

Before declaring the analysis complete, prove the whole pipeline reproduces end-to-end.

**1. Clean-room master run.** From a fresh session, run the master script that sources every stage in order and regenerates *every* table and figure from raw data:
```r
# code/00_master.R
source(here::here("code/01_clean.R"))
source(here::here("code/02_descriptives.R"))
source(here::here("code/03_analysis.R"))
source(here::here("code/04_robustness.R"))
source(here::here("code/05_output.R"))
```
```bash
# Ideally in a fresh working copy / clean session
Rscript code/00_master.R
```
Every output must regenerate with no manual intervention and no errors.

**2. Reconcile outputs.** Confirm the regenerated tables/figures match what's in the paper. Row counts, key coefficients, and the analysis N should be identical run-to-run (seeds make any randomness reproducible).

**3. Capture the environment.**
```r
# Record exact versions for the replication package
writeLines(capture.output(sessionInfo()), "output/sessionInfo.txt")
# If using renv (recommended):
renv::snapshot()   # locks package versions in renv.lock
```

**4. Assemble the replication package.** Confirm a stranger could reproduce the results:
- `README.md`: what to run, in what order, expected outputs, data access/restrictions.
- `code/` with numbered scripts + `00_master.R`.
- `data/`: raw (or instructions to obtain it) and the code that builds `clean/`.
- `output/`: tables and figures, plus `sessionInfo.txt` / `renv.lock`.
- Every number in the paper traces to a script that produces it.

### Final reproducibility block for the memo

```markdown
## Final Reproducibility Check
- **Clean-room master run**: [passed / errors fixed]
- **Outputs reconcile with paper**: [all tables/figures regenerate identically]
- **Environment captured**: [sessionInfo.txt + renv.lock]
- **Replication package complete**: [README, code, data instructions, outputs]
- **Remaining caveats**: [restricted data / manual steps that could not be automated, with rationale]
```

---

## Red flags that fail a handoff audit

- A result that cannot be reproduced by re-running the script (points to hidden interactive state).
- Randomness without a seed → numbers change run-to-run.
- An output file with no script that produces it (where did it come from?).
- Absolute/personal paths, or reading from a location outside the project.
- The analysis N differs from what the cleaning stage says it should be.
- A `-v2`/`-final` file instead of a git commit.
- "I just fixed that by hand in the CSV" — any manual data edit not encoded in a script.
