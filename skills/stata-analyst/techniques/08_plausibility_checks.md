# Plausibility Checks

**The user may not be an expert in the data or the code. Your job is to catch the number that is wrong, surprising, or impossible before it reaches a table.** At every stage, translate each result into a plain-language claim and ask: *would a domain expert believe this?* If not, stop and investigate before moving on.

This guide is stage-by-stage. Consult it in Phase 1 (descriptives), Phase 3 (main results), and Phase 4 (robustness). It also defines the **cross-specification consistency** language used to report whether a richer model (FE/DiD/IV) *confirms* or *overturns* a simpler one.

## The core habit

For every quantity you produce — a mean, a coefficient, a standard error, an R² — do three things:

1. **State it in words and units.** "The average respondent earns \$52,000." "A one-unit increase in X raises the probability of Y by 8 percentage points."
2. **Sanity-check it against what you already know.** Prior literature, the outcome's own scale, official statistics, common sense.
3. **Flag, don't bury.** If a number is implausible, surprising, or contradicts an earlier stage, say so explicitly in the memo and to the user. A surprising-but-real finding is the whole point of research; a surprising-but-wrong number is a bug. You cannot tell which without checking.

Never present a result you have not personally reality-checked.

---

## Tells: reconcile expected vs. actual

A **tell** is a gap between what you expected and what you got. After *every* transformation that could change the data — a filter, a merge, a recode, a `destring` — reconcile four things: **observation count, key uniqueness, distributions, and missingness.** If any moved and you cannot say why, stop: an unexplained change is a symptom, not a nuisance. Losing cases you did not mean to lose is often the first sign that something upstream is wrong.

```stata
* Log N before/after each step. An unexplained change is a tell.
count
local n0 = r(N)
* ... transformation ...
count
display "rows: `n0' -> " r(N) " (" r(N)-`n0' ")"

* Key uniqueness — assert it where you assume it:
isid id                              // errors if id is not unique -> a tell
duplicates report id

* Merges: NEVER keep(3) blindly. Inspect _merge and decide with the user.
merge m:1 id using "using.dta"
tab _merge                           // 1=master-only  2=using-only  3=matched
* low share of _merge==3 (match rate) is a tell; resolve before dropping

* destring / type coercion can silently create missings:
destring strvar, gen(numvar) force
count if missing(numvar) & !missing(strvar)   // NEW missings = tell
```

**Common tells and what they usually mean:**

| Tell | Usual cause |
|---|---|
| N in ≠ N out after `drop`/`keep` (unexpected) | wrong variable name, unexpected coding, condition matched nothing/everything |
| Merge changes N unexpectedly | key mismatch (loss) or `m:m`/duplicate keys (fan-out) |
| Low `_merge==3` share | ID formatting mismatch; biases everything downstream |
| `e(N)` shrinks between models | listwise deletion on a control only some specs include — specs no longer on the same sample |
| A variable becomes constant | bad recode or wrong column pulled |
| Mean/SD shifts after a "harmless" step | the step wasn't harmless — find out why |
| New missings after a transformation | `destring force`, failed date parse, unmatched recode |
| An all-missing variable | wrong name, or a merge that never matched |
| Spikes at −99 / 999 / 0 | sentinel codes being treated as real values |
| Levels appear/vanish after `recode`/`encode` | dropped or mismapped category |

Wire this into the sample-construction log from Phase 1 so every dropped case is counted and attributable.

## Involve the user in consequential data decisions

You provide the counts and the options; the user makes the call. **Never silently decide** any of the following — surface the number affected and at least two options, and get a choice:

- **Which cases to drop** (and confirm unexpected drops are intended, not a bug).
- **How to handle missing data** (listwise, imputation, indicator).
- **What to do with unmatched merge records** (`_merge==1` master-only / `_merge==2` using-only).
- **Outliers** (keep, winsorize, trim) and the cutoff.
- **Sample restrictions** (time window, subpopulation) that change who the findings are about.

A dropped case is both a decision (a) the user should own and a diagnostic (b) — if the count is larger than expected, treat it as a tell before treating it as a choice.

---

## Phase 1: Descriptives plausibility

Before any modeling, confirm the data describes a world that could exist.

**Range and bounds:**
```stata
* Every variable should live inside its logically possible range.
summarize age share pct events income, detail

