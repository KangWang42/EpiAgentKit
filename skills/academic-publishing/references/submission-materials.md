# Submission Materials reference

> Cover Letter · Response to Reviewers · Highlights · Graphical Abstract · Title Page · Declarations ·
> Editorial and research correspondence.
> Prerequisite: a near-final manuscript with locked data. Author info / ethics / funding missing →
> `[NEED CONFIRMATION]`, never invent. Files go to `07_paper/submission/`.

## Contents
1. Cover Letter
2. Response to Reviewers / rebuttal
3. Highlights
4. Graphical Abstract (text spec)
5. Title Page & Declarations
6. Editorial and research correspondence
7. Pre-submission checklist

---

## 1 Cover Letter

Structure: Header (corresponding author affiliation) → Date → Salutation (editor name + journal) → Opening
(title, article type, target journal) → Background (~80–120 words: why the study) → Key findings →
Contribution (why it fits this journal) → Statements (originality, no concurrent submission, no conflict of
interest, ethics, all authors approved) → Closing → Corresponding author info.

Get the editor name from the journal's Editorial Board, not a guess. Keep background concise — do not
restate the abstract.

Templates:
```
Dear Dr. [Surname],

We are pleased to submit our manuscript entitled "[Title]" for consideration as a [Article Type] in
[Journal Name].

[Topic] has become an important issue because [reason]. Although previous studies have examined [known
evidence], limited evidence is available regarding [specific gap]. Understanding [specific issue] is
important for [clinical/public health/theoretical/policy relevance].

In this study, we found that [main finding 1]. We also observed that [main finding 2]. These findings
provide [type of evidence] and may help [implication]. We believe this work is well suited to [Journal
Name] because [fit].

This manuscript has not been published elsewhere and is not under consideration by any other journal. All
authors have approved the submission. The authors declare no conflicts of interest. [Ethics statement if
applicable.]

Thank you for considering our manuscript. We look forward to hearing from you.

Sincerely,
[Corresponding Author Name, affiliation, email]
```

Self-check: editor name from official Editorial Board; journal name & article type accurate; background
concise (not abstract redux); fit-to-journal stated; originality/no-concurrent/COI/ethics statements
present; corresponding author info complete.

---

## 2 Response to Reviewers / rebuttal

> Not in the source skills — added here. The single most outcome-determining material after the manuscript.

Principles:
- Open with a brief thank-you and a one-line summary of major changes.
- Answer **every** numbered point, in the reviewer's order. Never skip or merge silently.
- For each point: quote the comment → state the response → quote the exact revised text → give its location
  (page/line or section). Show the change, do not just assert it.
- Be courteous even when disagreeing; if declining a change, justify with evidence, not opinion.
- Keep the manuscript and the response consistent — every claimed change must actually exist in the revision.
- Build a response matrix before drafting: comment number · requested action · action taken · evidence/reason ·
  manuscript location · verification status. Do not write “we added/performed/revised” until the change is verified.
- Use a visible convention: reviewer comments in one style, responses in another (e.g. **R1.1**, *Response:*).

Layout:
```
We thank the reviewers for their constructive comments. We have revised the manuscript accordingly; the
main changes are: (1) … (2) … (3) …. Our point-by-point responses follow; reviewer comments are in bold and
revised text is shown in quotation marks with locations.

Reviewer 1

R1.1 [verbatim comment]
Response: [what we did / why]. We have revised the text (Section 3.2, p.7, lines 12–18) to read:
"[exact new wording]."

R1.2 …

Reviewer 2
…
```

Response functions:
- Agreement: We thank the reviewer for this suggestion and have [revised/added/clarified] accordingly.
- Clarification: We apologize for the lack of clarity. We have clarified that …
- Added analysis: As suggested, we performed [analysis]; the results (new Table S2) show …
- Respectful disagreement: We appreciate this point. However, [evidence-based reason]; we have nonetheless
  added a sentence acknowledging this in the Limitations (p.X).
