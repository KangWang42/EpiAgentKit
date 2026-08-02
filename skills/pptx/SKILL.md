---
name: pptx
description: "Operate actual .pptx files: create, read, edit, render, validate, combine, split, or handle templates, layouts, notes and comments. For new or rebuilt decks, choose the SYSU official template, another institution or type, a user template, or a neutral design before creating slides. Use the relevant content workflow first, then add pptx only when a presentation file is an input or deliverable. Do not trigger for discussion of a talk without file work."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill

Start by applying the global `CLAUDE.md` scope entry: Q answer, L bounded artifact, P project execution, or R formal release. Loading this skill never expands that scope.

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |

---

## Template Routing Gate

Before creating or substantially rebuilding a presentation, determine the template source. If the user has not already specified it and no authoritative input presentation settles it, ask one concise question:

> 请确认模板来源：中大官方模板、其他学校/机构或特定汇报类型、您提供的模板，还是无模板的中性设计？

Do not ask again when the request, an attached `.pptx`, or the current project already identifies one authoritative template. If several plausible current templates exist and authority cannot be inferred, ask which one to use.

Route the answer as follows:

| Template source | Route |
|---|---|
| SYSU official | Load `sysu-ppt`, create through its official asset and toolkit workflow, then use this skill for file QA |
| Other school, institution, conference, or presentation type | Load any matching presentation-content workflow or reference, then use its supplied or project-authoritative `.pptx`; inspect it with [editing.md](editing.md) before writing content |
| User-provided template or reference deck | Treat that file as authoritative unless the user says it is inspiration only; preserve its masters, layouts, theme, branding, and fixed components |
| No template | Confirm the neutral route, then read [pptxgenjs.md](pptxgenjs.md) and create from scratch |

Do not invent an official logo, color system, master, or institutional identity when the named organization has not supplied a template. Ask for the file or offer a neutral design. Reading, extracting, or making a bounded edit to an existing presentation does not require this routing question because the existing file is already the source.

For every template-derived deck:

1. Inspect the template before drafting slides.
2. Use the template-editing workflow, not the from-scratch workflow.
3. Preserve required master/layout/theme relationships and brand assets while adapting content geometry for readability.
4. Verify in the rendered output that the intended template is visibly present and that no placeholder text remains.

---

## Output Version Hygiene

- In a formal project, keep one current presentation with a stable semantic filename and archive superseded source, output, renders and version-specific assets together under `09_backup/archive/`. Use `09_backup/workbench/` only for disposable render checks or isolated experiments.
- In a lightweight task, do not create project archives; preserve the user's original and write only to the requested output path.
- Make the generator write the stable current filename on every run. If two plausible current versions exist, ask the user which one is authoritative before archiving.

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for full details.**

Use when no template or reference presentation is available.

---

## Design Ideas

Let the content workflow, template, audience and display conditions determine the visual system. Use decoration only when it clarifies hierarchy or meaning.

### Before Starting

- **Choose a content-informed palette**: Preserve an existing template or brand system; otherwise use a restrained, readable palette suited to the topic and room conditions.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Contrast**: Meet readability needs at the actual display size; do not require dark title or conclusion slides.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

Use a chart, image, diagram, icon or shape only when it materially improves comprehension. A concise text slide is valid when the message is inherently verbal.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

Use the template's fonts or fonts already available in the environment. Prioritize glyph coverage, legibility and portability over novelty.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, report observed issues with their impact; do not invent defects to satisfy a checklist.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. List observed issues and their affected slides
3. Fix issues that violate the content, layout or rendering contract
4. Re-render and re-verify changed slides
5. If the first inspection passes, record that evidence without making a gratuitous edit

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Dependencies

- `markitdown[pptx]` in the user-selected Python environment for text extraction
- Pillow in the user-selected Python environment for thumbnail grids
- PptxGenJS in the user-selected Node.js environment for creating from scratch
- LibreOffice (`soffice`) - PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) - PDF to images

If any item is unavailable, explain the missing prerequisite and the user's next setup step; do not install or upgrade it.
