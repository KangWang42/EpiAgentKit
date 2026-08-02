# English IMRaD Writing reference

> SKILL.md §二 的英文执行细节。各部件框架、写作流程与自检清单见本文件；使用 `english-phrasebank.md`
> 审查时态、衔接、hedging、论断强度和模板痕迹，不从中复制套句。数字按固定结果名称从 `results/results.yaml` 读取；旧项目可读取旧版结果文件，没有项目结果数据文件时使用用户明确指定且来源可核验的正式结果。润色或改写同时执行 `academic-humanizer` 的事实保护与论断依据检查。

## Contents
1. Manuscript spine and section purposes
2. Title
3. Abstract
4. Introduction
5. Literature review (synthesis, not list)
6. Aims / Significance / Scope
7. Methods (reproducible)
8. Results
9. Discussion
10. Conclusion
11. Per-section self-check checklists

---

## 1 Manuscript spine

Order in manuscript: Title → Abstract → Keywords → Introduction → Methods → Results → Discussion →
(Conclusion) → References → Tables/Figures → Supplementary → Declarations. (Cover letter is separate;
see `submission-materials.md`.)

When the venue uses IMRaD, each section answers one question:
- Introduction — **why** was the study done?
- Methods — **how** was it done?
- Results — **what** was found?
- Discussion — **what do the findings mean?**
- Conclusion — **what is the contribution and implication?**

**Writing order**: Results + Methods first, then Introduction + Discussion, then Abstract + Title + cover letter.

**Build an objective–method–result–discussion map before drafting.** Record each primary and secondary
question, its estimand or analytic target, the method that answers it, the corresponding table or figure,
the result, and the boundary on interpretation. Related results may share one literature comparison or
explanation; do not force every result to have a mechanism and significance sentence. Cross-check that the
Introduction's gap is answered by Methods and Results and that the Discussion returns to that gap.

Before revising existing prose, also build a fact lock containing every number, citation, equation,
table/figure reference, technical term, and claim direction. If the author supplies prior work, note their
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

## 4 Introduction

Use the moves that the evidence and venue require. They often progress from a concrete problem to the closest
evidence, a specific gap, and the study purpose, but they do not require four paragraphs or a fixed order:

1. **Context** — real-world/theoretical importance of the problem; why it matters now; add epidemiologic/
   policy/mechanistic background as needed.
2. **Review** — what prior studies found and showed; move from broad to closest-to-this-study. Synthesize,
   do not list paper-by-paper.
3. **Gap** — what is specifically missing and why this study is needed. The gap must directly lead to the aim.
4. **Purpose** — exactly what this study addresses and how it maps to the gap.

**Gap must be specific**, not "few studies." Name the gap type: population / exposure / outcome / method
(non-linearity, lag, interaction, causal inference) / mechanism / practice (policy or clinical decision).

Self-check: each paragraph serves the aim; gap is specific not vague; purpose
maps 1-to-1 to the gap; does not over-report results; `[ref]` placeholders mark needed citations.

---

## 5 Literature review (synthesis)

Not a pile of references — organize, evaluate, and lead to the gap. Build a literature matrix first
(topic/mechanism/variable · population/data · method · findings · strengths · limitations · relation to
this study). A paragraph may synthesize evidence, evaluate it, or establish a transition; do not require every
paragraph to perform all three moves in the same order.

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

Distinguish reproducible rationale from an analysis diary. Keep reasons that affect bias, interpretation, or
reproducibility, including participant exclusions, missing-data handling, variable construction, quality
control, protocol deviations, diagnostics that determine the reported estimate, and validation status. Remove
version history, abandoned trials, file paths, internal variable names, rendering details, and textbook
definitions of familiar methods. For a new or modified method, explain enough rationale and parameters for a
reviewer to assess it.

Self-check: design stated first; inclusion/exclusion clear; exposure & outcome definitions reproducible;
models map to the aim; analysis platform and significance level stated when required; reporting guideline followed; no
engineering noise (random seed, render engine, package build).

---

## 8 Results

Order results by objectives or estimands, time, or the actual analysis sequence. Report participant flow and
analysis sets before primary, secondary, sensitivity, and exploratory findings. Use prose, subheadings, or a
list only when the relationship among results supports that form.

Surface key estimates, denominators, time points, uncertainty, and model levels without rewriting every table
cell. Cite every table and figure in text. Related numbers may be reported together and interpreted once; do
not append a generic significance sentence to every value. Report null, uncertain, and discordant findings as
faithfully as positive findings.

Forbidden in Results: rewriting whole tables into prose; heavy literature citation; deep mechanism;
repeating Methods; reporting results unrelated to the aim.

Self-check: each subsection maps to a research question; every table/figure cited; key data highlighted not
exhaustively listed; no Discussion content; numbers/%/CI/P exactly match the tables and source.

---

## 9 Discussion

Select and order the moves needed to explain the most important findings: principal findings, comparison with
previous studies, interpretation or mechanisms, implications, strengths, limitations, applicability, and a
short close. The venue and argument decide how many paragraphs or subheadings are needed.

- Group findings that share evidence or an explanation; do not assign one subsection to every significant
  factor or repeat a fixed finding–comparison–mechanism–implication sequence.
- Compare populations, measurements, analyses, and estimates rather than writing only "consistent with."
- Offer a mechanism only when supported by data or literature; not every finding needs one.
- State limitations in terms of their effect on bias, precision, or applicability. Add mitigation only when it
  actually occurred, and do not force a fixed number of limitations.
- Make implications proportionate to design and uncertainty.

Self-check: returns to the Introduction's gap; explains each main finding; compares specifically with prior
work; avoids causal over-inference; limitations real/specific/explained; ending concise.

---

## 10 Conclusion (if a separate section)

Keep it concise and proportionate to the evidence. State what was found, where it applies, and the contribution
that follows. Do not force a positive close, a fixed number of findings, or a future-work sentence. Include a
material boundary when omitting it would change how readers interpret the conclusion or the venue requires it.

Forbidden: new results; large new literature; causal over-claim; repeating the abstract; data-unrelated
policy claims.

---

## 11 Per-section self-check (consolidated)

Run before marking any section complete:

| Section | Must pass |
|---------|-----------|
| Title | reflects design; no over-claim; meets journal title rules |
| Abstract | explicit objective; key numbers w/ CI/P; conclusion = results; within word limit |
| Introduction | specific gap; purpose maps to gap; no result leak; no fixed paragraph template |
| Methods | reproducible; models map to aim; analysis platform/α stated when required; guideline followed |
| Results | order matches objectives/estimands; tables/figures cited; numbers match source; no table-by-table rewrite |
| Discussion | returns to gap; related findings grouped; specific comparisons; limitations and implications proportionate |
| Conclusion | no new content; no over-claim; proportionate |

Cross-section coherence (whole-draft): sample size consistent everywhere; same number in Abstract = Results
= Discussion = tables = source; Introduction gap answered by Results; Discussion returns to Introduction;
tense usage per `english-phrasebank.md`.

After any edit, compare the revised section against the fact lock. A fluent rewrite that changes a number,
citation, equation, table/figure reference, claim direction, population, outcome, or time window fails review.
