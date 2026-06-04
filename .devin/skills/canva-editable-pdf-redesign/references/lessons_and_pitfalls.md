# Lessons, Pitfalls & Alternatives

Hard-won notes from real rebuilds. Read this before you start; re-read when something looks off.

## Image keying (background removal)

- **Use border flood-fill, not global thresholding.** Global "alpha-out light pixels" destroys
  light parts of the subject (white rice in a black bowl, foam, pale petals). Flood-fill from
  the four edges only removes background *connected to the border*; interior lights survive.
  (`keyout.py: _flood_key`.)
- **Threshold tuning (`thr`, the min-channel cutoff for "background"):**
  - Pure white sheets / clipart: `236–242`.
  - Warm/cream pages: lower to `230–234`.
  - If the subject has near-white edges that get eaten, lower the threshold or shrink the crop.
  - If background scraps remain (mid-grey photographic backdrops), tighten the crop box rather
    than chasing the threshold — photographic, non-uniform backdrops don't flood-fill cleanly.
- **Halos / fringes** are usually acceptable on a tinted page. If not, erode the alpha by 1 px.
- **Connected-components extraction** (`extract_assets`) is ideal for a "library" page of objects
  on white: `binary_dilation(iterations≈14)` merges multi-part objects (flower+leaves, bowl+pile),
  `label` finds them, filter tiny specks by `minarea`. Always dump the **labeled contact sheet**
  and identify assets by eye — never trust the ordering blindly.
- **A clean clipart library beats tiny in-text photos.** Objects-on-white clipart keys perfectly
  and looks more "parlant" than a 90px photo cropped from a busy page.

## Backgrounds: the faithful-vs-editable tradeoff
You can't reproduce a photographic background AND keep it editable — a flat photo is the opposite
of editable, and you usually can't separate the baked-in text from it anyway. Options, best first:
1. **Sample the page's light tint** (median of the lightest pixels in the margins) and fill solid.
2. **Soft vector blobs / gradient** in the brand colors for depth.
3. **Faint image watermark** (a single keyed motif at ~6–8% alpha) for texture.
Tell the user they can drop the original photo back in as a background layer inside Canva.

## Color sampling
Sample brand colors straight from the source raster (e.g. title glyph pixels, accent text) so the
rebuild matches. Margins → background tint; a bold title stroke → primary; a green label → accent.

## Layout & overflow
- Flow the lower half with a **y-cursor**; don't hard-code every y.
- Expose `body_size / leading / gap / start` knobs and **compact only the dense pages**.
- Cap image heights so they fit their band; align ingredient columns on a common baseline for tidiness.
- After EVERY build, render a contact sheet and scan for: text past the footer, images overlapping
  cards/tips, and (critical) any two text elements sharing space.

## The overlapping-text trap (most important)
Designers love "big number behind the title". In a PDF it looks great; in Canva it **breaks** —
the two text boxes overlap and the importer interleaves their characters. If you want the look:
- put the number/word **clearly above or beside** the title (no shared rectangle), **or**
- render the decoration as a **vector shape** or a **flattened image element** (an image layer is
  fine; it's *text-over-text* that fragments).

## Expanding text "in context" (when asked to add more)
Enrich pages with benefit/tip text **sourced from elsewhere in the same document** (e.g. the
ingredient-property pages). This is legitimate and on-brand. **Never fabricate facts, dosages, or
claims.** Keep the author's wording and even their typos in the recipe body unless told to fix them.

## Image sourcing reality
- The sandbox network is typically restricted to package registries; you usually **cannot download
  arbitrary web images**. `image_search` can find/preview but not reliably fetch them.
- **Best source: the input PDF itself** (its own photos), then a reusable clipart library you keep
  on disk between tasks (assets can persist across turns in the same session).
- Don't promise web image downloads you can't deliver; set expectations and use what you can extract.

## Fonts & encoding
- Stick to ReportLab built-ins for guaranteed Canva matching. WinAnsi covers French accents,
  `’`, `«»`, `…` — pass normal `str`.
- A custom/script font *can* be embedded, but Canva may substitute it; better to use a standard font
  and let the user pick a script font in Canva.

## Tooling gotchas
- `pip install ... --break-system-packages`.
- `pdf2image` needs poppler; if missing, `apt`-style installs may be blocked — rasterize via
  `fitz` (`page.get_pixmap`) as a fallback for QA.
- Watch heredocs: a stray `EOF` accidentally written into a `.py` file causes `NameError: EOF`.
- Reset `setFillAlpha(1)`/`setStrokeAlpha(1)` after any translucent drawing, or later elements vanish.

## Debugging checklist (run when output looks wrong)
1. `extract_text()` empty on a page → your text got rasterized somewhere. Find and de-flatten it.
2. Words fragmented in Canva → overlapping text elements. Separate them.
3. Stray glyph inside an image → crop caught a caption. Re-crop tighter.
4. Image is a visible rectangle on the page → background not keyed (wrong threshold / non-uniform
   backdrop). Re-key or tighten crop.
5. Last paragraph cut off at the bottom → overflow; compact that page's density knobs.
6. Subject partially erased → global keying or too-high threshold; switch to flood-fill / lower thr.
7. Colors look off-brand → sample them from the source raster instead of guessing.

## Suggested deliverable note to the user
State plainly: text stays editable; standard fonts (swap to a script font in Canva if desired);
images are separate layers; photographic backgrounds were simplified to solid/vector (re-add in
Canva if wanted); list any deliberate choices (merged/added pages, expanded benefit text).
