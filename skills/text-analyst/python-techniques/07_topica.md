# Topica: unified topic modeling in Python

`topica` (https://github.com/nealcaren/topica) is a NumPy-native, Rust-backed topic-modeling library that unifies 50+ models — classical and neural — under one consistent API aimed at social scientists. **For most topic-modeling tasks in this skill, prefer `topica`**: it removes the historical R-vs-Python split (you no longer need R's `stm` for structural topic models), gives every model the same `fit` / diagnostics interface, and validates against the reference implementations (R `stm`, MALLET, keyATM) while running faster.

Reach for `topica` when the user wants topic models (LDA, STM, NMF, BERTopic, KeyATM, CTM/DTM/HDP, ETM). Use the neural stack in `03_topic_models.md` (raw BERTopic + sentence-transformers) only when you need something `topica` does not expose.

## Install

```bash
pip install topica
# optional extras:
# topica[viz]     matplotlib visualizations
# topica[formula] R-style formulas for covariates
# topica[polars]  Polars DataFrames
# topica[llm]     LLM-powered topic labeling (OpenAI or local ollama)
```

Pure-Rust dependencies — no PyTorch required for the core and embedding models (petal-clustering for HDBSCAN, umap-rs for optional reduction). Record the installed version in the replication package (see `concepts/08_handoff_audit.md`).

## Core workflow

Load → build a `Corpus` (metadata stays aligned through preprocessing) → fit a model → analyze.

```python
import topica

df = topica.datasets.load_gadarian()
corpus = topica.from_dataframe(
    df, text_col="open.ended.response",
    stopwords=topica.data.ENGLISH_STOPWORDS,
)

model = topica.LDA(num_topics=5, seed=13)   # ALWAYS set seed for reproducibility
model.fit(corpus)
print(topica.summary(model))
```

Structural topic model with covariates (prevalence), plus effect estimation — the workflow that used to require R `stm`:

```python
prevalence = corpus.metadata[["treatment"]]
stm = topica.STM(num_topics=5, seed=13)
stm.fit(corpus, prevalence, prevalence_names=["treatment"])

draws  = topica.effects.posterior_theta_samples(stm, nsims=30, seed=0)
effect = topica.effects.estimate_effect(
    draws, prevalence, feature_names=["treatment"]  # cluster-robust SEs
)
```

## Models (partial)

| Class | Use |
|-------|-----|
| `LDA` | Classical latent Dirichlet allocation (collapsed Gibbs) |
| `STM` | Topics as a function of document covariates |
| `NMF` | Deterministic matrix-factorization alternative |
| `BERTopic` | Embedding + clustering approach |
| `KeyATM` | Keyword/seed-assisted topics |
| `GSDMM` | One topic per short document (tweets, headlines) |
| `CTM`, `DTM`, `HDP` | Correlated, dynamic (over time), hierarchical |
| `ETM`, `DETM` | Embedding-based topic models |

All models share: `fit(...)`, `topic_word` (φ), `doc_topic` (θ), `top_words(n)`, `save()` / `load()`.

## Diagnostics & validation (use these in Phase 4)

`topica` builds the validation toolkit directly into the API — lean on it:

- `coherence()` — `u_mass`, `c_v`, `c_uci`, `c_npmi`
- `exclusivity()`, `topic_diversity()` — topic distinctiveness
- `search_k()` — evaluate the number of topics K across a grid
- `bootstrap_stability()` — how stable are topics across resamples (reproducibility of the solution)
- `ensemble()` — combine multiple runs into a consensus model
- `label_topics()` / `label_topics(..., method=...)` — FREX, lift, relevance, or LLM labeling
- `estimate_effect()` — covariate effects with cluster-robust SEs

Utilities: `tokenize()`, `learn_phrases()` / `apply_phrases()` (collocations), `one_hot()`, `spline()`, `interaction()` (covariate design), and the `Corpus` class for aligned metadata.

## Notes for this skill

- **K is not just a metric.** Use `search_k()` and `coherence()` to bound the choice, but pick a K whose topics are interpretable (see `concepts/02_topic_models.md`). Report the diagnostics *and* your substantive reasoning.
- **Always pass `seed=`** on the model and on `posterior_theta_samples`/bootstrap so runs reproduce. This is required by the handoff audit (`concepts/08_handoff_audit.md`).
- **Face-validity first.** After `fit`, read `top_words()` and a sample of high-θ documents per topic before believing any topic label (`concepts/07_plausibility_checks.md`).
- **Cross-check.** When feasible, compare a `topica` LDA/STM solution against BERTopic or NMF via `coherence()`/`bootstrap_stability()` and note whether they converge on similar themes.