- Out of scope: This is an important question but beyond the scope of the current study; we now note it as a
  direction for future work (p.X).

Self-check: every comment answered in order; each response cites exact revised wording + location; tone
courteous; declines are justified; manuscript and response are mutually consistent; new analyses are present
in the result source, tables/figures, manuscript, and response.

---

## 3 Highlights

3–5 bullet points, each ≤ ~85 characters (Elsevier convention; adjust to journal). Each captures one core
contribution — what was done and what was found, in plain declarative phrasing. No references, no
abbreviations on first sight, no over-claim.

```
- [Population/design] examined the association between [X] and [Y].
- [X] was associated with [direction/size of effect in Y].
- The association was [stronger/modified] in [subgroup].
- Findings support [implication], informing [policy/clinical use].
```

Self-check: 3–5 bullets; each ≤ char limit; each a distinct contribution; numbers match source; no hype.

---

## 4 Graphical Abstract (text spec)

This skill produces the **text/logic spec** for the graphical abstract; the complete non-statistical visual is
built via `research-visuals`, while any true data panel is first generated by `publication-figures` and supplied
as verified source content. Provide: one-line takeaway message; the exact visual flow (Population →
Exposure/Method → Key result → Implication); the 2–3 verified numbers to show; target-journal dimensions;
and a caption. Lock every label, number, node, and arrow before generation. Keep it self-explanatory and
consistent with the abstract's main result; if imagegen cannot preserve the exact content after Image 1
revision, applicable Image 2-assisted revision, and full-image regeneration, use `svg-diagrams` only as the
final whole-image fallback.

---

## 5 Title Page & Declarations

Title page items: see `english-writing.md` §2. Standard declaration blocks (fill from project; missing →
`[NEED CONFIRMATION]`):
- Ethics approval & consent: "The study was approved by [IRB/Ethics Committee], approval number [###].
  Informed consent was obtained from all participants."
- Conflict of interest: "The authors declare no conflicts of interest."
- Funding: "This work was supported by [funder], grant number [###]." / "This research received no specific
  grant."
- Data availability: "The data that support the findings are available from [source/on request]."
- Author contributions: per CRediT taxonomy (Conceptualization, Methodology, Formal analysis, Writing –
  original draft, etc.).
- Acknowledgements: non-author contributors.

---

## 6 Editorial and research correspondence

Use this mode for presubmission inquiries, extension requests, correction notices, withdrawal letters,
data or material requests, collaborator messages, and coauthor approval requests.

Structure: specific subject line → purpose in the first sentence → necessary facts and dates → requested
action → concise close. Include manuscript ID, short title, deadline, and attachment list when relevant.
Do not imply approval, attachment, analysis, or action that has not occurred.

- Extension: request a specific new date and give a brief truthful reason.
- Correction or withdrawal: separate the factual issue, its scope, its effect, and the action already taken.
- Data/material request: state intended use, requested scope, ethics or access conditions, and authorship terms.
- Coauthor approval: distinguish whether the message requests comments, formal approval, or acknowledgment.
- Presubmission inquiry: summarize fit and study contribution without reproducing the abstract or using hype.

Run the same fact lock as for the manuscript: names, dates, manuscript numbers, journal, files, results, and
promised actions must all be verifiable.

---

## 7 Pre-submission checklist (light)

Confirm against the journal's Guide for Authors before submitting:
- [ ] Manuscript matches Aim & Scope; journal has published comparable work
- [ ] Word/abstract/keyword limits met; reference style matches (journal EndNote/CSL style)
- [ ] All figures/tables cited in text; supplementary files named clearly
- [ ] Author info, ORCID, corresponding-author rules confirmed
- [ ] All required separate files prepared: main manuscript · title page · highlights · graphical abstract ·
  cover letter · figures · tables · supplementary · ethics/consent · COI · funding · data availability ·
  author contributions · (suggested reviewers if requested)
- [ ] Files are the final version; OA/APC terms confirmed
