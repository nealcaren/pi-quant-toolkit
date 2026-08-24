---
name: review-r
description: Read-only code review for R analysis scripts. Checks reproducibility, correctness, numerical discipline, modern tidyverse idioms, and clarity, then writes a report WITHOUT editing your files. Use when the user says "review this R script", "check my R code", "audit the analysis code", "is this R correct", or after r-analyst writes a script. Recommends switching to a stronger/different model for the review pass.
---

# Review R scripts (read-only)

You are reviewing R analysis code the way a careful methods-minded colleague
would: you find problems and propose fixes, but you **do not edit the files**.
You produce a written report the researcher can act on.

> **Inspired by** Pedro H. C. Sant'Anna's `r-reviewer` and `r-code-conventions`
> in [pedrohcgs/claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow) (MIT).
> This is our own write-up of the idea; credit for the review protocol and the
> numerical-discipline checklist goes to him.

---

## Step 0 — switch to a stronger, *different* model first (important)

A review is only as good as the critic. Two rules, in order of impact:

1. **Use a stronger model than the one that wrote the code.** If you drafted the
   analysis on the cheap default (`deepseek-v4-flash`), tell the user to switch
   before reviewing:

   ```
   /model openrouter/deepseek/deepseek-v4-pro
   ```

2. **Prefer a *different model family* than the one that wrote it.** A model
   reviewing its own output shares its own blind spots — it tends to bless its
   own mistakes. An independent critic from another family catches more. If the
   user has access, suggest reviewing with a different provider's model (e.g. a
   Claude or GPT model on OpenRouter) than they wrote with.

If the user is already on a strong model, say so and proceed. Do this check
**first**, before reading the code — state which model you're reviewing on.

---

## Protocol

1. **Identify the script(s).** One file if named; otherwise the `.R` files the
   user points to (don't wander the whole repo).
2. **Read each script end-to-end** before judging anything.
3. **If a `tidy-r` skill is available**, use its conventions as the modern-idiom
   standard (native `|>`, `.by`, `join_by()`, `map_*`).
4. **Check every category below.**
5. **Write the report** to `quality_reports/<script>_review.md` (create the
   folder). Also summarize the top issues in chat.
6. **Do NOT edit any `.R` file.** Fixes come after the researcher reads the
   report and decides.

---

## Review categories

### 1. Reproducibility
- [ ] `set.seed()` set **once** at the top (never inside loops/functions) for any randomness
- [ ] Packages loaded at the top with `library()` (not `require()`)
- [ ] All paths **relative to the project root** — no `/Users/...` or `C:\...`
- [ ] Output folders created with `dir.create(..., recursive = TRUE)`
- [ ] Would run top-to-bottom on a fresh clone via `Rscript`

### 2. Numerical discipline (the quiet bug source)
- [ ] **No float equality** — never `==` on doubles; use `all.equal()` or `abs(a - b) < tol`
- [ ] **Clamp probabilities** before `qnorm()`/`log()`: `p <- pmin(1 - eps, pmax(eps, p))` (e.g. `eps <- 1e-12`) so exact 0/1 don't become `±Inf`
- [ ] **Explicit `na.rm =`** on `mean()`/`sd()`/`sum()` when NAs are possible — never rely on the default silently
- [ ] **Pre-allocate** before loops (`numeric(n)`, `vector("list", n)`); don't grow with `c()`
- [ ] **`TRUE`/`FALSE`, never `T`/`F`** (T/F are reassignable variables)
- [ ] **Deterministic bootstrap** — seed before, and for nested resampling seed per replicate (`seed_base + b`)

### 3. Statistical / domain correctness
- [ ] Estimator matches the intended method (e.g. clustering level, FE absorbed, weights applied)
- [ ] Standard errors clustered at the right level; note if unclustered by default
- [ ] Sample restrictions and dropped observations are intentional and logged
- [ ] Any known package pitfalls handled (e.g. staggered-DiD → not plain TWFE)
- [ ] Model output actually answers the stated research question

### 4. Modern R idioms (defer to `tidy-r` if present)
- [ ] Native pipe `|>`, not `%>%`
- [ ] `.by =` for per-operation grouping instead of `group_by()` + `ungroup()`
- [ ] `join_by(...)`, not `by = c("a" = "b")`
- [ ] `map_*()` over `sapply()` for type stability; `\(x)` lambdas
- [ ] `snake_case` names; verbs for functions, nouns for data

### 5. Structure & clarity
- [ ] Header block: title, author, purpose, inputs, outputs
- [ ] Numbered sections (0 Setup → 1 Data → 2 Estimation → 3 Output)
- [ ] Non-trivial functions documented; no magic numbers; named return values
- [ ] No `cat()`/`print()` used as progress spam; `message()` sparingly

### 6. Output & figures
- [ ] Tables/figures written to disk with relative paths, not just printed
- [ ] Numbers in the script match any numbers quoted in the write-up
- [ ] Figures reproducible (theme/dimensions set in code, not by hand)
- [ ] **Tables exported to Word (`.docx`) by default** (`modelsummary`/`flextable`), unless the target journal wants LaTeX
- [ ] **Figures use a colorblind-safe palette** (Okabe–Ito categorical, viridis continuous) — not hand-picked colors; distinguishable in greyscale

---

## Report format

Write the report as:

```markdown
# R review: <script name>
Reviewed on model: <provider/model>   |   <N> issues (<C> critical, <H> high, <M> medium, <L> low)

## Critical
- **[line NN] <one-line problem>.** Why it matters: … Suggested fix: `…`

## High
- …

## Medium / Low
- …

## What's already good
- … (name real strengths — a review is not only complaints)
```

Rate each issue **Critical / High / Medium / Low**. Critical = wrong results or
won't run. Then, in chat, give the researcher the **top 3** to fix first.

Never edit the code. Hand back the report and let them decide.
