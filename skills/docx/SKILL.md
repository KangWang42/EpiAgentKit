---
name: docx
description: "Create, read, edit, render or validate Word .docx files, including layout, comments and tracked changes. Use when a Word file is an input or deliverable. Do not use for prose-only requests or other file formats."
license: Proprietary. LICENSE.txt has complete terms
---

# DOCX creation, editing, and analysis

A .docx file is a ZIP archive containing XML files.

Use the relevant paper or report content skill first; this skill handles file structure and display. Preserve the selected content source and layout master.

## Quick Reference

| Task | Approach |
|------|----------|
| Read/analyze content | `pandoc` or unpack for raw XML |
| Create new document | Use the content skill's established generator; otherwise use the compatible workflow below |
| Create from existing Word | Classify every input role → inherit the confirmed layout master → compare protected format properties |
| Edit existing document | Lock scope → derive clean/marked files from one exact revision record → compare scope and visible equivalence |

### Converting .doc to .docx

Legacy `.doc` files must be converted before editing:

```bash
python scripts/office/soffice.py --headless --convert-to docx document.doc
```

### Reading Content

```bash
# Text extraction with tracked changes
pandoc --track-changes=all document.docx -o output.md

# Raw XML access
python scripts/office/unpack.py document.docx unpacked/
```

### Converting to Images

