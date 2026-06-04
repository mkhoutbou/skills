#!/usr/bin/env python3
"""inspect_pdf.py — analyse a source PDF before redesigning it.

Usage:
    python inspect_pdf.py input.pdf                 # report only
    python inspect_pdf.py input.pdf --raster 1,4,9  # also rasterize pages (1-based) @200dpi
    python inspect_pdf.py input.pdf --raster all --dpi 200 --out ./pages

Why: tells you whether the source is FLATTENED (every page == 1 image, i.e. text is baked
in and must be reconstructed) and gives page size so your ReportLab canvas matches.
"""
import sys, os, argparse
import fitz  # pymupdf


def inspect(path):
    doc = fitz.open(path)
    print(f"pages: {len(doc)}")
    flat = True
    for i, p in enumerate(doc):
        imgs = p.get_images(full=True)
        txt = p.get_text("text").strip()
        has_text = bool(txt)
        if len(imgs) != 1 or has_text:
            flat = False
        flag = " (TEXT IS SELECTABLE)" if has_text else ""
        print(f"  page {i+1:>3}: {p.rect.width:.0f}x{p.rect.height:.0f} pt | "
              f"images={len(imgs)} | text_chars={len(txt)}{flag}")
    print("\nVERDICT:",
          "FLATTENED source (rebuild all text as native)." if flat
          else "Source already has some native text/multiple layers — inspect per page.")
    print("Tip: A4 is 595x842 pt. At 200 DPI a full A4 raster is ~1654x2340 px.")
    return doc


def rasterize(doc, pages, dpi, out):
    os.makedirs(out, exist_ok=True)
    if pages == "all":
        idxs = range(len(doc))
    else:
        idxs = [int(x) - 1 for x in pages.split(",")]
    for i in idxs:
        pix = doc[i].get_pixmap(dpi=dpi)
        fp = os.path.join(out, f"p{i+1:02d}.png")
        pix.save(fp)
        print("rasterized", fp, f"{pix.width}x{pix.height}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--raster", default=None, help="'all' or comma list of 1-based pages")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--out", default="./pages")
    a = ap.parse_args()
    doc = inspect(a.pdf)
    if a.raster:
        rasterize(doc, a.raster, a.dpi, a.out)
