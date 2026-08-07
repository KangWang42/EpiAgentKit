# Scoped DOCX revision and validation

Use this reference when an existing DOCX is edited, repaired, reviewed, or used to derive clean and marked deliverables. The active content skill still owns factual, rhetorical, and scientific decisions.

## Revision record

For exact text changes in ordinary body paragraphs or table-cell paragraphs, use one UTF-8 JSON revision record only as deterministic tool input. Keep it in the task workbench unless it belongs to an already-required formal revision state; it is not a separate project record or deliverable. Each change needs a stable `id`, an exact locator, `old`, and `new`:

```json
{
  "schema_version": 1,
  "locked_decisions": {},
  "changes": [
    {
      "id": "change-1",
      "locator": {"kind": "paragraph", "para_id": "00A1B2C3", "index": 0},
      "old": "<exact existing text>",
      "new": "<verified replacement>"
    }
  ]
}
```

Use stable `w14:paraId` when present; an accompanying zero-based body `index` verifies that the intended paragraph has not drifted. If no paraId exists, use the index. Use `table-cell-paragraph` with zero-based `table`, `row`, `cell`, and `paragraph` indices for a table target. Carry `locked_decisions` forward only across formal rounds and pass `--previous-record`; changing a locked value requires a traceable `supersedes` entry.

## Same-source derivation

Run from the skill directory:

```bash
python scripts/revise_docx.py input.docx revision-record.json \
  --clean-out manuscript.docx --marked-out manuscript_marked.docx \
  --author Reviewer --highlight yellow --json
python scripts/compare_docx.py input.docx manuscript.docx \
  --mode scope --allow paragraph:0 --json
python scripts/compare_docx.py input.docx manuscript.docx \
  --mode scope --allow-insert-after paragraph:12 --json
python scripts/compare_docx.py manuscript.docx manuscript_marked.docx \
  --mode equivalence --json
```

The revision script refuses to overwrite outputs, requires a unique target in a simple Word run, preserves source run formatting, copies unchanged package parts from the source, and derives clean and tracked files from the same change list. The scope comparison treats all unlisted paragraphs, table cells, embedded media, global styles, numbering, settings, theme, and section layout as protected. Use `--allow table:N` only when the complete table is authorized, `--allow table-cell:T:R:C` for a cell, and `--allow-insert-after paragraph:N` only for a contiguous block inserted after that original body paragraph. A successful equivalence comparison proves final visible content and structure match; it does not replace rendering.

## Advanced OOXML boundary

Use manual structural OOXML editing only when the deterministic script correctly refuses fields, bookmarks, comments, pre-existing tracked changes, drawings, or complex mixed formatting. Record exact locators first, work in an isolated temporary directory, preserve relationship and content-type integrity, and never apply document-wide prose or style regular expressions.

## Required validation

Run every applicable layer; a file opening successfully is not sufficient.

1. Validate package structure and tracked-change integrity:

   ```bash
   python scripts/office/validate.py output.docx --original document.docx --author Reviewer
   ```

2. Compare the authorized scope and, when both files exist, clean/marked final-visible equivalence with `scripts/compare_docx.py`.
3. Audit relationships, fields, bookmarks, tracked changes, comments, hidden text, identifying properties, image pixels, embedded format, display size, and effective dpi:

   ```bash
   python scripts/audit_docx.py output.docx --json
   python scripts/audit_docx.py manuscript.docx --anonymous --json
   ```

   Anonymous submission mode treats tracked changes, comments, hidden text, and populated creator properties as blocking errors. The audit reports rule, evidence location, impact, and action. Static table, symbol, caption, and field findings remain inputs to visual review, not substitutes for it.
4. Extract body and table text and reconcile it with the revision record, facts, references, captions, and expected table/figure order.
5. Render the final file to PDF and page images using the existing LibreOffice and Poppler tools when available. For an L revision, inspect the page containing each authorized change and the adjacent pages where pagination can shift; compare the same locations before and after when the source can be rendered. Expand to all direct consumers of changed styles, numbering, section layout, headers/footers, table continuation, figures, fields, cross-references or the table of contents. Inspect every page only for a newly created or substantially rebuilt document, or when P/R delivery requires complete pagination review. At the applicable pages, check pagination, table borders and continuation, alignment, fonts, Times New Roman for English text and Latin statistical symbols, italic `t`/`F`/`z`/`r`/`R`, bold-italic `P`, upright effect-size abbreviations, statistical superscripts/subscripts, captions, cross-references, images, axes, legends, and clipping. If rendering is unavailable or times out, finish structural and reopen checks, disclose that pagination was not visually verified, and do not terminate any pre-existing user Word process.
6. Keep unpacked XML, PDFs, page images, and test copies in the isolated directory. Remove it only after securing final files and validation evidence.

For tables, first classify the target as an academic display table or an official form/review sheet. For academic display tables, inspect the OOXML for the top rule, header separator, bottom rule, white cells, header/numeric alignment, long-text top alignment, widths, pagination, notes, and content consistency; do not introduce a full grid or colored header. For official forms, preserve the approved complete borders, merged cells, blank fields, and shading. Workbooks used as evidence matrices follow the `xlsx` skill instead. For images, preserve verified statistical and source imagery, prefer vector input where supported, and judge label readability at actual displayed size. Never replace scientific result images with generated approximations.

When a revision touches numbered paragraphs, verify that each independent list block has an explicit numbering reference and that its visible first number is correct after rendering. A scope comparison must treat numbering definitions, table borders, image relationships, and section layout as protected unless the revision record authorizes them.
