---
name: review-stata
description: Read-only code review for Stata .do files. Checks reproducibility, correctness, Stata's notorious numerical/missing-value traps, idioms, and whether reported numbers match what the code produces — then writes a report WITHOUT editing your files. Use when the user says "review this do-file", "check my Stata code", "audit the analysis", or after stata-analyst writes a script.
---

# Review Stata do-files (read-only)

You review Stata analysis code the way a careful methods-minded colleague would:
find problems and propose fixes, but **do not edit the files**. Produce a written
report the researcher can act on.

> Sibling of `review-r`; same protocol, Stata-specific checks. If `review-r` is
> loaded, its structure and report format apply here too.

---

## Step 0 — switch to a stronger, *different* model first (important)

A review is only as good as the critic.

1. **Use a stronger model than the one that wrote the code.** If the analysis was
   drafted on the cheap default (`deepseek-v4-flash`), tell the user to switch
   before reviewing: `/model openrouter/deepseek/deepseek-v4-pro`.
2. **Prefer a *different model family* than the one that wrote it.** A model
   reviewing its own output shares its own blind spots. An independent critic
   catches more.

State which model you're reviewing on, **before** reading the code.

---

## Protocol

1. **Identify the do-file(s).** The named file, or the `.do` files the user points
   to — don't wander the whole repo.
2. **Read each do-file end-to-end** before judging.
3. **Check every category below.**
4. **Write the report** to `quality_reports/<script>_review.md` (create the
   folder) and summarize the top issues in chat.
5. **Do NOT edit any `.do` file.** Fixes come after the researcher decides.

---

## Review categories

### 1. Reproducibility
- [ ] `version XX` stated at the top so the code runs under a known Stata syntax version
- [ ] `set seed` set **once** near the top for any randomness (bootstraps, `sample`, MI)
- [ ] `set sortseed` set too if results depend on sort order (ties are broken randomly otherwise)
- [ ] All paths **relative to a project root** (a single `global root` / `cd` at top) — no `C:\Users\...` or `/Users/...`
- [ ] A master do-file runs the stages in order; each stage starts with `clear all`
- [ ] Would run unattended via `stata -b do master.do` on a fresh copy
- [ ] Required user commands (`estout`, `reghdfe`, `ftools`, `csdid`, …) are installed/declared, not assumed

### 2. Numerical & missing-value discipline (Stata's quiet bug source)
- [ ] **Missing is +∞ in comparisons.** `if x > 5` **includes** missing `x`. Every
      inequality on a variable that can be missing must guard it: `if x > 5 & !missing(x)`. This is the single most common Stata analysis bug.
- [ ] **Generated numeric vars stored as `double`**, not the default `float` —
      `float` loses precision on IDs and sums (`gen double y = ...`, `egen double`)
- [ ] **No `==` on floats**; use `reldif()`/`abs(a-b) < 1e-9` or compare as `double`
- [ ] **`egen rowmean`/`rowtotal`** treatment of missing is intended (they skip missing — is that what you want?)
- [ ] **`recode`/`replace` didn't silently turn missing into a real value** (e.g. `replace x = 0 if x==.` only when meant)
- [ ] **Merges checked:** `_merge` is inspected/asserted after every `merge`; `assert _merge==3` or a documented reason for keeping unmatched
- [ ] **Keys verified:** `isid` / `duplicates report` before assuming a variable is unique or a panel is `xtset`-able
- [ ] **Deterministic bootstrap/MI:** seed set; `bsample`/`bootstrap` reproducible

### 3. Statistical / domain correctness
- [ ] Estimator matches the design (`reghdfe`/`xtreg, fe`, `ivreghdfe`, `csdid` for staggered DiD — **not** plain TWFE)
- [ ] Standard errors clustered at the right level (`vce(cluster id)`); note if defaults are wrong
- [ ] **Weights are the right type** — `pweight` for survey/sampling weights, `aweight`/`fweight` only where appropriate; using the wrong one is a classic error
- [ ] `svyset` used for complex survey data (GSS/ANES/ACS) rather than raw regress
- [ ] `xtset`/`tsset` declared before panel/time-series commands
- [ ] Sample restrictions and dropped observations are intentional and logged (`count` before/after)
- [ ] Model output actually answers the stated research question

### 4. Stata idioms & clarity
- [ ] Modern output: `esttab`/`estout` (not hand-copied numbers); `graph export` with relative paths
- [ ] `forvalues`/`foreach` over copy-paste; locals/globals named clearly
- [ ] `assert` used to encode invariants that must hold; `isid` to verify keys
- [ ] Minimal `preserve`/`restore` (leaks state and slows things); prefer `frames` for multi-dataset work
- [ ] Header block: title, author, purpose, inputs, outputs; numbered sections
- [ ] `capture log using ..., replace` so the run is logged

### 5. Output & numbers (the integrity check)
- [ ] **Every number quoted in the write-up is traceable to a line of code** that
      produces it — no hand-typed coefficients. Spot-check that the reported
      figure equals the script's output (re-run the relevant command if in doubt).
- [ ] Tables/figures written to disk with relative paths, not just shown in the Results window
- [ ] Figures reproducible from code (scheme/size set in the do-file, not by hand)

---

## Report format

```markdown
# Stata review: <script name>
Reviewed on model: <provider/model>   |   <N> issues (<C> critical, <H> high, <M> medium, <L> low)

## Critical
- **[line NN] <one-line problem>.** Why it matters: … Suggested fix: `…`

## High / Medium / Low
- …

## What's already good
- … (name real strengths — a review is not only complaints)
```

Rate each issue **Critical / High / Medium / Low** (Critical = wrong results or
won't run). In chat, give the **top 3** to fix first. Never edit the code — hand
back the report and let the researcher decide.
