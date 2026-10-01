# Editing Presentations

## Choose the editing scope

For an L bounded edit, use the existing presentation as the authoritative source without remapping the deck:

1. Lock the input file, target slide numbers or stable slide relationships, exact elements, allowed package parts and protected scope.
2. Inspect only the target slides and the masters/layouts they already consume; unpack the source and edit only the authorized slide XML, relationships, notes or media.
3. Pack with the original presentation as the source, validate the package, and confirm slide order/count, masters, layouts, theme and all unauthorized parts remain unchanged.
4. Extract and reconcile the changed text, then render the changed slides and adjacent slides only when pagination-like continuity, transitions or a shared visual edge can be affected.
5. If the change touches a master, layout, theme, font, shared asset, slide order/count or deck-wide setting, upgrade to P and inspect the slides that actually use the changed item; R performs complete presentation QA.

Do not run template selection, slide mapping, placeholder replacement across all slides or deck-wide style cleanup for an L edit.

## Template-Based Workflow

When using an existing presentation as a template:

1. **Analyze existing slides**:
   ```bash
   python scripts/thumbnail.py template.pptx
   python -m markitdown template.pptx
   ```
   Review `thumbnails.jpg` to see layouts, and markitdown output to see placeholder text.

2. **Plan slide mapping**: For each content section, choose the template layout that fits the slide's function in the storyboard from the content workflow (for example, a title-and-text layout for an argument, a figure layout for a result figure, a two-column layout only for a real side-by-side comparison).

   Do not add layout variety for its own sake. Stat callouts, icon grids, card walls and decorative quote slides are used only when the template fixes them or the content workflow asks for them; a plain text slide is often the correct choice for research content.

3. **Unpack**: `python scripts/office/unpack.py template.pptx unpacked/`

4. **Build presentation** (structural changes in one pass, not split across parallel workers):
   - Delete unwanted slides (remove from `<p:sldIdLst>`)
   - Duplicate slides you want to reuse (`add_slide.py`)
   - Reorder slides in `<p:sldIdLst>`
   - **Complete all structural changes before step 5**

5. **Edit content**: Update text in each `slide{N}.xml`. Slides are separate XML files, so parallel workers may edit different slides if the client supports them.

6. **Clean**: `python scripts/clean.py unpacked/`

7. **Pack**: `python scripts/office/pack.py unpacked/ output.pptx --original template.pptx`

---

## Scripts

| Script | Purpose |
|--------|---------|
| `unpack.py` | Extract and pretty-print PPTX |
| `add_slide.py` | Duplicate slide or create from layout |
| `clean.py` | Remove orphaned files |
| `pack.py` | Repack with validation |
| `thumbnail.py` | Create visual grid of slides |

### unpack.py

```bash
python scripts/office/unpack.py input.pptx unpacked/
```

Extracts PPTX, pretty-prints XML, escapes smart quotes.

### add_slide.py

```bash
python scripts/add_slide.py unpacked/ slide2.xml      # Duplicate slide
python scripts/add_slide.py unpacked/ slideLayout2.xml # From layout
```

Prints `<p:sldId>` to add to `<p:sldIdLst>` at desired position.

### clean.py

```bash
python scripts/clean.py unpacked/
```

Removes slides not in `<p:sldIdLst>`, unreferenced media, orphaned rels.

### pack.py

```bash
python scripts/office/pack.py unpacked/ output.pptx --original input.pptx
```

Validates, repairs, condenses XML, re-encodes smart quotes.

### thumbnail.py

```bash
python scripts/thumbnail.py input.pptx [output_prefix] [--cols N]
```

Creates `thumbnails.jpg` with slide filenames as labels. Default 3 columns, max 12 per grid.

**Use for template analysis only** (choosing layouts). For visual QA, render full-resolution individual slides with the renderer in SKILL.md section 3.

---

## Slide Operations

Slide order is in `ppt/presentation.xml` → `<p:sldIdLst>`.

**Reorder**: Rearrange `<p:sldId>` elements.

**Delete**: Remove `<p:sldId>`, then run `clean.py`.

**Add**: Use `add_slide.py`. Never manually copy slide files—the script handles notes references, Content_Types.xml, and relationship IDs that manual copying misses.

---

## Editing Content

**Parallel workers:** If the client supports them, they may edit different slides after step 4. Give each worker the slide file path(s), the instruction to make targeted text edits, and the formatting rules and pitfalls below.

For each slide:
1. Read the slide's XML
2. Identify ALL placeholder content—text, images, charts, icons, captions
3. Replace each placeholder with final content

**Make targeted text edits** with the client's file-edit tool (for example Edit in Claude Code or apply_patch in Codex), not bulk sed or ad-hoc Python rewrites. Targeted edits force specificity about what to replace and where.

### Formatting Rules

- **Keep heading emphasis from the template**: slide titles and in-slide section headers keep the template's weight (`b="1"` on `<a:rPr>` only when the template or content workflow uses bold headers). Do not turn prose into "Label: text" lines just to create bold labels.
- **Never use unicode bullets (•)**: Use proper list formatting with `<a:buChar>` or `<a:buAutoNum>`
- **Bullet consistency**: Let bullets inherit from the layout. Only specify `<a:buChar>` or `<a:buNone>`.

---

## Common Pitfalls

### Template Adaptation

When source content has fewer items than the template:
- **Remove excess elements entirely** (images, shapes, text boxes), don't just clear text
- Check for orphaned visuals after clearing text content
- Run visual QA to catch mismatched counts

When replacing text with different length content:
- **Shorter replacements**: Usually safe
- **Longer replacements**: May overflow or wrap unexpectedly
- Test with visual QA after text changes
- Consider truncating or splitting content to fit the template's design constraints

**Template slots ≠ Source items**: If template has 4 team members but source has 3 users, delete the 4th member's entire group (image + text boxes), not just the text.

### Multi-Item Content

If source has multiple items (numbered lists, multiple sections), create separate `<a:p>` elements for each — **never concatenate into one string**.

**❌ WRONG** — all items in one paragraph:
```xml
<a:p>
  <a:r><a:rPr .../><a:t>Step 1: Do the first thing. Step 2: Do the second thing.</a:t></a:r>
</a:p>
```

**✅ CORRECT** — separate paragraphs (headers keep the template's emphasis):
```xml
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" b="1" .../><a:t>Step 1</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" .../><a:t>Do the first thing.</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" b="1" .../><a:t>Step 2</a:t></a:r>
</a:p>
<!-- continue pattern -->
```

Copy `<a:pPr>` from the original paragraph to preserve line spacing.

### Smart Quotes

Handled automatically by unpack/pack. Text edit tools may convert smart quotes to ASCII.

**When adding new text with quotes, use XML entities:**

```xml
<a:t>the &#x201C;Agreement&#x201D;</a:t>
```

| Character | Name | Unicode | XML Entity |
|-----------|------|---------|------------|
| `“` | Left double quote | U+201C | `&#x201C;` |
| `”` | Right double quote | U+201D | `&#x201D;` |
| `‘` | Left single quote | U+2018 | `&#x2018;` |
| `’` | Right single quote | U+2019 | `&#x2019;` |

### Other

- **Whitespace**: Use `xml:space="preserve"` on `<a:t>` with leading/trailing spaces
- **XML parsing**: Use `defusedxml.minidom`, not `xml.etree.ElementTree` (corrupts namespaces)
