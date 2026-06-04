# ReportLab Cookbook for Canva-editable rebuilds

Companion to `scripts/design_kit.py`. These are the patterns that made the output both
**editable** and **good-looking**. Copy what you need.

## 1. Canvas, page size, top-origin coordinates
```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4   # (595.28, 841.89) pt — match the source
c = canvas.Canvas("out.pdf", pagesize=A4)
PW, PH = A4
def T(y): return PH - y     # work in top-origin; convert when drawing
```
Match the source page size exactly (read it from `inspect_pdf.py`). A4 source raster at
200 DPI is 1654×2340 px; to map a source-pixel (X,Y) to points: `x_pt = X*PW/1654`,
`y_pt_from_top = Y*PH/2340`.

## 2. Native text (the editable part)
```python
c.setFont("Helvetica-Bold", 28); c.setFillColorRGB(*BROWN)
c.drawCentredString(PW/2, T(60), "MON TITRE")        # title
# wrapped paragraph: see DesignKit.wrap()
# justified body: use Platypus Paragraph with alignment=TA_JUSTIFY, then wrap()/drawOn()
```
Fonts that exist everywhere and import cleanly: `Helvetica`, `Helvetica-Bold`,
`Helvetica-Oblique`, `Helvetica-BoldOblique`, `Times-Roman`, `Times-Bold`, `Times-Italic`,
`Times-BoldItalic`, `Courier`. A serif italic (`Times-BoldItalic`) is a decent stand-in for
a handwritten/script header while staying standard.

## 3. Transparent images as layers
```python
from reportlab.lib.utils import ImageReader
c.drawImage(ImageReader("leaf.png"), x, T(top)-h, w, h, mask='auto',
            preserveAspectRatio=True)   # mask='auto' honors PNG alpha
```
Soft watermark / faint botanical: wrap in `saveState()/setFillAlpha(0.07)/restoreState()`.

## 4. Vector graphics that read as "design"
- Rounded cards/pills: `c.roundRect(x, y, w, h, r, stroke, fill)`.
- Icons from primitives: clock = circle + 2 short lines; hourglass = 4 lines; snowflake =
  3 crossed lines; difficulty = filled/empty dots.
- Leaf/botanical: a 2-curve bezier (`beginPath/curveTo`) rotated with `translate+rotate`.
- Step numbers: filled circle + white number. Check marks: two short strokes.
- Soft background blobs: big circles at low `setFillAlpha`. **Always reset alpha to 1.**
All of these are in `design_kit.py` — prefer importing it.

## 5. Page density control (avoid overflow)
Long pages overflow the footer. Make the body flow with a y-cursor and expose knobs:
```python
def recipe(..., body_size=10.5, body_lead=15.0, gap=22, prep_start=500):
    cur = prep_start
    cur = section_header(...); cur += 24
    cur = bullets(...,size=body_size, lead=body_lead); cur += gap
    ...
```
For the *densest* pages pass smaller values (e.g. `body_size=9.3, body_lead=12.4, gap=12,
prep_start=476`). Then RENDER and confirm the last line sits above the footer (~y=805 on A4).
If a page is too packed, drop a decorative thumbnail rather than shrink text to illegibility.

## 6. Filling short pages (so the whole page is used)
- Lay images in a tidy **2×2 grid** (`DesignKit.image_grid`) instead of one lonely photo.
- Add a **benefits card** + **tip box** of in-context text.
- Add a **bottom flourish** (leaf trio + italic tagline) when the last content y < ~700.
- Keep a consistent top bar + footer so even sparse pages feel intentional.

## 7. Minimal full page (recipe-style)
```python
from design_kit import DesignKit, palette
dk = DesignKit(c, PW, PH, palette("brown_green"))
dk.background(); dk.topbar()
dk.title_block("Force & Brillance", 58, 27)
dk.badges(95, [("dots","Facile",1),("clock","Prépa 5 min"),
               ("hour","Pose 20–30 min"),("snow","2 sem. congel.")])
bottom = dk.ingredients_card(45, 150, 255, ["3 c. à soupe de crème de riz", ...])
dk.image_grid(["img/rice.png","img/fenugrec.png","img/hibiscus.png","img/gombo.png"])
by = dk.benefits_card(45, max(bottom,380)+14, 510, "Bienfaits des ingrédients",
                      ["Riz : gaine la fibre…", "Fenugrec : protéines…", ...])
ay = dk.steps_block(45, by+10, 510, "Application", ["Appliquer sur cheveux humides…", ...])
ay = dk.tip_box(45, ay+4, 510, "Les mucilages du fenugrec et du gombo…")
if ay < 700: dk.bottom_flourish(728, "Thiossane — des soins naturels, simples et accessibles.")
dk.footer("lala aicha thiam"); c.showPage()
```

## 8. Divider / section pages
Big light-grey number + section title, **never overlapping** (number ABOVE, title below, clear
gap). A `Helvetica-BoldOblique` number at ~120 pt in a 0.85 grey reads as a stylish accent.

## 9. Justified text-heavy pages
Use Platypus `Paragraph` with `ParagraphStyle(alignment=TA_JUSTIFY)`, `wrap(maxw, 9999)` then
`drawOn(c, x, T(y)-h)`; advance the cursor by the returned height. Escape `&` → `&amp;`.

## 10. Render + QA loop
```python
from pdf2image import convert_from_path
imgs = convert_from_path("out.pdf", dpi=100)         # contact sheet at low dpi
# tile imgs into a grid PNG and VIEW it; zoom dense pages at dpi=135
```
