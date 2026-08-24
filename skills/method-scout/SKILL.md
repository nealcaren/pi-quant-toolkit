---
name: method-scout
description: Protocol for adopting a statistical method that isn't in the analysis skills' built-in technique menu (e.g. latent class analysis, mixture models, SEM, survival, sequence analysis, GEE). Instead of guessing an API from memory, it finds the maintained, canonical package via the ecosystem's own index, reads and follows the package's vignette, applies the same identification/validation/reproducibility discipline, and benchmarks against the vignette before touching real data. Use when a user asks for a method r-analyst/stata-analyst/text-analyst don't already have a technique guide for, or says "how do I do <method> in R/Stata/Python".
---

# Method scout — adopting an unfamiliar method safely

The analysis skills carry technique guides for a core menu (DiD, IV, RD, matching,
panel, synthetic control, Bayesian, nonlinear, topic models…). Sociology routinely
needs methods outside that menu — latent class analysis, finite mixture models,
SEM/CFA, multilevel models, event-history/survival, sequence analysis, GEE. When a
requested method isn't in the built-in guides, **do not improvise the API from
memory** — model-recalled function signatures for less-common packages are a
frequent source of silently-wrong results. Follow this protocol.

The point is a *procedure* that scales to any method, not a list of methods.

## Core principles

1. **Use the ecosystem's index, not your memory.** Find the maintained package
   through the language's own catalog (CRAN Task Views, Stata SSC / Stata Journal,
   PyPI + the scientific stack) — not from a half-remembered function name.
2. **Read the vignette; follow the authors.** The package authors document the
   intended workflow, the arguments that matter, and the pitfalls. Follow *their*
   recommended path before deviating.
3. **Same discipline as any analysis.** Identification/assumptions first, then
   method-appropriate validation, plausibility checks, and reproducibility — the
   novelty of the method doesn't suspend the standards in `plausibility_checks.md`
   and `handoff_audit.md`.
4. **Benchmark before you trust.** Reproduce the vignette's worked example (or a
   textbook result) so you know your call is correct, *then* run on the real data.
5. **Never fabricate.** If you can't verify how an argument behaves, say so and
   read the docs — don't assert a default you're guessing.

## Step 1 — Find the canonical, maintained package

Use the language's own index. Prefer packages that are actively maintained, widely
cited, and documented.

### R
- **CRAN Task Views** are the map: browse the relevant one at
  <https://cran.r-project.org/web/views/> or install `ctv` and read it in-session.
  Relevant views by method family:
  - *Cluster* → finite mixture & model-based clustering (`mclust`, `flexmix`)
  - *Psychometrics* → LCA, IRT, SEM (`poLCA`, `tidySEM`, `lavaan`, `mirt`)
  - *MixedModels* → multilevel/HLM (`lme4`, `glmmTMB`)
  - *Survival* → event history (`survival`, `survminer`)
  - *SocialSciences*, *Econometrics* → broad
- Cross-check maintenance: last CRAN update, a JSS/`citation()` paper, active
  GitHub. A package untouched for years with no vignette is a yellow flag.

### Stata
- **`search <method>`** and **`ssc describe <pkg>`** for community commands from
  the SSC archive; **Stata Journal** articles document many (`search sj`).
- Check **built-in** first — Stata's `gsem`, `sem`, `meglm`, `mecmd`, `stcox`
  cover a lot (LCA is built into `gsem, lclass()`; no add-on needed).
- Read the `help <command>` file end-to-end before running.

### Python
- Prefer the **scientific stack** over a random PyPI hit: `statsmodels` (models +
  robust/clustered SEs), `scikit-learn` (ML, mixtures via `GaussianMixture`),
  `lifelines` (survival), `semopy` (SEM), `pymc` (Bayesian). Check GitHub
  activity, releases, and docs quality before adopting anything niche.
- Declare the dependency in a `uv` PEP-723 header and run with `uv run`.

> **Secondary route — a paper's replication package.** To copy a *known-good
> specification* for the method, you can find a published paper that used it and
> read its replication code (often on Dataverse — use the `data-acquisition`
> skill). This is a reference for how experts specified the model, **not** the way
> to find the software itself.

## Step 2 — Read and follow the vignette

- **R:** `vignette(package = "poLCA")`, `browseVignettes("tidySEM")`, and the
  reference `?function`. Many packages have a JSS paper — read it.
- **Stata:** the `help` file's *Examples* and the Stata Journal article.
- **Python:** the package's docs site and `examples/` — run their example.

Extract from the docs: the exact function/command, the arguments that control the
model, the required data shape, the diagnostics the authors recommend, and the
known failure modes. Do not substitute an argument you *think* exists.

## Step 3 — Apply the standard discipline

- **Identification/assumptions first** — what does this method assume, and does the
  design/data support it? (For LCA: conditional independence within class,
  meaningful indicators, a decision rule for the number of classes.)
- **Method-appropriate validation** — every method has its own "did this work"
  checks (model selection criteria, convergence, class separation, fit indices,
  proportional-hazards tests). Name them and run them; a model that merely *ran*
  is not a validated model.
- **Plausibility** — translate the output into a plain claim and sanity-check it
  against what's known (`techniques/09_plausibility_checks.md`).
- **Reproducibility** — seed any randomness (mixtures/LCA use random starts;
  always set multiple starts *and* a seed), pin the package version, and pass the
  stage's handoff audit (`techniques/10_handoff_audit.md`).

## Step 4 — Benchmark, then run for real

Reproduce the vignette's worked example (or a known textbook result) and confirm
you get the documented numbers. Only then apply the method to the user's data.
This catches wrong-argument and wrong-data-shape mistakes before they contaminate
the analysis.

## When to pause for the user

Surface the method-specific research decisions rather than deciding silently:
package choice when there are real alternatives, the number of classes/factors,
the model-selection rule, and any assumption the data strains. These are the
researcher's calls; you supply the options and the evidence.

> **Model tier.** Method selection and reading vignettes is exactly the careful,
> multi-step reasoning the cheap default model is weakest at. Suggest the user
> switch to the stronger model (`/model openrouter/deepseek/deepseek-v4-pro`) for
> this protocol.

## Worked example

- `examples/lca.md` — latent class analysis end-to-end in R (`poLCA`/`tidySEM`)
  and Stata (`gsem, lclass()`): package choice, class enumeration, model selection
  (BIC/entropy/bootstrap LRT), interpreting class-conditional probabilities,
  reproducibility. Use it as the template for scouting any latent-variable method.
