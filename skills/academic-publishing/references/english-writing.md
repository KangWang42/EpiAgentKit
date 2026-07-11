# English IMRaD Writing reference

> SKILL.md §二 的英文执行细节。各部件框架 + 写作流程 + 自检清单。句式从 `english-phrasebank.md` 取；
> 时态/hedging/over-claim 规范同样在 phrasebank。数据一律取自 `07_paper/results.yaml` 及其派生
> `0_result_summaries.md`。润色或改写同时执行 `academic-humanizer` 的事实锁与论断—证据检查。

## Contents
1. IMRaD skeleton + section purposes + result-interpretation-contribution map
2. Title
3. Abstract
4. Introduction (CRGP)
5. Literature review (synthesis, not list)
6. Aims / Significance / Scope
7. Methods (reproducible)
8. Results (LOC–KD–COM)
9. Discussion (7-part)
10. Conclusion
11. Per-section self-check checklists

---

## 1 IMRaD skeleton

Order in manuscript: Title → Abstract → Keywords → Introduction → Methods → Results → Discussion →
(Conclusion) → References → Tables/Figures → Supplementary → Declarations. (Cover letter is separate;
see `submission-materials.md`.)

Each section answers one question:
- Introduction — **why** was the study done?
- Methods — **how** was it done?
- Results — **what** was found?
- Discussion — **what do the findings mean?**
- Conclusion — **what is the contribution and implication?**

**Writing order**: Results + Methods first, then Introduction + Discussion, then Abstract + Title + cover letter.

**Build a result–interpretation–contribution map before Discussion.** For each of 3–5 key results, fix:
(a) one interpretation/mechanism point, (b) one literature comparison point, (c) one significance point.
The Discussion must use this map. Cross-check coherence: the Introduction's gap must be answered by
Methods+Results, and the Discussion must return to the Introduction's gap.

Before revising existing prose, also build a fact lock containing every number, citation, equation,
table/figure pointer, technical term, and claim direction. If the author supplies prior work, note their
sentence rhythm, preferred subjects, connective habits, and placement of hedging. Preserve these unless
they impair clarity or accuracy.

---

## 2 Title

Include: study population/object · core exposure/intervention/method · core outcome · design/data source
(when informative). Common patterns:
- `Association between X and Y among Z: a cohort study`
- `Effects of X on Y: evidence from [data source]`
- `X and risk of Y: a population-based study`
- `Interactive effects of X and Y on Z`

Title page items (per journal): Full title · Running title · Authors · Affiliations · Corresponding
author · Author contributions · Word count · No. of tables/figures · Funding · Conflicts of interest ·
Ethics approval · Data availability · Acknowledgements. Missing author info → `[NEED CONFIRMATION]`.

Self-check: not too long; no unnecessary abbreviations; accurately reflects design; no causal over-claim;
matches journal capitalization/word/running-title rules.

---

## 3 Abstract

**Write last.** Structured (Background/Objective/Methods/Results/Conclusions) or unstructured per journal;
unstructured must still imply all five. Pull 1 background + 1 objective sentence from Introduction; design/
population/data/model from Methods; the 2–4 most important results; 1 interpretation/significance sentence.
Compress strictly to the journal word limit.

Self-check: contains explicit objective; methods specific enough; results carry key numbers (with CI/P);
conclusion consistent with results; obeys word limit and structure; keywords cover exposure, outcome,
design, and discipline.

---

## 4 Introduction — CRGP

Four moves, general → specific, every sentence serving the final aim:

1. **Context** — real-world/theoretical importance of the problem; why it matters now; add epidemiologic/
   policy/mechanistic background as needed.
2. **Review** — what prior studies found and showed; move from broad to closest-to-this-study. Synthesize,
   do not list paper-by-paper.
3. **Gap** — what is specifically missing and why this study is needed. The gap must directly lead to the aim.
4. **Purpose** — exactly what this study addresses; directly answers the gap.

**Gap must be specific**, not "few studies." Name the gap type: population / exposure / outcome / method
(non-linearity, lag, interaction, causal inference) / mechanism / practice (policy or clinical decision).

Self-check: funnels general→specific; every paragraph serves the aim; gap is specific not vague; purpose
maps 1-to-1 to the gap; does not over-report results; `[ref]` placeholders mark needed citations.

---

## 5 Literature review (synthesis)

Not a pile of references — organize, evaluate, and lead to the gap. Build a literature matrix first
(topic/mechanism/variable · population/data · method · findings · strengths · limitations · relation to
this study). Each paragraph: topic sentence → evidence synthesis → critical evaluation → gap/transition.

Three evaluation moves: positive (affirm contribution), negative (point out limitation), neutral (inference
or unresolved question). Only turn into a **specific gap** the limitations this study actually addresses;
general limitations of the field are not the gap.

Self-check: avoids paper-by-paper narration; groups similar studies; evaluates rather than only describes;
states why this study is necessary; ends with a bridge to the Aim.

---

## 6 Aims / Significance / Scope

**Aim** — lead with *what*, then *how*. Prefer `This study aimed to examine the association between X and Y
using Z data.` Avoid putting the method first (`Using a large dataset, this study aimed…`) unless the method
is the paper's contribution. Separate primary and secondary objectives.

**Significance** — a *predictive* contribution, stated cautiously (may/could). Goes at the end of the
Introduction or in Discussion/Conclusion. Do not state unproven results as fact.

