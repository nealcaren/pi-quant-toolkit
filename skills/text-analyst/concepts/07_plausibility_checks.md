# Plausibility Checks

**The user may not be an expert in the corpus or the code. Your job is to catch the topic, score, or classification that is wrong, meaningless, or an artifact before it reaches a table.** Text methods fail quietly — a topic model always returns topics, a classifier always returns labels, a sentiment scorer always returns a number, even when the input is garbage. At every stage, translate the output into a plain-language claim and ask: *does this actually describe the documents?* If you cannot show it does, do not report it.

Consult this guide in Phase 1 (corpus), Phase 3 (results), and Phase 4 (validation). It complements — does not replace — the formal validation in `concepts/06_validation_strategies.md`.

## The core habit

For every result — a topic, a class prediction, a sentiment score, a prevalence estimate — do three things:

1. **State it in words.** "Topic 4 is about immigration enforcement." "The classifier labels 62% of posts as toxic." "Coverage of the policy is 0.3 SD more negative post-2016."
2. **Go back to the documents.** Read a sample of the actual texts the number is built from. Face validity beats any coherence score.
3. **Flag, don't launder.** If a topic is incoherent, a class boundary is nonsense, or a score contradicts a read of the text, say so. A model's output is a hypothesis about the corpus, not a finding.

Never present a text-analysis result you have not checked against the underlying documents.

---

## Phase 1: Corpus plausibility

Before modeling, confirm the corpus is what you think it is.

- **Counts and coverage.** Is the document count what you expected? Are there empty, duplicate, or truncated documents? `n` per subgroup/time period adequate for the planned comparison?
- **Language and encoding.** Right language(s)? Mojibake, HTML tags, boilerplate (headers, signatures, retweet prefixes) that will dominate the vocabulary?
- **Length distribution.** Are documents long enough for the method? (LDA on 5-word tweets → use GSDMM; huge boilerplate docs → trim.) Check min/median/max token counts.
- **Vocabulary sanity.** After preprocessing, do the top terms look like content, or like artifacts (`http`, `amp`, `rt`, numbers, stopwords that slipped through)? Read the top 100 terms.
- **Metadata alignment.** If you'll use covariates (STM/`estimate_effect`), confirm each document's metadata row actually matches the document.

A vocabulary dominated by junk tokens is the single most common cause of uninterpretable topics. Fix it here, not after modeling.

---

## Phase 3: Results plausibility

**Topic models — read before you believe:**
- For **every** topic, look at `top_words()` **and** a sample of the highest-probability documents. A label you cannot justify from reading real documents is not a topic — it may be a stopword cluster, a boilerplate artifact, or a junk-token bin.
- Does topic **prevalence** match intuition? A "topic" that is 0.4 of the corpus and whose top words are function words is a preprocessing failure, not a theme.
- Are topics **distinct**, or are several the same theme? (Check `exclusivity()` / `topic_diversity()`; if two topics share top words, K may be too high.)
- Do covariate effects have a **believable sign and size**? "Treatment moves topic prevalence by 40 points" is almost always too large.

**Classifiers — check the boundary makes sense:**
- Run the model on **obvious cases** you hand-pick. Does a clearly toxic sentence get labeled toxic? A clearly neutral one, neutral?
- **Compare accuracy to the base rate**, never to zero. 85% accuracy is worthless if 85% of documents are the majority class. Report precision/recall/F1 per class, and the confusion matrix.
- Read a sample of **false positives and false negatives** — do the errors reveal a systematic bias (e.g., flags anything mentioning a group)?

**Dictionary / sentiment — validate the instrument:**
- Score a handful of **known-polarity documents**; do the scores come out right?
- Read the documents at the **extremes** — are the most "positive" documents actually positive, or are they long documents that accumulate hits?
- Check whether scores are **confounded by length**; normalize if so.

**Face-validity statement (write this every time):**
> "Result X says [claim]. I read [N] of the underlying documents; they [do / do not / partly] support this because [evidence]."

---

## Cross-method consistency (the confirm-or-overturn question)

When you have more than one lens on the same construct, **compare them and report whether they agree**, exactly as an econometric analysis compares OLS to FE/DiD:

| Pattern | Example | What to report |
|---|---|---|
| **Converge** | LDA, NMF, and BERTopic all surface the same immigration theme; dictionary and supervised sentiment correlate strongly | "Three methods with different assumptions recover the same structure — strong evidence the theme is real, not an artifact of one algorithm." |
| **Partly agree** | Topics align but one method splits a theme the other merges | "Robust to method choice at the coarse level; the finer split is model-dependent, so I treat it cautiously." |
| **Diverge / overturn** | Dictionary sentiment says coverage is positive; a supervised classifier trained on hand-labels says negative | **Flag prominently.** "The off-the-shelf lexicon and the corpus-trained classifier disagree; the lexicon is likely mismatched to this domain. I trust the validated classifier and report the discrepancy." |

Convergence across methods that make different assumptions is one of the strongest validity arguments available in text analysis. Divergence is a finding about method sensitivity — surface it, don't average it away.

---

## Phase 4: Validation plausibility

- **Human validation must actually happen.** Hand-code a sample, compute agreement with the model (see `concepts/06_validation_strategies.md`), and report it. Coherence scores are not a substitute for reading.
- **Stability.** Refit with different seeds and (for K) nearby values. Do the headline topics survive? (`bootstrap_stability()` in `topica`.) A finding that vanishes when the seed changes is not a finding.
- **Sensitivity to preprocessing.** Does the result hold under a reasonable alternative stopword list / min-doc-frequency? If a theme depends on one preprocessing choice, say so.

---

## Red-flag catalog (stop and investigate)

- A topic whose top words are function words, junk tokens, or one repeated boilerplate phrase.
- A classifier at **~100% accuracy** → leakage (an id, a template phrase, the label itself in the features).
- Accuracy that only matches the **base rate** dressed up as success.
- Sentiment/topic scores **correlated with document length** rather than content.
- Topics or classes that **change completely across seeds**.
- Covariate/prevalence effects **too large to be believable**.
- Findings that **vanish under a reasonable alternative preprocessing**.
- Two validated methods that **disagree**, reported as if they agreed.

When you hit one, name it, go back to the documents, and resolve or document it.

---

## What to write in the memo

At each phase, add a short **Plausibility Check** block:

```markdown
### Plausibility Check
- **Read the documents**: [what samples you read; did output match the text?]
- **Face validity**: [topics/classes/scores that hold up vs. don't]
- **Cross-method** (Phase 3–4): [do methods converge / partly agree / diverge? state it]
- **Red flags**: [none / list what was found and how resolved]
```
