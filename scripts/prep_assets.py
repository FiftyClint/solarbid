#!/usr/bin/env python3
"""Normalize dropped-in assets to the shapes the layouts expect.

Run after adding photos or a new logo to assets/. Reproducible, so nobody has
to hand-crop in an image editor and nobody accidentally ships a stretched
photo.

    python scripts/prep_assets.py
"""

from pathlib import Path

from PIL import Image

ASSETS = Path("assets")

# The solar flyer's photo band gives each image a half-width slot on an 8.5x11
# page: about 3.56in wide by 2.04in tall.
BAND_ASPECT = 1.75

# The one-page sheet has less room, so a pair at 1.75 would run into the
# footer. A wider crop keeps them full width and short enough to fit. Cropping
# is the right answer here rather than scaling, which would distort them. Both
# frames carry a lot of dead sky and foreground dirt, so the band loses nothing
# by being cut this thin.
WIDE_ASPECT = 4.6

# Source files as dropped in, with the vertical bias for the crop. Farm photos
# carry a lot of sky that does nothing, so both bias downward toward the array.
SOURCES = [
    ("IMG_0716.jpg", "ground_mount_1.jpg", 0.42),
    ("IMG_1678.jpg", "ground_mount_2.jpg", 0.72),
]

LOGO_SOURCES = ["CGF Logo - 2 (1).png", "cgf_logo_src.png"]
LOGO_OUT = ASSETS / "cgf_logo.png"


def crop_to_aspect(im: Image.Image, aspect: float, bias: float) -> Image.Image:
    """Center-crop to a target aspect, biased vertically.

    bias 0.5 is centered, higher keeps more of the lower part of the frame.
    """
    w, h = im.size
    if w / h > aspect:
        new_w = int(h * aspect)
        left = (w - new_w) // 2
        return im.crop((left, 0, left + new_w, h))

    new_h = int(w / aspect)
    top = int((h - new_h) * bias)
    top = max(0, min(top, h - new_h))
    return im.crop((0, top, w, top + new_h))


def trim_transparent(im: Image.Image) -> Image.Image:
    """Drop transparent padding so the logo fills its slot."""
    if im.mode != "RGBA":
        return im
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox) if bbox else im


def main() -> int:
    for src_name, out_name, bias in SOURCES:
        src = ASSETS / src_name
        if not src.exists():
            print(f"skip {src_name}, not present")
            continue
        im = Image.open(src).convert("RGB")
        for aspect, suffix in ((BAND_ASPECT, ""), (WIDE_ASPECT, "_wide")):
            out = crop_to_aspect(im, aspect, bias)
            name = out_name.replace(".jpg", f"{suffix}.jpg")
            out.save(ASSETS / name, quality=92)
            print(f"{src_name} {im.size} -> {name} {out.size} "
                  f"(aspect {out.size[0]/out.size[1]:.2f})")

    for name in LOGO_SOURCES:
        src = ASSETS / name
        if not src.exists():
            continue
        im = trim_transparent(Image.open(src).convert("RGBA"))
        im.save(LOGO_OUT)
        print(f"{name} -> {LOGO_OUT.name} {im.size} "
              f"(aspect {im.size[0]/im.size[1]:.2f})")
        break
    else:
        print("no logo source found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
