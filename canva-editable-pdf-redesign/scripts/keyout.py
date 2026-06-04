#!/usr/bin/env python3
"""keyout.py — turn flattened-page crops into clean, transparent image layers.

Two core tools, both battle-tested:

1) crop_keyout(src_png, box, thr=236, frac=False) -> RGBA Image
   Crop a region and remove the background by BORDER FLOOD-FILL: only light pixels
   (min(R,G,B) >= thr) that are CONNECTED to the crop edge become transparent.
   This is the key trick — it preserves light/white parts INSIDE the subject
   (white rice in a dark bowl, foam, etc.) because they aren't connected to the edge.

2) extract_assets(src_png, out_dir, ...) -> list
   For a clean "library/asset sheet" (objects on white): segment every object via
   connected components (with dilation so multi-part objects merge), crop each, key it,
   and write a LABELED contact sheet so a human/agent can identify each asset.

Plus contact_sheet(images, path) to QA any set of crops.

CLI:
    python keyout.py crop  page.png 0.1,0.3,0.3,0.45 out.png --frac --thr 236
    python keyout.py assets library.png ./assets --dilate 14 --minarea 1500
"""
import sys, os, math, argparse
from collections import deque
import numpy as np
from PIL import Image, ImageDraw


def _flood_key(crop, thr=236):
    c = crop.convert("RGBA")
    arr = np.asarray(c).copy()
    light = arr[:, :, :3].min(2) >= thr
    h, w = light.shape
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y, x]:
            continue
        seen[y, x] = True
        if light[y, x]:
            arr[y, x, 3] = 0
            q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return Image.fromarray(arr, "RGBA")


def crop_keyout(src_png, box, thr=236, frac=False, pad=0):
    """box = (x0,y0,x1,y1) in pixels, or fractions of (W,H) if frac=True."""
    im = Image.open(src_png).convert("RGB")
    W, H = im.size
    if frac:
        x0, y0, x1, y1 = box
        box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
    x0, y0, x1, y1 = box
    box = (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad))
    return _flood_key(im.crop(box), thr)


def extract_assets(src_png, out_dir, dilate=14, minarea=1500, minside=40, thr=236,
                   keythr=236, cols=5, tile=300):
    """Segment all objects on a near-white sheet and dump keyed PNGs + a labeled sheet."""
    from scipy import ndimage
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(src_png).convert("RGB")
    a = np.asarray(im); H, W, _ = a.shape
    mask = a.min(2) < (thr - 2)                     # non-background
    md = ndimage.binary_dilation(mask, iterations=dilate)
    lab, n = ndimage.label(md)
    objs = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) < minarea:
            continue
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        if (x1 - x0) < minside or (y1 - y0) < minside:
            continue
        objs.append((x0, y0, x1, y1))
    objs.sort(key=lambda o: (o[1] // 120, o[0]))    # top->bottom, left->right
    saved = []
    for idx, (x0, y0, x1, y1) in enumerate(objs):
        pad = 8
        box = (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad))
        k = _flood_key(im.crop(box), keythr)
        fp = os.path.join(out_dir, f"asset_{idx:02d}.png")
        k.save(fp); saved.append(fp)
    # labeled contact sheet
    rows = math.ceil(len(saved) / cols) if saved else 1
    sheet = Image.new("RGB", (tile * cols, tile * rows), (235, 235, 235))
    d = ImageDraw.Draw(sheet)
    for i, fp in enumerate(saved):
        k = Image.open(fp); k.thumbnail((tile - 30, tile - 50))
        r, cc = divmod(i, cols)
        cell = Image.new("RGBA", (tile, tile), (255, 255, 255, 255))
        cell.alpha_composite(k, (15, 30))
        sheet.paste(cell.convert("RGB"), (cc * tile, r * tile))
        d.text((cc * tile + 8, r * tile + 6), str(i), fill=(200, 0, 0))
    sheet.save(os.path.join(out_dir, "_assets_sheet.png"))
    print(f"extracted {len(saved)} assets -> {out_dir} (see _assets_sheet.png)")
    return saved


def contact_sheet(image_paths, out_path, bg=(248, 239, 243), cols=4, tile=360):
    rows = math.ceil(len(image_paths) / cols)
    sheet = Image.new("RGB", (tile * cols, tile * rows), bg)
    d = ImageDraw.Draw(sheet)
    for i, fp in enumerate(image_paths):
        k = Image.open(fp).convert("RGBA"); k.thumbnail((tile - 30, tile - 40))
        r, cc = divmod(i, cols)
        cell = Image.new("RGBA", (tile, tile), bg + (255,))
        cell.alpha_composite(k, (15, 30)); sheet.paste(cell.convert("RGB"), (cc * tile, r * tile))
        d.text((cc * tile + 6, r * tile + 6), os.path.basename(fp), fill=(150, 0, 0))
    sheet.save(out_path); print("contact sheet ->", out_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("crop"); c.add_argument("src"); c.add_argument("box")
    c.add_argument("out"); c.add_argument("--frac", action="store_true")
    c.add_argument("--thr", type=int, default=236); c.add_argument("--pad", type=int, default=0)
    e = sub.add_parser("assets"); e.add_argument("src"); e.add_argument("out")
    e.add_argument("--dilate", type=int, default=14); e.add_argument("--minarea", type=int, default=1500)
    e.add_argument("--thr", type=int, default=236)
    a = ap.parse_args()
    if a.cmd == "crop":
        box = tuple(float(v) for v in a.box.split(","))
        if not a.frac:
            box = tuple(int(v) for v in box)
        crop_keyout(a.src, box, thr=a.thr, frac=a.frac, pad=a.pad).save(a.out)
        print("saved", a.out)
    elif a.cmd == "assets":
        extract_assets(a.src, a.out, dilate=a.dilate, minarea=a.minarea, thr=a.thr)
    else:
        ap.print_help()