**Scope** — study boundaries: what is included, what is excluded, why, and whether it limits interpretation.
Keep scope distinct from limitation (scope = deliberate boundary; limitation = shortcoming).

Self-check: aim specific to variable/object/outcome/method; significance uses hedging; scope states
boundaries clearly and is distinguished from limitations.

---

## 7 Methods (reproducible)

Structure: Study design and setting → Data source/participants/samples → Exposure/intervention/predictors →
Outcome definition → Covariates → Statistical analysis / experimental procedure → Sensitivity/subgroup
analyses → Ethical approval → Software.

Principles: follow the actual workflow; past tense for completed actions; define variables precisely;
statistical methods must map to the research question; do **not** interpret results here; report the
relevant reporting guideline (STROBE / CONSORT / PRISMA …).

**State what was done, not why/how it was decided** (the most common failure). Methods is not an analysis
diary or a justification of choices. Cut these four to a half-clause or delete: (1) motivation/justification
("to avoid collinearity…", "because the distribution was skewed…", "given that…"); (2) exclusion reasoning
("variable X was not included because it was unrelated…" → just state how X was handled); (3) pre-analysis
process / data-quality checks / diagnostics narration ("before analysis we checked completeness/missingness",
"we ran VIF/Shapiro/Cook…") — keep a diagnostic only when it determines which estimate is reported (e.g.
"because heteroscedasticity was detected, CIs are bootstrap-based"); (4) textbook definitions of a method
("MCA is a dimension-reduction technique that projects categories into a low-dimensional space…") → "we
applied MCA to the 12 categorical variables and retained the first three dimensions (44.0% of inertia)."
Signal that you drifted: "because / in order to / given / since / is a method that / before analysis we
checked." Build a composite the right way: "items A, B, C were summed into an accessibility score (0–6,
Cronbach α=0.75)" — not why it was not dichotomized, not why X was excluded, not what was checked first.

Self-check: design stated first; inclusion/exclusion clear; exposure & outcome definitions reproducible;
models map to the aim; analysis platform and significance level stated when required; reporting guideline followed; no
engineering noise (random seed, render engine, package build).

---

## 8 Results — LOC–KD–COM

1. **LOC** (locate) — point the reader to the table/figure.
2. **KD** (key data) — surface only the important numbers, not every cell.
3. **COM** (comment) — brief necessary interpretation/comparison, without drifting into Discussion.

Report only: highest/lowest values · overall trend · key comparisons · outliers · results tied to the
hypothesis · results supporting the main conclusion. One subsection per research question. Every table/
figure must be cited in text; key tables/figures must be embedded in text (not "see Table N" with no data).

Forbidden in Results: rewriting whole tables into prose; heavy literature citation; deep mechanism;
repeating Methods; reporting results unrelated to the aim.

Self-check: each subsection maps to a research question; every table/figure cited; key data highlighted not
exhaustively listed; no Discussion content; numbers/%/CI/P exactly match the tables and source.

---

## 9 Discussion (7-part)

1. **Principal findings** — open by summarizing 2–4 main findings; do not repeat all numbers.
2. **Comparison with previous studies** — state consistent or inconsistent, and explain why (population,
   exposure assessment, model specification…). Not just "consistent."
3. **Interpretation / mechanisms** — cautious, not asserted as fact.
4. **Strengths** — concrete (large sample, prospective design, high-quality data, repeated measures, robust
   sensitivity analyses, novel exposure/outcome/interaction, policy/clinical relevance), no empty praise.
5. **Limitations** — each = what the limitation is + why it exists + its effect on interpretation / how to
   handle it.
6. **Implications** — proportionate to the strength of evidence; no over-claim.
7. **Conclusion** — short close.

Self-check: returns to the Introduction's gap; explains each main finding; compares specifically with prior
work; avoids causal over-inference; limitations real/specific/explained; ending concise.

---

## 10 Conclusion (if a separate section)

Short, contribution-oriented, no over-claim. A short paper usually needs one paragraph: what was found,
what it suggests, and the evidence-proportionate contribution. Do not add a new limitation or future-work
sentence merely to complete a template; place limitations in the Discussion unless the venue requires otherwise.

Forbidden: new results; large new literature; causal over-claim; repeating the abstract; data-unrelated
policy claims.

---

## 11 Per-section self-check (consolidated)

Run before marking any section complete:

| Section | Must pass |
|---------|-----------|
| Title | reflects design; no over-claim; meets journal title rules |
| Abstract | explicit objective; key numbers w/ CI/P; conclusion = results; within word limit |
| Introduction | general→specific; specific gap; purpose maps to gap; no result leak |
| Methods | reproducible; models map to aim; analysis platform/α stated when required; guideline followed |
| Results | per-question subsections; tables/figures cited & embedded; numbers match source; no interpretation |
| Discussion | returns to gap; each finding explained; specific comparison; limitations w/ 3 elements |
| Conclusion | no new content; no over-claim; proportionate |

Cross-section coherence (whole-draft): sample size consistent everywhere; same number in Abstract = Results
= Discussion = tables = source; Introduction gap answered by Results; Discussion returns to Introduction;
tense usage per `english-phrasebank.md`.

After any edit, compare the revised section against the fact lock. A fluent rewrite that changes a number,
citation, equation, table/figure pointer, claim direction, population, outcome, or time window fails review.