* Explicit impossible-value checks — one per variable with known bounds
count if age   < 0 | age   > 120        // ages
count if share < 0 | share > 1          // proportions in [0,1]
count if pct   < 0 | pct   > 100        // percentages in [0,100]
count if events < 0                     // counts non-negative
count if income < 0                     // dollars non-negative
```

**Ask, for each key variable:**
- Is the **mean** where you'd expect? (A mean income of \$52 vs \$52,000 vs \$52M tells you the units.)
- Is the **unit of measurement** what you assumed? (dollars vs thousands of dollars; rate per 100 vs per 100,000; monthly vs annual)
- Does the **SD** imply a sensible spread, or is it implausibly tight/wide?
- Do **categories** have the levels and shares you expect? (`tab x, missing` — any unexpected codes like -99, 999, blanks?)
- Is the **N** what you expected, and do subgroup **cell counts** support the planned design (e.g., enough treated pre/post units for DiD)?

**Benchmark against the outside world.** When a variable has a known population value, compare:
```stata
* e.g., does sample unemployment roughly match the official rate for these years?
summarize unemployed          // compare to BLS/Census/known figure
```
A sample that says 40% unemployment when the real figure is 5% signals a coding, weighting, or sampling problem — not a finding.

**Bivariate signs sanity check.** Before controls, do the raw relationships point the expected way?
```stata
correlate x outcome
* If theory says X and Y move together and the raw correlation is strongly negative,
* resolve that puzzle now — it will not go away when you add controls.
```

**Missingness plausibility.** Is the amount and pattern of missing data believable, and is it correlated with treatment/outcome in a way that threatens the design? (See Phase 4 for formal tests.)

---

## Phase 3: Results plausibility

Once you have coefficients, interrogate them before you believe them.

**1. Sign.** Does the coefficient's sign match theory *and* the Phase 1 bivariate relationship?
- Sign matches expectation → note it, move on.
- Sign flips from the raw correlation when you add controls → **investigate**. This can be legitimate (confounding, suppression, Simpson's paradox) or a bug (mis-coded variable, wrong reference category, collinearity). Do not report a flip you cannot explain.

**2. Magnitude.** Interpret the effect in real units and ask if it is believable.
```stata
* Translate to substantive scale: effect relative to the outcome's own SD
quietly summarize outcome
display "Effect in SD units = " _b[treatment]/r(sd)
* a treatment effect of 3+ SDs is almost always too big to be real
```
- Compare the effect to the outcome's plausible range, its mean, and its SD.
- Compare to published estimates for similar treatments. An effect an order of magnitude larger than the literature is a red flag, not a breakthrough.
- A coefficient larger than the outcome could ever plausibly move (e.g., "increases test scores by 400 points" on a 0–100 scale) means something is wrong — often a units/scaling error.

**3. Precision.** Is the standard error believable?
- Absurdly tiny SEs (everything at p < 0.001) often mean clustering was forgotten or the panel structure was ignored.
- Absurdly huge SEs often mean collinearity or too few effective clusters.
- Check that **N in the regression matches** the analysis sample you built in Phase 1 (`e(N)`). Silent listwise deletion can shrink the sample dramatically.

**4. Fit.** Is R² (or pseudo-R²) in a plausible range for this kind of data?
- **R² ≈ 1** in observational social data almost always means leakage — a "control" that is a near-proxy of the outcome, or the outcome accidentally on both sides.
- Perfect classification / perfect separation in a logit (`outcome != 0 predicts perfectly`) is the same warning.

**Units-and-belief statement (write this every time):**
> "Model X implies that [treatment] changes [outcome] by [magnitude in real units], which is [about Z% of the outcome mean / Z SDs]. This is [plausible because... / surprisingly large because... / implausible and needs checking because...]."

---

## Cross-specification consistency (the confirm-or-overturn question)

Whenever you estimate a sequence of models — naive OLS → +controls → +fixed effects → DiD/IV — **explicitly report what each step does to the estimate of interest.** This is one of the most informative things you can tell a reader, and it is easy to lose in a table of stars.

Build the comparison mechanically so the pattern is unmissable:
```stata
eststo clear
eststo ols:      regress  outcome treatment
eststo controls: regress  outcome treatment $controls
eststo twfe:     reghdfe  outcome treatment, absorb(unit year) vce(cluster unit)
eststo main:     reghdfe  outcome treatment $controls, absorb(unit year) vce(cluster unit)

