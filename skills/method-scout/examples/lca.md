# Worked example: Latent Class Analysis (LCA)

A concrete pass through the `method-scout` protocol for a method not in the
analysis skills' built-in menu. LCA finds unobserved subgroups ("classes") from
categorical indicators — a common sociological "types of X" analysis. Use this as
the template for scouting any latent-variable method (LPA, mixture models, SEM).

> This shows the *workflow and the decisions*, not copy-paste answers. Read the
> packages' own vignettes (Step 2) for authoritative argument behavior.

## Step 1 — Package choice

**R** (via the *Psychometrics* / *Cluster* Task Views):
- **`poLCA`** — the standard for LCA on categorical (polytomous) indicators. Mature,
  JSS-documented. Indicators must be coded as consecutive positive integers.
- **`tidySEM`** — a modern, tidyverse-friendly wrapper (LCA/LPA/mixtures) with
  built-in class-enumeration and plotting; good diagnostics. Consider for a cleaner
  workflow and figures.
- **`mclust`** — for *continuous* indicators (latent profile analysis), not LCA.

**Stata:** no add-on needed — LCA is built into **`gsem, lclass()`**. Read
`help gsem` and the *Stata Journal* LCA references.

Surface the choice to the user; default to `poLCA` (categorical) or `tidySEM` for
figures/enumeration, and note the alternative.

## Step 2 — Read the vignette first

```r
citation("poLCA"); ?poLCA::poLCA          # arguments, data coding rules
browseVignettes("tidySEM")                 # mixture-model vignette
```
Key things the docs tell you (don't guess these): indicators must be coded
`1..K` positive integers; the model formula is `cbind(y1, y2, ...) ~ 1` for
unconditional LCA; `nrep` controls random starts; `maxiter` the EM iterations.

## Step 3 — Fit a range of solutions and select the number of classes

The central LCA decision is **how many classes** — a research decision, made with
evidence, not a default. Fit 1..K and compare.

```r
library(poLCA)
set.seed(20240824)                          # reproducibility: seed the random starts
f <- cbind(ind1, ind2, ind3, ind4, ind5) ~ 1

models <- lapply(1:6, function(k)
  poLCA(f, data = df, nclass = k,
        nrep = 20,        # multiple random starts — LCA likelihoods are multimodal
        maxiter = 5000,
        verbose = FALSE))

# Model-selection table: lower BIC is better; also watch entropy & class sizes
tibble::tibble(
  classes  = 1:6,
  logLik   = sapply(models, \(m) m$llik),
  BIC      = sapply(models, \(m) m$bic),
  AIC      = sapply(models, \(m) m$aic),
  min_size = sapply(models, \(m) min(table(m$predclass)) / nrow(df))
)
```

Selection criteria to weigh together (name them in the memo, don't cherry-pick one):
- **BIC** (and AIC) — prefer the elbow / minimum; BIC penalizes complexity more.
- **Entropy / classification certainty** — how cleanly cases sort into classes.
- **Bootstrap likelihood-ratio test (BLRT)** — is k classes better than k−1?
  (`tidySEM::BLRT()` or the `poLCA`-based helpers.)
- **Interpretability & class size** — a statistically-favored solution with an
  uninterpretable or tiny (<5%) class is often not the right substantive choice.
- **Convergence** — confirm each retained model converged (`m$numiter < maxiter`,
  no boundary warnings); re-fit with more `nrep` if a solution is unstable.

## Step 4 — Interpret and validate

```r
best <- models[[3]]                         # e.g. the 3-class solution
best$probs        # class-conditional response probabilities -> label the classes
best$P            # estimated class shares
poLCA::poLCA.table                          # or plot item-response profiles
df$class <- best$predclass                  # modal-class assignment (note: ignores
                                            # classification uncertainty — flag it)
```
- **Label classes from the response-probability profiles**, substantively — not
  "Class 1/2/3." State what distinguishes each.
- **Plausibility**: do the class sizes and profiles make sense against theory and
  the raw data? A class that's a coding artifact is a *tell* to investigate.
- **Downstream caution**: using modal class as a predictor in a later regression
  ignores classification error; mention three-step / BCH approaches (in `tidySEM`)
  if the user goes there.

## Stata equivalent (built-in)

```stata
gsem (ind1 ind2 ind3 ind4 ind5 <- ), logit lclass(C 3) startvalues(randomid, draws(20) seed(20240824))
estat lcprob        // class shares
estat lcmean        // class-conditional means/probabilities
estat ic            // AIC/BIC for comparing 1..k (fit each and compare)
```
Fit `lclass(C 1)` … `lclass(C 6)`, collect `estat ic`, and select as above.

## Reproducibility notes

- Seed the random starts (`set.seed` / `seed()`), and use enough starts (`nrep`/
  `draws`) that the best solution replicates — LCA log-likelihoods are multimodal
  and a single start can land on a local optimum.
- Pin the package version (`renv::snapshot()`), record it, and pass the stage
  handoff audit before moving on.
