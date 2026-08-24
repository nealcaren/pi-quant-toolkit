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

## Phase 1: Descriptives plausibility

Before any modeling, confirm the data describes a world that could exist.

**Range and bounds:**
```r
# Every variable should live inside its logically possible range.
psych::describe(analysis_data)   # min/max/mean/sd/skew at a glance

# Explicit impossible-value checks — write one per variable with known bounds
analysis_data |> summarise(
  age_bad      = sum(age < 0 | age > 120, na.rm = TRUE),
  prop_bad     = sum(share < 0 | share > 1, na.rm = TRUE),   # proportions in [0,1]
  pct_bad      = sum(pct < 0 | pct > 100, na.rm = TRUE),     # percentages in [0,100]
  count_bad    = sum(events < 0, na.rm = TRUE),              # counts non-negative
  dollars_bad  = sum(income < 0, na.rm = TRUE)
)
```

**Ask, for each key variable:**
- Is the **mean** where you'd expect? (A mean income of \$52 vs \$52,000 vs \$52M tells you the units.)
- Is the **unit of measurement** what you assumed? (dollars vs thousands of dollars; rate per 100 vs per 100,000; monthly vs annual)
- Does the **SD** imply a sensible spread, or is it implausibly tight/wide?
- Do **categories** have the levels and shares you expect? (`table(x, useNA = "ifany")` — are there unexpected codes like -99, 999, blank strings?)
- Is the **N** what you expected, and do subgroup **cell counts** support the planned design (e.g., enough treated pre/post units for DiD)?

**Benchmark against the outside world.** When a variable has a known population value, compare:
```r
# e.g., does sample unemployment roughly match the official rate for these years?
mean(analysis_data$unemployed, na.rm = TRUE)   # compare to BLS/Census/known figure
```
A sample that says 40% unemployment when the real figure is 5% signals a coding, weighting, or sampling problem — not a finding.

**Bivariate signs sanity check.** Before controls, do the raw relationships point the expected way?
```r
analysis_data |>
  summarise(cor_xy = cor(x, outcome, use = "complete.obs"))
# If theory says X and Y move together and the raw correlation is strongly negative,
# resolve that puzzle now — it will not go away when you add controls.
```

**Missingness plausibility.** Is the amount and pattern of missing data believable, and is it correlated with treatment/outcome in a way that threatens the design? (See Phase 4 for formal tests.)

---

## Phase 3: Results plausibility

Once you have coefficients, interrogate them before you believe them.

**1. Sign.** Does the coefficient's sign match theory *and* the Phase 1 bivariate relationship?
- Sign matches expectation → note it, move on.
- Sign flips from the raw correlation when you add controls → **investigate**. This can be legitimate (confounding, suppression, Simpson's paradox) or a bug (mis-coded variable, wrong reference category, collinearity). Do not report a flip you cannot explain.

**2. Magnitude.** Interpret the effect in real units and ask if it is believable.
```r
# Translate to substantive scale: effect relative to the outcome's own SD
b   <- coef(model)["treatment"]
sdy <- sd(analysis_data$outcome, na.rm = TRUE)
b / sdy   # a treatment effect of 3+ SDs is almost always too big to be real
```
- Compare the effect to the outcome's plausible range, its mean, and its SD.
- Compare to published estimates for similar treatments. An effect an order of magnitude larger than the literature is a red flag, not a breakthrough.
- A coefficient larger than the outcome could ever plausibly move (e.g., "increases test scores by 400 points" on a 0–100 scale) means something is wrong — often a units/scaling error.

**3. Precision.** Is the standard error believable?
- Absurdly tiny SEs (everything at p < 0.001) often mean clustering was forgotten or the panel structure was ignored.
- Absurdly huge SEs often mean collinearity or too few effective clusters.
- Check that **N in the regression matches** the analysis sample you built in Phase 1. Silent listwise deletion can shrink the sample dramatically.

**4. Fit.** Is R² (or pseudo-R²) in a plausible range for this kind of data?
- **R² ≈ 1** in observational social data almost always means leakage — a "control" that is a near-proxy of the outcome, or the outcome accidentally on both sides.
- Perfect classification / perfect separation in a logit is the same warning.

**Units-and-belief statement (write this every time):**
> "Model X implies that [treatment] changes [outcome] by [magnitude in real units], which is [about Z% of the outcome mean / Z SDs]. This is [plausible because... / surprisingly large because... / implausible and needs checking because...]."

---

## Cross-specification consistency (the confirm-or-overturn question)

Whenever you estimate a sequence of models — naive OLS → +controls → +fixed effects → DiD/IV — **explicitly report what each step does to the estimate of interest.** This is one of the most informative things you can tell a reader, and it is easy to lose in a table of stars.

Build the comparison mechanically so the pattern is unmissable:
```r
library(modelsummary)

specs <- list(
  "OLS (raw)"        = m_ols,
  "OLS + controls"   = m_controls,
  "Unit + time FE"   = m_twfe,
  "DiD / IV"         = m_main
)

# Extract just the coefficient of interest across specs
comparison <- modelsummary(specs, output = "data.frame",
                           coef_map = c("treatment" = "Treatment"),
                           gof_map = "nobs")
print(comparison)
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
- Each robustness row should be compared to Main using the confirm / attenuate / overturn language above.
- **Placebo tests must pass:** a pre-treatment or fake-timing "effect" that is large and significant means the design is picking up something other than the treatment. A placebo that "works" is a failure.
- **Sample size must stay stable** across robustness specs unless a restriction is the point; unexplained N changes signal silent deletion.
- **Sensitivity to unobservables (sensemakr):** translate the robustness value into words — "a confounder 3× as strong as [strongest control] would be needed to overturn this; that is implausible here because..."

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
