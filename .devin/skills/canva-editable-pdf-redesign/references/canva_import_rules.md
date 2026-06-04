# Canva Import Rules — how the parser sees your PDF

Canva's PDF importer reconstructs an editable design by detecting three kinds of objects:

1. **Native text runs** → become editable **text boxes**.
2. **Vector paths/shapes** (lines, rects, circles, beziers, fills) → become editable **elements**.
3. **Embedded image binaries** (PNG/JPEG) → become editable **images**.

Anything that is *rasterized* (drawn as pixels) is imported as a flat, **locked** image.
So the entire job is: emit the design as text + vector + discrete images, never as a
single baked picture.

## DO
- Write text with real text operators (ReportLab `drawString`/`drawCentredString`/`Paragraph`,
  or jsPDF `doc.text`). Keep each logical block as its own run.
- Use **standard font families** Canva can match on the fly: Helvetica/Arial,
  Times New Roman, Georgia, Courier. (ReportLab built-ins: `Helvetica*`, `Times-*`, `Courier`.)
- Lay out elements in **clean, sequential, absolute coordinates**.
- Embed images as **separate** PNGs with real transparency (alpha), placed individually.
- Use **solid color or vector** backgrounds.
- Set text alignment explicitly (left/center/right) so edits keep the intended layout.

## DON'T
- ❌ Flatten the page (or big regions) into one PNG/JPEG. This is the cardinal sin.
- ❌ **Overlap two text elements in the same space.** Canva imports them as separate boxes
  that collide and fragment the words. (Real failure seen: a faint decorative number placed
  behind a centered title made "SOINS SANS RINÇAGE" import as `1ANS RINÇAGE` + `SOINS S`.)
  Keep decorative text spatially separated from real text, or make the decoration a vector/image.
- ❌ Use heavily nested group transforms / matrix transforms — parsers frequently drop or
  misplace them. Prefer flat, pre-computed coordinates.
- ❌ Rely on exotic embedded fonts. If a specific look matters, the user re-applies a font in Canva.
- ❌ Bake captions/labels into image crops. Crop tighter; keep text as text.

## Verifying editability before you ship
- `pypdf` → `PdfReader(out).pages[i].extract_text()` must return the actual words for **every**
  page. Empty/garbled = your "text" is secretly an image. Fix it.
- Open the render and confirm: titles are crisp vector glyphs (not fuzzy pixels), images sit
  on the page background cleanly, no two text blocks share the same rectangle.

## ReportLab vs jsPDF (pick by toolchain)
Both satisfy the rules; they produce native text + vector + embedded images.

- **ReportLab (Python)** — recommended in a Python sandbox. Stable, no DOM needed, great text
  and vector support, transparency via `setFillAlpha`. Built-in fonts cover French accents
  (WinAnsi). This skill's `design_kit.py` is ReportLab.

- **jsPDF (JS/Node/Vite)** — use if the project is web/Node. Notes that bite people:
  - `new jsPDF({unit:"px", format:[w,h]})` and write text with `doc.text(s, x, y, {align})`.
  - For images, rasterize SVG/remote images to PNG via a **canvas** first; in a browser/SPA use
    `new window.Image()` (NOT `new Image()` in abstract modules) and set
    `img.crossOrigin = "anonymous"` before `img.src` to avoid canvas taint.
  - Draw shapes with explicit bounds (`doc.roundedRect`, `doc.ellipse`, `doc.line`); avoid
    relying on nested `<g transform="matrix(...)">` which Canva may drop.
  - Same golden rules apply: native text, standard fonts, no flattening, no overlapping text.

The choice of library never changes the principles — only the syntax.
