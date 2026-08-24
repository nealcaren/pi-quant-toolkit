# Reproducibility & Handoff Audit

**Every stage must end reproducible-ready.** Treat each phase (corpus preparation, main analysis, validation, output) as something you are handing to another person — a coauthor, a replicator, a reviewer, or the next phase agent — who has *only* your inputs and your script, not your memory of what you ran. Text pipelines are especially fragile: a single undocumented preprocessing choice (a stopword list, a min-frequency cutoff, a random seed) silently determines the results. Before you close a phase, run a **handoff audit**; at the end, run a **final reproducibility check** that rebuilds every output from the raw corpus in a clean session.

This is a gate, not a suggestion. Do not mark a phase done until its handoff audit passes.

## Why per-stage, not just at the end

If every stage is independently reproducible, a break is local and cheap to fix. In text analysis the preprocessing stage is where reproducibility usually dies — the document-term matrix depends on a dozen choices that are easy to make interactively and forget. Auditing at each handoff keeps that failure surface small.

---

## The per-stage handoff audit (definition of done)

At the end of **each** phase, verify all of the following. Every "no" must be fixed or explicitly documented before proceeding.

**1. Runs top-to-bottom, unattended.** The stage's script runs clean from a fresh session (`Rscript code/NN_stage.R` or `python code/NN_stage.py`) — no manual edits, no notebook cells run out of order, no console-only steps.

**2. Every random operation is seeded.** Topic models, train/test splits, bootstrap, UMAP, K-means, sampling for human coding — all take an explicit seed. Set it at the top; pass it into every model (`topica.LDA(..., seed=13)`, `posterior_theta_samples(..., seed=0)`, `set.seed()`).

**3. The full preprocessing pipeline is in code.** Tokenization, stopwords (the actual list, not "default"), stemming/lemmatization, n-gram/phrase learning, min/max document frequency, and any manual document exclusions are all encoded and reproducible. No "I cleaned that by hand."

**4. Inputs and outputs are explicit and canonical.** Reads only declared inputs (raw corpus or a prior stage's saved DTM/embeddings/model); writes only to canonical paths (`data/processed/`, `output/`). No absolute/personal paths. Save fitted models (`model.save()`) so downstream stages don't refit.

**5. Document counts are logged.** Print N documents (and vocabulary size) at entry and exit, and log every filtering step (empty docs dropped, min-freq pruning, language filter) so the corpus is auditable. An unexplained change in the document count is a *tell* that something is wrong — reconcile it before proceeding (see the Tells section in `concepts/07_plausibility_checks.md`).

**6. Decisions are documented where they happen.** Every non-obvious choice (why K=8, why this stopword added, why these documents excluded, why this threshold) has a one-line comment saying *why*.

**7. Environment is capturable.** Package/model versions are recordable (`sessionInfo()` or `pip freeze` / the `topica` version); dictionaries and lexicons used are saved with the project.

**8. Committed.** The stage's script, saved models, and outputs are committed to git (`text-analyst: Phase N complete`) before the next phase modifies anything. No `-v2` copies.

### Handoff audit block for the memo

Append to `memos/analysis-memo.md` at each phase, after the Plausibility Check:

```markdown
### Handoff Audit
- **Runs clean from fresh session**: [yes / fixed X]
- **Seeds set on all random ops**: [yes / list any unseeded]
- **Preprocessing fully in code**: [tokenization, stopwords list, thresholds, exclusions]
- **Inputs → outputs**: [input files] → [DTM/model/output files], canonical paths only
- **Document-count reconciliation**: [N in → N out, filters logged; vocab size]
- **Committed**: [commit hash / message]
- **Ready for handoff**: [yes / blockers]
```

---

## The final reproducibility check (Phase 5)

Before declaring the analysis complete, prove the whole pipeline reproduces end-to-end.

**1. Clean-room master run.** From a fresh session, run the master script that sources every stage in order and regenerates *every* table, figure, and model from the raw corpus:
```bash
Rscript code/00_master.R      # or: python code/00_master.py
```
Every output must regenerate with no manual intervention and no errors.

**2. Reconcile outputs.** Confirm the regenerated topics/labels/scores match what's in the paper. With seeds fixed, topic top-words, class metrics, and prevalence estimates should be identical run-to-run. (If a neural component is nondeterministic even with a seed, document that and report the tolerance.)

**3. Capture the environment.** Record exact versions for the replication package:
- R: `writeLines(capture.output(sessionInfo()), "output/sessionInfo.txt")`
- Python: `pip freeze > output/requirements.txt` (note the `topica` version explicitly)
- Save all dictionaries/lexicons and hand-coded validation sets used.

**4. Assemble the replication package.** Confirm a stranger could reproduce the results:
- `README.md`: what to run, in what order, expected outputs, corpus access/restrictions, required packages + versions.
- `code/` with numbered scripts + `00_master`.
- `data/`: raw corpus (or instructions to obtain it) and the code that builds the processed corpus/DTM.
- `dictionaries/`, hand-coded validation samples, and `output/` (tables, figures, saved models, version files).
- Every number and topic label in the paper traces to a script that produces it.

### Final reproducibility block for the memo

```markdown
## Final Reproducibility Check
- **Clean-room master run**: [passed / errors fixed]
- **Outputs reconcile with paper**: [topics/labels/scores regenerate identically]
- **Environment captured**: [sessionInfo.txt / requirements.txt incl. topica version]
- **Replication package complete**: [README, code, corpus instructions, dictionaries, validation sets, outputs, saved models]
- **Remaining caveats**: [restricted corpus / nondeterministic neural steps / manual steps, with rationale]
```

---

## Red flags that fail a handoff audit

- Topic or classifier output that **changes when you re-run** → unseeded randomness.
- A DTM or model file with **no script that produces it**.
- Preprocessing done **interactively** (a notebook cell, a hand edit) and not encoded.
- The stopword list / thresholds described as "default" with no record of what that was.
- Document count differs from what the preprocessing stage says it should be.
- A `-v2`/`-final` file instead of a git commit.
- "I relabeled those topics by hand" — any manual output edit not traceable to code + a documented decision.
