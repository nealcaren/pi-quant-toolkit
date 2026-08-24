---
name: stat-check
description: Guard against hallucinated statistics in write-ups. Defines the results-ledger convention (analysis scripts emit every reportable number to output/results.json at full precision) and runs a reconciliation pass that flags any number in a report's prose that doesn't trace back to a computed value ("orphans"). Use after drafting a Results/findings memo or report, before finalizing, or whenever the user asks to check that reported numbers match the analysis. Invoked by r-analyst/stata-analyst Phase 5, the review skills, and repro-package.
---

# stat-check — no number in the prose the analysis didn't compute

The most dangerous error a research assistant can make is a **wrong statistic
stated confidently** — a coefficient, N, p-value, or CI that was hand-typed from
memory and drifted from what the model actually produced. On a cheap model, with
context that gets summarized across a long project, this is a real risk, not a
hypothetical one. `stat-check` replaces the *norm* "don't invent numbers" with a
*mechanism*: numbers are extracted from computation, not typed, and a pass verifies
every number in the prose against what was computed.

Two parts: the **results ledger** (write numbers down at compute time) and the
**reconciliation pass** (check the report against the ledger).

## Part 1 — The results ledger (single source of truth)

Every analysis phase writes each reportable statistic to `output/results.json`
(or the project's tables path) at **full precision**, with metadata. The write-up
then reads named quantities from the ledger — it never restates a number the model
recalled from conversation.

Recommended shape (the reconciler doesn't enforce it — it treats *every* number
anywhere in the JSON as "known" — but this shape gives you traceability):

```json
{
  "sample": { "n": 1204, "n_treated": 402 },
  "results": [
    { "id": "main_effect", "term": "treatment", "model": "m3",
      "estimate": 0.3421, "se": 0.112, "p": 0.0023,
      "ci_low": 0.122, "ci_high": 0.562, "n": 1204 }
  ],
  "r2": 0.291
}
```

Rules:
- **Full precision in the ledger; round only when rendering.** Storing rounded
  values defeats the check and creates rounding drift.
- **One entry per reportable quantity**, with a stable `id` you can cite in prose
  ("(results.json: main_effect)").
- **Emit from the object, never by hand.** Pull straight from the fitted model.

### Emit snippets

**R** (`broom` + `jsonlite`):
```r
library(broom); library(jsonlite)
tidym <- tidy(m3, conf.int = TRUE)
ledger <- list(
  sample  = list(n = nobs(m3)),
  results = lapply(split(tidym, tidym$term), \(r) list(
    id = r$term, term = r$term, estimate = r$estimate, se = r$std.error,
    p = r$p.value, ci_low = r$conf.low, ci_high = r$conf.high)),
  r2 = summary(m3)$r.squared
)
write_json(ledger, "output/results.json", auto_unbox = TRUE, digits = 10)
```

**Stata** (write scalars after estimation):
```stata
matrix b = e(b)
file open L using "output/results.json", write replace
file write L "{" _n `"  "n": "' (e(N)) "," _n
file write L `"  "main_effect": {"estimate": "' (b[1,1]) `", "n": "' (e(N)) "}"' _n "}" _n
file close L
* Or use a JSON helper (e.g. -insheetjson-/-jsonio- from SSC) for many terms.
```

**Python** (`statsmodels` + `json`):
```python
import json
led = {
    "sample": {"n": int(res.nobs)},
    "results": [{"id": name, "estimate": float(res.params[name]),
                 "se": float(res.bse[name]), "p": float(res.pvalues[name]),
                 "ci_low": float(res.conf_int().loc[name, 0]),
                 "ci_high": float(res.conf_int().loc[name, 1])}
                for name in res.params.index],
    "r2": float(res.rsquared),
}
json.dump(led, open("output/results.json", "w"), indent=2)
```

## Part 2 — The reconciliation pass

After a report/memo is drafted, run the bundled reconciler. It extracts every
numeric token from the prose and checks each against the ledger.

```bash
uv run skills/stat-check/scripts/reconcile_report.py \
    --report memos/analysis-memo.md \
    --ledger output/results.json --show-matched
```

(Needs `uv` — install per `skills/data-acquisition/sources/dataverse.md` if the
student doesn't have it. The script has no third-party dependencies.)

It sorts every number into:
- **matched** — traces to a ledger value (rounding-aware; `0.34` matches `0.3421`,
  `1,204` matches `1204`, `48.7%` matches `0.487`). Reported with the ledger path.
- **p-threshold / convention** — `p < .05`, `5% level`, `95% CI`: conventional
  cutoffs, not data; not checked.
- **structural** — `Table 2`, `Model 3`, `Section 4`: references, not data.
- **year?** — bare 4-digit numbers in 1900–2099; verify if one is actually a
  substantive quantity.
- **ORPHAN** — a number that appears **nowhere** in the computed results. This is
  the hallucination signature.

**Exit status gates a workflow:** 0 if no orphans, 1 if any orphan (use
`--warn-only` to report without failing). `--tol` sets an absolute tolerance floor.

### What to do with orphans

Each orphan must be resolved one of two ways — never left standing:
1. **It's real but unlogged** → the analysis computed it but didn't write it to the
   ledger. Add it to `results.json` (emit it from the object), then re-run.
2. **It's wrong / invented** → correct it to the computed value or remove the
   claim. A number that lives only in prose is a red flag by definition.

Do not "pass" the check by loosening tolerance or deleting the check — fix the
number or the ledger.

## How this wires into the toolkit

- `r-analyst` / `stata-analyst` **Phase 5** emit `output/results.json` and run the
  reconciliation before the report is called done.
- `review-r` / `review-stata` / `review-py` treat a clean reconciliation as part
  of the numbers-match-script check.
- `repro-package` requires the reconciliation to pass for the archived report.

> **Not a substitute for reading.** The reconciler proves a number *exists* in the
> computed output; it does not prove you cited the *right* one (an estimate where
> you meant the SE still "matches"). Pair it with the human/again-model check that
> each number is the correct quantity in the correct place.
