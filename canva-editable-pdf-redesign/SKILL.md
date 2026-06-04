---
name: canva-editable-pdf-redesign
description: >
  Recreate a PDF (especially a flattened design e-book, recipe book, brochure, or
  Canva export) into a NEW PDF that imports into Canva as fully EDITABLE, layered
  elements — native text boxes, separate transparent image layers, and vector
  graphics — while improving the visual design. Use this skill whenever the user
  wants to "make a PDF editable in Canva", "import a PDF into Canva", "redesign /
  improve / beautify a PDF", "convert a flattened PDF to editable", "recreate these
  pages", "transform this image/PDF to Canva", or hands over a PDF/PNG of designed
  pages and asks for an editable or better-looking version — even if they don't say
  the word "Canva". Also use it when only part of a document (a page range) needs
  redesigning. It covers analysis, text reconstruction, image keying/extraction,
  a ReportLab design framework, design enrichment, and Canva-import pitfalls.
---

# Canva-Editable PDF Redesign

## What this skill does

Takes a source PDF (or page images) — typically a **flattened design** where every
page is one baked image with no editable layers — and produces a **new PDF** that:

1. Has **native, selectable text** (so Canva imports each block as an editable text box).
2. Uses **separate, background-removed (transparent) images** as movable layers.
3. Uses **vector graphics** (shapes, icons, cards, decorations) instead of baked pixels.
4. Optionally **improves the design** (richer layout, more imagery, more in-context text).