```bash
python scripts/office/soffice.py --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

### Accepting Tracked Changes

To produce a clean document with all tracked changes accepted, use an already available compatible LibreOffice installation and an existing workbench directory:

```bash
python scripts/accept_changes.py input.docx output.docx --work-dir 09_backup/workbench/<batch>/runtime
```

The script keeps the input read-only, uses an isolated LibreOffice profile, verifies that tracked-change markup is gone, and writes the output only after success. Missing LibreOffice, timeout, residual tracked changes, or an existing output are failures; do not install a renderer or describe an unverified copy as a clean document.

---

## Classifying Existing Word Inputs

Before choosing the creation or editing path, classify every supplied Word file as a content source, layout master, both, or background-only reference. Read [layout-master inheritance](references/layout-master-inheritance.md) completely when an existing Word may govern a new or substantially rebuilt same-series document.

Classify an explicitly content-only file as a content source. Classify a same-study plan, report, or template as both content source and layout master when the user asks to generate or continue a document based on it. Choose the visual contract from the active content skill, project instructions, and confirmed layout master. If multiple plausible files or roles would produce materially different documents, stop and request the selection.

Use the new-document path when no layout master applies and follow the active content skill's format. Map substantive sections to the confirmed hierarchy; record every additional document component and visual property in the task's confirmed format contract.

## Creating New Documents

If no layout master applies and the active content skill or project provides a tested document generator, use it and apply this skill for validation and file QA. Otherwise inspect the existing environment and use an already available compatible generator; do not install one silently. When JavaScript `docx` is selected for a new or substantially rebuilt file, read [docx-js generation reference](references/docx-js-generation.md) completely. An existing `python-docx` or R `officer` environment may be used only if the generated package passes the same structural and page checks.

Generator-specific API names are not interchangeable. In `officer`, paragraph alignment uses `left`, `right`, `center`, or `justify`; do not pass Word UI labels such as `both`. With `python-docx`, pass image paths as strings for versions that do not accept `pathlib.Path`. Treat the first generated file as a compatibility check: run `scripts/office/validate.py`, and change the generator or correct the package when it fails rather than declaring the validator optional.

Pandoc 转换或回读成功不等于 Word 版式通过。Pandoc 可能保留参考文档的 `Hyperlink`、主题色或 `accent1` 样式；当内容 skill 已确认连续黑白版式时，必须在任务清单声明 `allowed_text_colors: ["000000"]`，并用 `scripts/audit_docx.py --requirements` 检查正文、题注、页眉页脚、表格文字和超链接文字的有效颜色。图像内部颜色不属于文字颜色审计。

For a new or substantially rebuilt Word file, a strict formatting task, or the first assembly of a complete formal document, read [delivery requirements](references/delivery-requirements.md) completely. For a bounded correction or regeneration, repeat only requirements that the current content, editing method, package parts, or page geometry could affect; an additional user correction does not by itself reopen the complete document checklist.

### Neutral Default Formatting

- Unless the user or an existing template specifies a visual theme, use a white page, black text, regular font sizes, and restrained borders. Build hierarchy with font size, weight, spacing, and alignment.
- Use white table cells throughout, including headers, first columns, and total rows; distinguish structure with font weight, alignment, spacing, and black or gray borders.
- When editing an established document or creating from a confirmed layout master, inherit its protected styles and layout.

### Validation
After creating the file, validate it. If validation fails, unpack, fix the XML, and repack.
```bash
python scripts/office/validate.py doc.docx
```

### Candidate-first delivery

When creating or regenerating a stable DOCX, write the output to an isolated workbench candidate first. Run package validation, the task-specific audit, content reconciliation, and any required page rendering against that candidate. Promote it only after all applicable checks pass, using a same-volume atomic replace such as `Report.promote_candidate()` from the report-writing helper. If the target is locked or replacement fails, keep the candidate, preserve the existing target, and stop with the target and candidate paths; do not force-close Word/LibreOffice or describe the candidate as the current delivery.

## Editing Existing Documents

Use the active content skill to decide whether the request is a local content revision, structural rewrite, format-only repair, final review, or reviewer-response closure. For academic texts, load `../academic-humanizer/references/revision-workflow.md` and lock the unique input, allowed and forbidden scope, facts, user corrections, and target output before touching the package. An answer-only request creates no file. A single local DOCX change does not require a project `revision-state.json`, clean/marked/response set, archive sweep, or full-project audit; use those only when the revision workflow actually requires them.

For an exact body or table-cell text change, clean/marked deliverables, comments or tracked changes, read `references/scoped-revision.md` completely for the revision record, deterministic derivation and applicable validation. A format-only edit, image replacement or other package operation does not load the text-revision schema unless it also changes ordinary text. Separate content changes from format changes and validate them independently. Do not use fuzzy full-document replacement. If an exact target is absent, repeated, inside a field or drawing, or spans incompatible run structure, stop and report candidate locations.

Use `scripts/revise_docx.py` first for exact text changes in ordinary body or table-cell paragraphs. It copies every unchanged ZIP part from the source package and replaces only `word/document.xml`, so do not add a second unpack-and-repack helper for ordinary scoped edits. Prefer a stable `w14:paraId` locator when available and retain an index only as a cross-check. Then use `scripts/compare_docx.py` for authorized-scope and clean/marked visible-equivalence checks; explicitly authorize limited paragraph insertion with `--allow-insert-after`. Run `scripts/audit_docx.py` only when the current change can affect relationships, fields, comments or tracked changes, hidden or identifying content, images, captions, styles or task-specific requirements that it checks; do not run a full static audit for an ordinary exact text replacement already covered by package validation and scope comparison. Carry locked decisions across formal rounds; changing one requires an explicit superseding record.

### Advanced OOXML editing

For fields, bookmarks, comments, pre-existing tracked changes, drawings or complex mixed formatting that the deterministic revision script correctly refuses, read [OOXML editing reference](references/ooxml-editing.md) completely. It contains the isolated unpack/edit/pack commands and XML invariants. Do not use this path for an ordinary supported replacement.

Use the user or workflow's author name; otherwise use the neutral value `Reviewer` and disclose the choice.

### Scope-based validation after any edit

Choose the applicable checks in `references/scoped-revision.md` from the authorized change and the document problems it could cause: package validation, authorized-scope comparison, clean/marked equivalence, structural or anonymity audit, content reconciliation, page inspection, and final reopen. For repeated L edits, repeat a check only when the source file, editing method, or document content examined by that check has changed. Regenerating one target does not invalidate unrelated successful checks. A file opening successfully is not sufficient. Keep intermediate XML, renderings, and test copies outside the active delivery directory.

Decide first whether the change can affect pagination or page display. Do not probe LibreOffice for an ordinary L edit with no page risk. When page inspection is required, use LibreOffice if the executable has already been found or a one-time lightweight capability check succeeds. Do not use hidden Word COM automation as an automatic fallback: it can load the user's add-ins, reuse an existing Office session or wait on an invisible dialog. If any Word process is already running, do not start COM automation because a new application object does not guarantee process isolation; ask the user to save and close Word or use another renderer. Word-native rendering is allowed only when the user requests it, no Word process is running beforehand, the new process ID is recorded, and a timeout can close only that process. If required rendering remains unavailable or times out, complete the applicable static and reopen checks, state explicitly which pagination and final-display properties were not verified, and do not launch or terminate an existing user Word process. Do not claim a structural-only check is equivalent to page inspection.

## Dependencies

- **pandoc**: Text extraction
- **docx**: JavaScript package for new documents; if unavailable, report it as a prerequisite without installing it
- **LibreOffice**: PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- **Poppler**: `pdftoppm` for images
