#!/usr/bin/env python3
"""Make a bleed-to-the-edge design safe to print on a home printer.

The Canva pieces run their navy fields to the paper edge. No home printer can
put ink there. It holds back roughly 0.17in on the sides and often more at the
foot, and the amount is rarely equal on all four, so a full-bleed page comes out
framed in a lopsided white sliver that reads as a misprint rather than a design.

The driver's "shrink to fit" will do something about it, but it shrinks by
whatever the driver feels like and centres it by its own rules, which differ
between printers and change between sessions. Doing it in the file instead means
the margin is chosen once, is identical on every copy, and every printer just
prints at 100%.

Scales each page to sit inside a 0.25in safe margin and centres it, which is
0.941 scale on letter. The white frame is even, so it reads as a border rather
than as an accident.

    python scripts/prep_home_print.py IN.pdf [IN2.pdf ...]

Writes alongside the input as *_homeprint.pdf.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

# Sides most consumer printers cannot reach is about 0.17in. A quarter inch
# clears that with room for paper skew on a hand-fed sheet.
SAFE_MARGIN_IN = 0.25
PT = 72.0
OUT_DIR = Path("out/home_print")


def fit_page(src: pymupdf.Document, out: pymupdf.Document, index: int) -> float:
    page = src[index]
    w_in, h_in = page.rect.width / PT, page.rect.height / PT
    avail_w = w_in - 2 * SAFE_MARGIN_IN
    avail_h = h_in - 2 * SAFE_MARGIN_IN
    scale = min(avail_w / w_in, avail_h / h_in)

    new_w, new_h = w_in * scale, h_in * scale
    x0 = (w_in - new_w) / 2
    y0 = (h_in - new_h) / 2

    dest = out.new_page(width=page.rect.width, height=page.rect.height)
    dest.show_pdf_page(
        pymupdf.Rect(x0 * PT, y0 * PT, (x0 + new_w) * PT, (y0 + new_h) * PT),
        src, index)
    return scale


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for raw in paths:
        src_path = Path(raw)
        src = pymupdf.open(src_path)
        out = pymupdf.open()
        scale = 1.0
        for i in range(src.page_count):
            scale = fit_page(src, out, i)
        target = OUT_DIR / f"{src_path.stem}_homeprint.pdf"
        out.save(target, deflate=True)
        print(f"{src_path.name}: {src.page_count} page(s) at {scale:.3f} scale "
              f"-> {target}")

    print(f"\nPrint these at 100%, NOT 'fit to page'. Scaling twice shrinks the "
          f"page again and the margin stops being even.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