The output is a standard PDF. When dragged into Canva ("Import" / "Create design from
file"), each text run becomes an editable text box, each image an editable image, each
shape an editable element. **That is the whole point — never flatten.**

## The Golden Rules (non-negotiable for Canva editability)

These come directly from how Canva's importer parses PDFs. Violating any of them
produces a "locked"/garbled result.

1. **NEVER flatten.** Do not render the page (or large regions) to a single PNG/JPEG and
   drop it into the PDF. Text-as-image is not editable. Reconstruct text as real text.
2. **Native text only.** Generate text with a PDF library that writes true text operators
   (ReportLab `drawString`/`Paragraph`). Verify with `pypdf` `extract_text()` afterwards.
3. **Standard, web-safe fonts** so Canva can match/substitute them: Helvetica(/-Bold/
   -Oblique/-BoldOblique), Times-Roman(/-Bold/-Italic/-BoldItalic), Courier. Avoid exotic
   embedded fonts; the user can swap to a fancy font inside Canva in two clicks.
4. **No overlapping text boxes.** See the #1 pitfall below — this is the single most
   common failure.
5. **Images as separate transparent layers**, not glued into the background.
6. **Backgrounds are solid color or vector**, never a flat photo with text baked on it.
7. **One element = one layer, laid out in clean sequential coordinates.** Avoid nested
   group transforms.

## ⚠️ Critical errors to avoid (learned the hard way)

- **Overlapping text elements break Canva import.** If you place a big decorative number
  (e.g. a faint "3") *behind* a centered title at the same coordinates, the PDF *looks*
  fine, but Canva imports them as two separate text boxes occupying the same space and
  **fragments the words** (e.g. "SOINS SANS RINÇAGE" rendered as `1ANS RINÇAGE` / `SOINS S`).
  **FIX:** never let two text elements overlap. Separate them spatially — put the big
  number *above* the title with a clear gap, or make the number a vector/image element
  instead of text. This applies to any decorative-text-behind-text design.
- **Baked-in text inside cropped images.** When you crop an ingredient/photo from a
  flattened source page, the crop often catches adjacent caption text. Always crop tighter
  and **verify on a contact sheet** before placing. A stray glyph in a "transparent" image
  is a dead giveaway of a sloppy crop.
- **Content overflowing past the footer** on dense pages. Long recipes/paragraphs push
  past the page bottom. Parametrize font size / leading / section gaps per page, or flow
  with a y-cursor and compact the heavy pages. Always render and check.
- **Keying out white that is part of the subject.** A global "make light pixels
  transparent" erases white rice inside a bowl, foam, etc. Use **border flood-fill**
  keying (only background connected to the edges is removed) — interior whites survive.
- **Trying to faithfully reproduce a photographic background.** You cannot have it both
  faithful *and* editable; a flat photo is the opposite of editable. Use a sampled solid
  tint or soft vector blobs, and tell the user they can re-add the photo in Canva.
- **Assuming you can download arbitrary web images.** The sandbox network is usually
  locked to package registries. `image_search` finds images but you often can't fetch
  them. **Prefer extracting imagery from the source PDF itself**, or reuse a clipart
  library you already have. Don't promise web downloads you can't deliver.

## Environment & dependencies

```bash
pip install pymupdf reportlab pdf2image pillow scipy pypdf --break-system-packages
```
- `pymupdf` (`import fitz`) — inspect + rasterize the source.
- `reportlab` — build the native-text output PDF.
- `pdf2image` (`convert_from_path`) — render the result for visual QA (needs poppler).
- `pillow` + `scipy` — crop, key out backgrounds, extract assets.
- `pypdf` — confirm the output text is selectable.

Work in `/home/claude/...` for scratch; copy the final deliverable to
`/mnt/user-data/outputs/`; inputs are in `/mnt/user-data/uploads/`. Use `present_files`
to share the result.

## Workflow

Follow these phases in order. The bundled scripts handle the mechanical parts; read the
references for deep code.

### Phase 0 — Inspect the source
Run `scripts/inspect_pdf.py <input.pdf>`. It reports page count, page sizes, and
**images-per-page**. **If every page has exactly 1 image, the source is fully flattened**
(text is baked in) — the common case. Note the page size (usually A4 595×842 pt) and
rasterize the pages you need at 200 DPI (A4@200dpi = 1654×2340 px) for cropping.

### Phase 1 — Capture the text
Read the source pages (they are usually visible to you as document images in context, or
rasterize + OCR-by-eye). **Transcribe every page's text faithfully**, preserving the
author's wording, accents, and even their typos unless asked to fix them. Organize it as
structured data (per page: title, metadata, ingredient/bullet lists, paragraphs, etc.).

### Phase 2 — Extract and key out images
The source's own photos are your best, most on-brand image source. Use
`scripts/keyout.py`:
- `crop_keyout` — crop a region (by pixel or fractional box) and flood-fill out the light
  background to transparency.
- `extract_assets` — for a clean "library" page (objects on white), auto-segment every
  object via connected components (dilate to merge parts), crop, key, and dump a labeled
  contact sheet so you can identify each asset.
Always build a **contact sheet** and eyeball the crops; re-crop anything that caught text
or has halos. See `references/lessons_and_pitfalls.md` for threshold tuning.

### Phase 3 — Rebuild the text natively (ReportLab)
This is the core. Use the helpers in `scripts/design_kit.py` (import or copy them):
- A top-origin coordinate helper `T(y) = page_height - y` (ReportLab origin is bottom-left;
  top-origin is far easier to reason about).
- Title / section-header / wrapped-paragraph / bullet / centered-line helpers.
- Place keyed images with `drawImage(..., mask='auto')`.
Build a **reusable page template** and feed it your structured text. Match the source's
palette (sample colors from the raster). Keep the design system consistent across pages.
See `references/reportlab_cookbook.md`.

### Phase 4 — Enrich the design (when asked to improve it)
To "fill the page" and make it expressive, add (all vector, all editable):
- **Icon badges / pills** for metadata (clock, hourglass, snowflake, difficulty dots).
- **Rounded tinted cards** for sections (ingredients, benefits).
- **Numbered step circles**, **check-mark bullets**, **leaf/botanical** bezier shapes.
- **Soft background blobs / watermarks** via `setFillAlpha` (reset to 1 after!).
- **More images** — a tidy 2×2 grid beats one lonely photo.
- **More text, strictly in-context** — expand "benefits/tips" using facts found *elsewhere
  in the same document* (e.g. an ingredient's described properties). **Never invent facts.**
- A **bottom flourish + tagline** to fill leftover space on short pages.
See `references/reportlab_cookbook.md` for ready-made functions.

### Phase 5 — Verify (do this every iteration)
- Render with `pdf2image` and build a **contact sheet** (grid of all pages) to scan layout.
- Zoom into dense pages and any decorative-overlap zones.
- Confirm text is native: `pypdf` → `extract_text()` must return the real words on every page.
- Specifically re-check: no overlapping text, no baked text in images, nothing past the footer.

### Phase 6 — Deliver
Copy to `/mnt/user-data/outputs/`, `present_files` it, and briefly tell the user:
what stays editable, that backgrounds were simplified (and can be re-added in Canva), and
any deliberate content choices (merged pages, expanded benefit text, swapped script fonts).

## Handling a page range
Users often want only some pages (e.g. "pages 42–55"). Build just those, but **pull
context from outside the range** when needed for coherence (e.g. a recipe's ingredients
live on the previous page) so each output page stands on its own.

## French / accents note
ReportLab built-in fonts use WinAnsi encoding, which **supports** French accents
(é è à ê î ç ô…), curly apostrophes `’`, guillemets, and the ellipsis `…`. Pass normal
Python `str`; no special handling needed.

## References (read as needed)
- `references/canva_import_rules.md` — the full parser model + do/don't, with the jsPDF
  equivalent for web/Node toolchains.
- `references/reportlab_cookbook.md` — copy-paste helpers: coords, cards, badges, icons,
  leaves, steps, flourish, image placement, per-page density control.
- `references/lessons_and_pitfalls.md` — keying thresholds, color sampling, layout flow,
  alternatives considered, and a debugging checklist.

## Scripts
- `scripts/inspect_pdf.py` — page sizes, images-per-page, flatten detection, rasterize.
- `scripts/keyout.py` — `crop_keyout`, `extract_assets` (connected-components), contact sheets.
- `scripts/design_kit.py` — importable ReportLab design system used to build the output.
