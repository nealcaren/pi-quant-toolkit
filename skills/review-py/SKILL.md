---
name: review-py
description: Read-only code review for Python analysis scripts and notebooks (pandas, statsmodels, scikit-learn, and text-analysis pipelines). Checks reproducibility, correctness, pandas/NumPy numerical traps, data leakage, and whether reported numbers match what the code produces — then writes a report WITHOUT editing your files. Use when the user says "review this Python script", "check my notebook", "audit the analysis", or after text-analyst writes code.
---

# Review Python analysis code (read-only)

You review Python analysis code the way a careful methods-minded colleague would:
find problems and propose fixes, but **do not edit the files**. Produce a written
report the researcher can act on. Covers `.py` scripts and `.ipynb` notebooks —
for social-science analysis (pandas/statsmodels/sklearn) and the `text-analyst`
pipelines (topic models, embeddings, classifiers).

> Sibling of `review-r`; same protocol, Python-specific checks.

---

## Step 0 — switch to a stronger, *different* model first (important)

1. **Use a stronger model than the one that wrote the code** — if drafted on the
   cheap default, `/model openrouter/deepseek/deepseek-v4-pro` before reviewing.
2. **Prefer a *different model family* than the author.** Self-review shares blind
   spots; an independent critic catches more.

State which model you're reviewing on, **before** reading the code.

---

## Protocol

1. **Identify the file(s)** the user points to — don't wander the repo.
2. **Read each script/notebook end-to-end** before judging.
3. **For notebooks, check execution order** (see below) — out-of-order cells are
   a top reproducibility failure.
4. **Check every category.**
5. **Write the report** to `quality_reports/<script>_review.md` and summarize the
   top issues in chat.
6. **Do NOT edit any file.**

---

## Review categories

### 1. Reproducibility
- [ ] **All seeds set** for every RNG in play: `random.seed`, `np.random` (prefer
      `rng = np.random.default_rng(seed)` over global `np.random.seed`), and the
      framework — `torch.manual_seed` + deterministic flags, sklearn `random_state=`,
      LDA/BERTopic/UMAP `random_state`/`seed` (UMAP is nondeterministic without it)
- [ ] **Dependencies pinned and declared** — a `uv` PEP-723 header (`# /// script`)
      or a lockfile; run with `uv run`, not a bare `python`/`pip install` (project convention)
- [ ] **Paths relative** via `pathlib.Path(__file__).parent` / a project root — no `/Users/...`
- [ ] **Runs top-to-bottom unattended** (`uv run script.py`)
- [ ] **Notebooks:** cells run cleanly in order from a fresh kernel (Restart & Run All).
      Flag reliance on hidden state, out-of-order execution, or manually-edited outputs.
      For a real pipeline, recommend extracting logic into a `.py` module the notebook imports.

### 2. Numerical & pandas discipline (the quiet bug source)
- [ ] **No float `==`**; use `np.isclose`/`math.isclose`
- [ ] **NaN handling is explicit.** pandas reductions default to `skipna=True` —
      a silently-dropped NaN can change a mean. `groupby` **drops NaN keys by
      default** (`dropna=True`) — is that intended? State it.
- [ ] **Chained assignment / `SettingWithCopyWarning`** — writes go through `.loc`,
      not `df[df.x>0]['y'] = ...`; use `.copy()` when a subset is meant to be independent
- [ ] **Index alignment surprises** — arithmetic on two Series aligns on index, not
      position; a misaligned join can silently produce NaNs or wrong rows
- [ ] **Integer division / dtype** — `int` vs `float` division; unintended `float32`
      (embeddings) losing precision; `astype` truncation
- [ ] **Probability/log clamping** — clip to `[eps, 1-eps]` before `log`/`logit` so 0/1 don't become `±inf`
- [ ] **Deterministic ordering** — don't rely on dict/set iteration order for results;
      sort explicitly; `groupby(sort=...)` set intentionally
- [ ] **Merges/joins validated** — `merge(..., validate="1:1"/"m:1", indicator=True)` and the `_merge` counts checked

### 3. Statistical / ML / domain correctness
- [ ] **No data leakage** — scalers/vectorizers/imputers `fit` on **train only**,
      inside a `Pipeline`, never on the full dataset before splitting; CV done right
- [ ] **Robust/clustered SEs** where the design needs them (`statsmodels`
      `cov_type="cluster", cov_kwds={"groups": ...}`); default IID SEs flagged
- [ ] **Survey weights** applied when using GSS/ANES/ACS microdata (not just unweighted `.mean()`)
- [ ] **Class imbalance / metric choice** appropriate; accuracy not reported on skewed classes without base rate
- [ ] **Text pipelines validated** — topic/label output checked against documents,
      not taken as ground truth; k / hyperparameters justified; preprocessing deterministic and documented
- [ ] Sample restrictions and dropped rows are intentional and logged (`len()` before/after)
- [ ] Model output actually answers the stated research question

### 4. Idioms & clarity
- [ ] **Vectorized** pandas/NumPy over `for`/`iterrows()` (correctness and speed)
- [ ] `pathlib` over string paths; f-strings; no mutable default args (`def f(x=[])`)
- [ ] Functions for repeated logic; light type hints on non-trivial signatures; no magic numbers
- [ ] Header/docstring: purpose, inputs, outputs; logical sections
- [ ] Logging via `logging`/`print` intentionally, not scattered debug spam

### 5. Output & numbers (the integrity check)
- [ ] **Every number quoted in the write-up is traceable to code** that produces
      it — no hand-typed values. Spot-check that a reported figure equals the
      script's actual output (re-run the cell/line if in doubt).
- [ ] Tables/figures written to disk with relative paths, not only shown inline
- [ ] Figures reproducible from code (size/style set in code, not by hand)
- [ ] **Tables exported to Word (`.docx`) by default** (`python-docx`, or a styled pandas table), unless the target journal wants LaTeX
- [ ] **Figures use a colorblind-safe palette** (`seaborn` `"colorblind"`, or `viridis`/`cividis`) — not `jet`/`rainbow`; distinguishable in greyscale

---

## Report format

```markdown
# Python review: <script name>
Reviewed on model: <provider/model>   |   <N> issues (<C> critical, <H> high, <M> medium, <L> low)

## Critical
- **[line/cell NN] <one-line problem>.** Why it matters: … Suggested fix: `…`

## High / Medium / Low
- …

## What's already good
- … (name real strengths — a review is not only complaints)
```

Rate each issue **Critical / High / Medium / Low** (Critical = wrong results or
won't run). In chat, give the **top 3** to fix first. Never edit the code.
