# Reproducibility & Handoff Audit

**Every stage must end reproducible-ready.** Treat each phase (cleaning, descriptives, main findings, robustness, output) as something you are handing to another person — a coauthor, a replicator, a reviewer, or the next phase agent — who has *only* your inputs and your do-file, not your memory of what you typed. Before you close a phase, run a **handoff audit**: confirm that someone starting from your inputs could reproduce your outputs exactly. At the very end, run a **final reproducibility check** that rebuilds everything from raw data in a clean session.

This is a gate, not a suggestion. Do not mark a phase done until its handoff audit passes.

## Why per-stage, not just at the end

If every stage is independently reproducible, a break is local and cheap to fix. If reproducibility is only checked at the end, a single undocumented manual step buried in cleaning can invalidate everything downstream and be nearly impossible to find. Auditing at each handoff keeps the failure surface small.

---

## The per-stage handoff audit (definition of done)

At the end of **each** phase, verify all of the following. Every "no" must be fixed or explicitly documented before proceeding.

**1. Runs top-to-bottom, unattended.**
- The stage's do-file runs clean from a fresh Stata session (`do code/NN_stage.do`) — no manual edits, no command-window-only steps, no "run this line first."
```stata
* A stage do-file should start self-sufficient:
clear all
set more off
set seed 12345                         // any randomness is seeded
capture log close
log using "logs/NN_stage.log", replace text
use "data/clean/prev_stage.dta", clear
```

**2. Inputs and outputs are explicit and canonical.**
- Reads only from declared inputs (raw or a prior stage's saved `.dta`), writes only to canonical paths from `project.yaml` (`data/clean/`, `output/tables/`, `output/figures/`).
- No absolute/personal paths (`/Users/you/...`); anchor with a `global root` or project-relative paths set once in the master do-file.
- Output filenames are stable and descriptive (no `final2`, `_v3`, `temp`).

**3. Sample and row counts are logged.**
- Report N at entry and exit, and log every observation-dropping step so the sample is auditable.
```stata
count
local nin = r(N)
drop if missing(outcome)
count
display "rows in: `nin'  rows out: " r(N)  "  dropped: " `nin' - r(N)
```

**4. No hidden state.**
- No dependence on data already in memory from another do-file, on `cd` quirks, or on settings toggled interactively. Each stage stands alone given its inputs (`clear all` at the top).

**5. Decisions are documented where they happen.**
- Every non-obvious choice (a filter threshold, a recode, a winsorization cutoff, dropping a unit) has a one-line comment saying *why*, next to the code.

**6. Environment is capturable.**
- `version` is stated so syntax is pinned to a Stata version. User-written commands (`reghdfe`, `estout`, etc.) are noted so they can be installed (see below).

**7. Committed.**
- The stage's do-file, log, and outputs are committed to git with a clear message (`stata-analyst: Phase N complete`) before the next phase modifies anything. Git history is the version trail — no `-v2` copies.

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

**1. Clean-room master run.** From a fresh session, run the master do-file that calls every stage in order and regenerates *every* table and figure from raw data:
```stata
* code/00_master.do
clear all
version 18
global root "`c(pwd)'"          // or set explicitly; no personal paths
do "$root/code/01_clean.do"
do "$root/code/02_descriptives.do"
do "$root/code/03_analysis.do"
do "$root/code/04_robustness.do"
do "$root/code/05_output.do"
```
```bash
# Ideally in a fresh working copy
stata -b do code/00_master.do
```
Every output must regenerate with no manual intervention and no errors (check the log for `r(...)` error codes).

**2. Reconcile outputs.** Confirm the regenerated tables/figures match what's in the paper. Row counts, key coefficients, and the estimation `e(N)` should be identical run-to-run (`set seed` makes any randomness reproducible).

**3. Capture the environment.**
```stata
* Record versions and required user-written commands for the replication package
about
creturn list     // c(stata_version), c(born_date), etc.
* Pin user-written packages in the master do-file, e.g.:
* ssc install reghdfe   (version noted); which reghdfe
```
Note every `ssc install` / `net install` dependency and its version in the README.

**4. Assemble the replication package.** Confirm a stranger could reproduce the results:
- `README.md`: what to run, in what order, expected outputs, required user-written commands + versions, data access/restrictions.
- `code/` with numbered do-files + `00_master.do`.
- `data/`: raw (or instructions to obtain it) and the do-file that builds `clean/`.
- `output/`: tables and figures, plus the master log.
- Every number in the paper traces to a do-file that produces it.

### Final reproducibility block for the memo

```markdown
## Final Reproducibility Check
- **Clean-room master run**: [passed / errors fixed]
- **Outputs reconcile with paper**: [all tables/figures regenerate identically]
- **Environment captured**: [Stata version + user-written commands/versions listed]
- **Replication package complete**: [README, code, data instructions, outputs, log]
- **Remaining caveats**: [restricted data / manual steps that could not be automated, with rationale]
```

---

## Red flags that fail a handoff audit

- A result that cannot be reproduced by re-running the do-file (points to hidden interactive state).
- Randomness without `set seed` → numbers change run-to-run.
- An output file with no do-file that produces it (where did it come from?).
- Absolute/personal paths, or reading from a location outside the project.
- The estimation `e(N)` differs from what the cleaning stage says it should be.
- A `-v2`/`-final` file instead of a git commit.
- "I just fixed that by hand in the data editor" — any manual data edit not encoded in a do-file.
