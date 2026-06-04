#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design_kit.py — a reusable, native-text ReportLab design system for building
Canva-editable PDFs. Import the DesignKit class, give it a canvas, and compose pages
with native text + vector graphics + transparent image layers.

ALL text drawn here is native/selectable (Canva-editable). ALL shapes are vector.
Images must be transparent PNGs (use keyout.py) and are placed with mask='auto'.

Coordinate convention: every helper takes y measured from the TOP of the page
(more intuitive). Internally T(y)=page_height-y converts to ReportLab's bottom-left.

Minimal example:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from design_kit import DesignKit, palette
    c = canvas.Canvas("out.pdf", pagesize=A4)
    dk = DesignKit(c, *A4, palette("brown_green"))
    dk.background(); dk.topbar()
    dk.title_block("MON TITRE", y=58)
    dk.badges(95, [("dots","Facile",1),("clock","5 min"),("snow","2 sem.")])
    b = dk.ingredients_card(45, 150, 250, ["3 c. à soupe de X", "1 c. à soupe de Y"])
    dk.image("img/x.png", 430, 150, 120)
    dk.footer("ma signature"); c.showPage(); c.save()
"""
import math
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader

# ---- ready-made palettes (sample your own from the source raster when possible) ----
PALETTES = {
    "brown_green": dict(  # warm botanical / African natural-care look
        PRIMARY=(0.337, 0.212, 0.106), PRIMARY_D=(0.24, 0.15, 0.07),
        ACCENT=(0.49, 0.66, 0.12), ACCENT_D=(0.36, 0.49, 0.09),
        INK=(0.13, 0.13, 0.13), MUTED=(0.55, 0.48, 0.40),
        PAGE=(0.992, 0.972, 0.937), CARD_A=(0.953, 0.973, 0.90),
        CARD_B=(0.97, 0.945, 0.91), WARN=(0.78, 0.55, 0.05)),
    "blush": dict(  # soft pink (recipe/beauty)
        PRIMARY=(0.13, 0.13, 0.15), PRIMARY_D=(0.1, 0.1, 0.12),
        ACCENT=(0.74, 0.32, 0.45), ACCENT_D=(0.55, 0.2, 0.32),
        INK=(0.18, 0.18, 0.20), MUTED=(0.62, 0.6, 0.62),
        PAGE=(0.976, 0.941, 0.957), CARD_A=(0.98, 0.93, 0.95),
        CARD_B=(0.97, 0.95, 0.96), WARN=(0.78, 0.55, 0.05)),
}
def palette(name): return PALETTES[name]


class DesignKit:
    def __init__(self, c, pw, ph, pal):
        self.c, self.PW, self.PH, self.p = c, pw, ph, pal

    # ---- coords & primitives ----
    def T(self, y): return self.PH - y
    def _fill(self, rgb, a=1): self.c.setFillColorRGB(*rgb); self.c.setFillAlpha(a)
    def _stroke(self, rgb, a=1): self.c.setStrokeColorRGB(*rgb); self.c.setStrokeAlpha(a)

    def rounded(self, x, y_top, w, h, r, fill=None, stroke=None, lw=1, fa=1, sa=1):
        c = self.c
        if fill: self._fill(fill, fa)
        if stroke: self._stroke(stroke, sa); c.setLineWidth(lw)
        c.roundRect(x, self.T(y_top) - h, w, h, r, stroke=1 if stroke else 0, fill=1 if fill else 0)
        c.setFillAlpha(1); c.setStrokeAlpha(1)

    def circle(self, cx, cy_top, r, fill=None, stroke=None, lw=1, fa=1):
        c = self.c
        if fill: self._fill(fill, fa)
        if stroke: self._stroke(stroke); c.setLineWidth(lw)
        c.circle(cx, self.T(cy_top), r, stroke=1 if stroke else 0, fill=1 if fill else 0)
        c.setFillAlpha(1); c.setStrokeAlpha(1)

    def text(self, x, y, s, font="Helvetica", size=11, color=None, align="left", a=1):
        c = self.c; color = color or self.p["INK"]
        c.setFont(font, size); self._fill(color, a)
        if align == "center": c.drawCentredString(x, self.T(y), s)
        elif align == "right": c.drawRightString(x, self.T(y), s)
        else: c.drawString(x, self.T(y), s)
        c.setFillAlpha(1)

    def wrap(self, x, y, s, maxw, font="Helvetica", size=10.5, lead=14.5, color=None, align="left"):
        c = self.c; color = color or self.p["INK"]; c.setFont(font, size); self._fill(color)
        line, yy = "", y
        for w in s.split(" "):
            t = (line + " " + w).strip()
            if stringWidth(t, font, size) <= maxw or not line: line = t
            else:
                (c.drawCentredString if align == "center" else c.drawString)(x, self.T(yy), line)
                yy += lead; line = w
        if line:
            (c.drawCentredString if align == "center" else c.drawString)(x, self.T(yy), line)
            yy += lead
        c.setFillAlpha(1); return yy

    def image(self, path, cx, y_top, w, maxh=999, align="c"):
        try:
            im = ImageReader(path); iw, ih = im.getSize(); h = w * ih / iw
            if h > maxh: w = w * maxh / h; h = maxh
            x = cx - w / 2 if align == "c" else cx
            self.c.drawImage(im, x, self.T(y_top) - h, w, h, mask='auto', preserveAspectRatio=True)
            return h
        except Exception: return 0

    def image_watermark(self, path, cx, y_top, w, a=0.07):
        c = self.c; c.saveState(); c.setFillAlpha(a)
        try:
            im = ImageReader(path); iw, ih = im.getSize(); h = w * ih / iw
            c.drawImage(im, cx - w / 2, self.T(y_top) - h, w, h, mask='auto')
        except Exception: pass
        c.restoreState()

    # ---- vector icons ----
    def icon_clock(self, cx, cy, r=7, col=None):
        col = col or self.p["PRIMARY"]; self._stroke(col); self.c.setLineWidth(1.4)
        self.c.circle(cx, self.T(cy), r, stroke=1, fill=0); self.c.setLineWidth(1.3)
        self.c.line(cx, self.T(cy), cx, self.T(cy) + r * .55)
        self.c.line(cx, self.T(cy), cx + r * .45, self.T(cy)); self.c.setStrokeAlpha(1)

    def icon_hour(self, cx, cy, r=7, col=None):
        col = col or self.p["PRIMARY"]; self._stroke(col); self.c.setLineWidth(1.3)
        top, bot = self.T(cy) + r, self.T(cy) - r
        self.c.line(cx - r*.7, top, cx + r*.7, top); self.c.line(cx - r*.7, bot, cx + r*.7, bot)
        self.c.line(cx - r*.7, top, cx + r*.7, bot); self.c.line(cx + r*.7, top, cx - r*.7, bot)
        self.c.setStrokeAlpha(1)

    def icon_snow(self, cx, cy, r=7, col=None):
        col = col or self.p["PRIMARY"]; self._stroke(col); self.c.setLineWidth(1.3)
        for ang in (90, 30, 150):
            a = math.radians(ang); dx, dy = math.cos(a)*r, math.sin(a)*r
            self.c.line(cx - dx, self.T(cy) - dy, cx + dx, self.T(cy) + dy)
        self.c.setStrokeAlpha(1)

    def icon_dots(self, cx, cy, level, col=None):
        col = col or self.p["PRIMARY"]
        for i in range(3):
            x = cx - 8 + i * 8
            if i < level: self.circle(x, cy, 2.6, fill=col)
            else: self.circle(x, cy, 2.6, stroke=col, lw=1)

    def leaf(self, cx, cy, L=22, ang=30, col=None, a=1):
        col = col or self.p["ACCENT"]; c = self.c; c.saveState()
        self._fill(col, a); c.translate(cx, self.T(cy)); c.rotate(ang)
        p = c.beginPath(); p.moveTo(0, 0)
        p.curveTo(L*.35, L*.45, L*.85, L*.30, L, 0)
        p.curveTo(L*.85, -L*.30, L*.35, -L*.45, 0, 0); p.close()
        c.drawPath(p, fill=1, stroke=0); c.restoreState(); c.setFillAlpha(1)

    def check(self, x, y, col=None):
        col = col or self.p["ACCENT"]; self._stroke(col); self.c.setLineWidth(1.8)
        self.c.line(x, self.T(y) - 1, x + 3, self.T(y) - 4)
        self.c.line(x + 3, self.T(y) - 4, x + 8, self.T(y) + 3.5); self.c.setStrokeAlpha(1)

    def step_circle(self, cx, cy, n):
        self.circle(cx, cy, 12, fill=self.p["ACCENT"])
        self.text(cx, cy + 4, str(n), font="Helvetica-Bold", size=12, color=(1, 1, 1), align="center")

    # ---- page furniture ----
    def background(self, rgb=None, blobs=True):
        p = self.p; self._fill(rgb or p["PAGE"]); self.c.rect(0, 0, self.PW, self.PH, stroke=0, fill=1)
        self.c.setFillAlpha(1)
        if blobs:
            self.circle(self.PW - 10, 40, 130, fill=p["ACCENT"], fa=0.10)
            self.circle(20, self.PH - 30, 150, fill=p["PRIMARY"], fa=0.06)

    def topbar(self):
        p = self.p; self._fill(p["PRIMARY"]); self.c.rect(0, self.PH - 7, self.PW, 7, stroke=0, fill=1)
        self.c.setFillAlpha(1); self._fill(p["ACCENT"]); self.c.rect(0, self.PH - 10, self.PW, 3, stroke=0, fill=1)
        self.c.setFillAlpha(1)

    def footer(self, name):
        self.leaf(self.PW/2 - 58, 815, 9, 20); self.leaf(self.PW/2 - 58, 815, 9, 160)
        self.text(self.PW/2, 816, name, font="Times-Italic", size=9.5, color=self.p["MUTED"], align="center")

    def title_block(self, t, y=58, size=27):
        p = self.p; w = stringWidth(t, "Helvetica-Bold", size)
        self.text(self.PW/2, y, t, font="Helvetica-Bold", size=size, color=p["PRIMARY"], align="center")
        lx, rx = self.PW/2 - w/2 - 20, self.PW/2 + w/2 + 20
        if lx > 40: self.leaf(lx, y - 6, 14, 200); self.leaf(rx, y - 6, 14, -20)
        self._stroke(p["ACCENT"]); self.c.setLineWidth(2)
        self.c.line(self.PW/2 - 70, self.T(y + 14), self.PW/2 + 70, self.T(y + 14))
        self._stroke(p["PRIMARY"], 0.5); self.c.setLineWidth(0.8)
        self.c.line(self.PW/2 - 110, self.T(y + 19), self.PW/2 + 110, self.T(y + 19)); self.c.setStrokeAlpha(1)

    def badges(self, y, items):
        """items: (icon, label[, level]); icon in {dots,clock,hour,snow}."""
        p = self.p; ph, gap, pad = 30, 12, 13
        widths = [pad + 22 + stringWidth(it[1], "Helvetica-Bold", 9) + pad for it in items]
        x = self.PW/2 - (sum(widths) + gap * (len(items) - 1)) / 2
        for it, w in zip(items, widths):
            self.rounded(x, y, w, ph, 15, fill=p["CARD_A"], stroke=p["ACCENT"], lw=1)
            icx, icy = x + pad + 9, y + 18
            {"clock": self.icon_clock, "hour": self.icon_hour, "snow": self.icon_snow}.get(it[0],
                lambda a, b: self.icon_dots(a, b, it[2]) if it[0] == "dots" else None)(icx, icy)
            self.text(x + pad + 24, y + 20, it[1], font="Helvetica-Bold", size=9, color=p["PRIMARY_D"])
            x += w + gap

    def section_header(self, x, y, label):
        p = self.p; self.leaf(x + 4, y - 3, 11, 200)
        self.text(x + 20, y, label, font="Helvetica-BoldOblique", size=14, color=p["ACCENT_D"])
        self._stroke(p["ACCENT"], 0.6); self.c.setLineWidth(1)
        w = stringWidth(label, "Helvetica-BoldOblique", 14)
        self.c.line(x + 20, self.T(y + 4), x + 20 + w, self.T(y + 4)); self.c.setStrokeAlpha(1)

    def ingredients_card(self, x, y, w, items, title="Ingrédients"):
        p = self.p; line_h, inner = 17, 30
        h = inner + line_h * len(items) + 14
        self.rounded(x, y, w, h, 12, fill=p["CARD_A"], stroke=p["ACCENT"], lw=1.2)
        self.section_header(x + 14, y + 22, title); yy = y + inner + 14
        for it in items:
            self._fill(p["PRIMARY"]); self.c.circle(x + 22, self.T(yy) - 3.5, 2.3, stroke=0, fill=1); self.c.setFillAlpha(1)
            self.wrap(x + 32, yy, it, w - 44, font="Helvetica-Bold", size=10.5, lead=15)
            yy += line_h
        return y + h

    def benefits_card(self, x, y, w, title, lines):
        p = self.p; line_h = 16
        rows = sum(max(1, math.ceil(stringWidth(s, "Helvetica", 9.5) / (w - 44))) for s in lines)
        h = 30 + rows * line_h + 14
        self.rounded(x, y, w, h, 12, fill=p["CARD_B"], stroke=p["PRIMARY"], lw=0.9, sa=0.5)
        self.section_header(x + 14, y + 22, title); yy = y + 44
        for s in lines:
            self.check(x + 18, yy)
            yy = self.wrap(x + 32, yy, s, w - 44, font="Helvetica", size=9.5, lead=14) + 2
        return y + h

    def steps_block(self, x, y, w, title, steps):
        self.section_header(x, y, title); yy = y + 26
        for i, s in enumerate(steps, 1):
            self.step_circle(x + 12, yy + 3, i)
            end = self.wrap(x + 32, yy, s, w - 40, font="Helvetica-Bold", size=10.5, lead=15)
            yy = max(end, yy + 24) + 6
        return yy

    def tip_box(self, x, y, w, text_s, label="Le savais-tu ?"):
        p = self.p; lines = max(1, math.ceil(stringWidth(text_s, "Helvetica", 9.5) / (w - 60)))
        h = 30 + lines * 14 + 12
        self.rounded(x, y, w, h, 10, fill=(0.97, 0.94, 0.86), stroke=p["WARN"], lw=0.9, sa=0.6)
        self.circle(x + 22, y + 22, 11, fill=p["WARN"])
        self.text(x + 22, y + 26, "!", font="Helvetica-Bold", size=13, color=(1, 1, 1), align="center")
        self.text(x + 40, y + 19, label, font="Helvetica-Bold", size=10.5, color=p["WARN"])
        self.wrap(x + 40, y + 34, text_s, w - 54, font="Helvetica", size=9.5, lead=14, color=p["PRIMARY_D"])
        return y + h

    def bottom_flourish(self, y, tagline):
        self.leaf(self.PW/2 - 17, y, 13, 210); self.leaf(self.PW/2, y - 4, 15, 270); self.leaf(self.PW/2 + 17, y, 13, 330)
        self.text(self.PW/2, y + 30, tagline, font="Times-Italic", size=12.5, color=self.p["ACCENT_D"], align="center")

    def image_grid(self, paths, x0=372, x1=482, y0=158, y1=276, w=98, maxh=84):
        """tidy 2x2 grid for up to 4 transparent images in a right-hand column."""
        grid = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
        for i, pth in enumerate(paths[:4]):
            self.image(pth, grid[i][0], grid[i][1], w, maxh)