* Show just the coefficient of interest across specs
esttab ols controls twfe main, keep(treatment) b(3) se(3) ///
    mtitles("OLS raw" "OLS+controls" "Unit+time FE" "DiD/IV") scalars(N)
```

Then classify the pattern and **state it in the memo**:

| Pattern | What it looks like | What to report |
|---|---|---|
| **Confirms** | Estimate stable in sign, magnitude, significance as you add rigor | "The FE/DiD estimate confirms the OLS association: 0.48 → 0.45, essentially unchanged. Confounding by fixed unit characteristics is not driving the result." Raises confidence. |
| **Attenuates but survives** | Shrinks toward zero but stays same sign and significant | "Adding unit and time FE attenuates the estimate from 0.50 to 0.30 (−40%) but it remains significant. Part of the raw association reflects fixed confounders; a robust effect remains." |
| **Overturns** | Sign flips, or effect vanishes, once you add rigor | **Flag prominently.** "The naive OLS association (0.50, p<.01) reverses to −0.05 (n.s.) under DiD. The cross-sectional relationship was confounded; the within-unit design finds no effect (or the opposite effect)." This is a substantive finding, not a footnote. |
| **Emerges** | Null in OLS, significant under the credible design | "No association in OLS; the IV/DiD estimate is 0.35 (p<.05). The naive estimate was masked by [downward bias / measurement error / confounding]." |

**Rules:**
- The **preferred specification is the one whose identification you defended in Phase 0**, *not* whichever gives the biggest or most significant estimate. Report the others as context for it.
- When the credible design **overturns** a simpler model, that comparison *is* the headline — it shows why the design matters. Do not let it read as a mere robustness row.
- When it **confirms**, say so plainly: convergence across methods with different assumptions is strong evidence.
- If estimates move around wildly with no interpretable pattern, treat that as instability to explain, not to average over.

---

## Phase 4: Robustness plausibility

Robustness checks are themselves plausibility checks — read them the same way.
- Each robustness column should be compared to Main using the confirm / attenuate / overturn language above.
- **Placebo tests must pass:** a pre-treatment or fake-timing "effect" that is large and significant means the design is picking up something other than the treatment. A placebo that "works" is a failure.
- **Sample size must stay stable** across robustness specs unless a restriction is the point; unexplained `e(N)` changes signal silent deletion.
- **Sensitivity to unobservables:** translate the robustness statistic into words — "a confounder 3× as strong as [strongest control] would be needed to overturn this; that is implausible here because..."

---

## Red-flag catalog (stop and investigate)

Any of these should halt the pipeline and be raised with the user, not silently reported:

- A coefficient **larger than the outcome could plausibly move**, or an effect many multiples of the literature.
- **R² ≈ 1** or perfect separation → suspect leakage / a proxy-of-outcome control.
- **Sign flip** between raw and adjusted estimates that you cannot explain mechanically.
- **All coefficients significant at p < 0.001** with tiny SEs → suspect forgotten clustering or ignored panel structure.
- **N silently changes** between models → listwise deletion; align samples and re-run.
- **A placebo/pre-trend test that shows a strong effect.**
- **Means, rates, or totals far from known population benchmarks.**
- **Impossible values** in any variable (negative counts, shares > 1, ages > 120).
- **Reversal of a well-established relationship** with no mechanism offered.

When you hit one, name it, diagnose it, and resolve or document it. Surfacing a problem you found is always better than shipping a table that a reader (or reviewer) will catch.

---

## What to write in the memo

At each phase, add a short **Plausibility Check** block:

```markdown
### Plausibility Check
- **Sanity of quantities**: [ranges/means/units confirmed; anything off?]
- **Benchmark comparison**: [how key figures compare to known values / literature]
- **Cross-specification** (Phase 3–4): [does the preferred design confirm / attenuate /
  overturn the simpler models? state the pattern]
- **Red flags**: [none / list what was found and how resolved]
```
