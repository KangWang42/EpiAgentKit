# Scoped DOCX revision and validation

Use this reference when an existing DOCX is edited, repaired, reviewed, or used to derive clean and marked deliverables. The active content skill still owns factual, rhetorical, and scientific decisions.

## Revision record

For exact text changes in ordinary body paragraphs or table-cell paragraphs, create one UTF-8 JSON revision record. Each change needs a stable `id`, an exact locator, `old`, and `new`:

```json
{
  "schema_version": 1,
  "locked_decisions": {},
  "changes": [
    {
      "id": "change-1",
      "locator": {"kind": "paragraph", "index": 0},
      "old": "<exact existing text>",
      "new": "<verified replacement>"
    }
  ]
}
```

Use `table-cell-paragraph` with zero-based `table`, `row`, `cell`, and `paragraph` indices for a table target. Carry `locked_decisions` forward and pass `--previous-record` on later rounds; changing a locked value requires a traceable `supersedes` entry.

## Same-source derivation

Run from the skill directory:

```bash
python scripts/revise_docx.py input.docx revision-record.json \
  --clean-out manuscript.docx --marked-out manuscript_marked.docx \
  --author Reviewer --highlight yellow --json
python scripts/compare_docx.py input.docx manuscript.docx \
  --mode scope --allow paragraph:0 --json
python scripts/compare_docx.py manuscript.docx manuscript_marked.docx \
  --mode equivalence --json
```

The revision script refuses to overwrite outputs, requires a unique target in a simple Word run, preserves source run formatting, and derives clean and tracked files from the same change list. The scope comparison treats all unlisted paragraphs, table cells, embedded media, global styles, numbering, settings, theme, and section layout as protected. Use `--allow table:N` only when the complete table is authorized, or `--allow table-cell:T:R:C` for a cell. A successful equivalence comparison proves final visible content and structure match; it does not replace rendering.

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
5. Render the final file to PDF and page images using the existing LibreOffice and Poppler tools. Inspect every page at actual delivery size for pagination, table borders and continuation, alignment, fonts, statistical italics and super/subscripts, captions, cross-references, images, axes, legends, and clipping. Reopen the DOCX after rendering.
6. Keep unpacked XML, PDFs, page images, and test copies in the isolated directory. Remove it only after securing final files and validation evidence.

For tables, inspect structure, header hierarchy, borders, alignment, widths, pagination, notes, and content consistency together. For images, preserve verified statistical and source imagery, prefer vector input where supported, and judge label readability at actual displayed size. Never replace scientific result images with generated approximations.
