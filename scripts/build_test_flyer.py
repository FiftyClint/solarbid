#!/usr/bin/env python3
"""The test cell's flyer. 77 envelopes, 86 layer, pullet and breeder farms.

This is the B side of an A/B, and the variable is register. The mailer is a
document: type on white, hairline rules, photographs as a strip along the
bottom. It is deliberately plain, because it travels with a handwritten note and
a real stamp, and a glossy insert would expose the note as a device.

So this page has to be visibly a different animal, or the test measures nothing.
An earlier version failed that: same palette, same type, same rules, same photo
strip, different copy structure. Two pieces that a grower would say came from the
same company, because they did.

What carries the contrast:
  - A navy field across the top with the figure set large in the brand green.
    That green is unreadable on white, about 1.8:1, and excellent on this navy,
    which is the only place the palette lets it be used at size.
  - One photograph, full bleed, at real proportion rather than letterboxed.
  - Three figures pulled out at display size instead of buried in sentences.
  - Half the body copy the earlier version carried.

Ogilvy's rules still hold underneath: the headline earns the read on its own, the
caption carries a selling point rather than a label, and the close asks for one
small thing. Not solar-led, because the layer load model is unvalidated and the
offer here is the bill analysis, which does not depend on bird type.

    python scripts/build_test_flyer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.image import imread  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from brand import (  # noqa: E402
    ACCENT, ADDRESS, EMAIL, Flow, INK, L, LOGO_PATH, measure, MUTE, PAGE_H,
    PAGE_W, PAPER, PHONE, PHOTO_HERO, R, WEB,
)

# Type is what dated the earlier version. IBM Plex Serif body copy reads
# institutional, which is right for the mailer and wrong for the piece that is
# supposed to look like marketing. Bricolage Grotesque carries the display, and
# Instrument Sans the body: a sans text face, a wide type-scale range, and no
# panel boxes is roughly what separates a page made this year from one made
# fifteen years ago.
DISPLAY = "Bricolage Grotesque"
BODY = "Instrument Sans"
MONO = "Geist Mono"

# The navy field and the photograph are the two full-width elements, and how far
# they run depends on how this gets printed.
#
# An office laser cannot print to the paper edge. It leaves an unprintable strip
# of four or five millimetres, and it is rarely even on all four sides, so a
# design drawn to the edge comes back framed in a crooked white sliver that
# reads as a misprint. A commercial run on oversized stock trims that away.
#
# False is the safe default and matches copy/print_spec.md, which recommends
# printing this in the office: the two elements inset to a deliberate, even
# margin instead. Set True only for a printer that is genuinely taking bleed.
BLEED = False
EDGE = 0.0 if BLEED else 0.034
TOP = 1.0 if BLEED else 1.0 - EDGE * (PAGE_W / PAGE_H)

# Every figure is farm-grain, from the co-op account file, at the retail rate in
# solarbid.config. Re-derive all of them after any change to the workbook or the
# tariff. The single-house egg band is the one quoted because that is the farm
# the reader compares himself against, and 66 of the 86 in this cell are it.
# The band is rounded in the display slot because 88,986 - 131,871 is seventeen
# characters and will not set at 26pt in a third of the measure. The exact
# figures go in the line underneath, where they are still checkable.
STATS = [
    ("89k - 132k", "KWH A YEAR",
     "where the middle half land, 88,986 to 131,871"),
    ("107,958", "KWH A YEAR", "what the median single egg house runs"),
    ("31", "KW DEMAND", "median billed on the same farms"),
]

COPY = [
    "Pull your last twelve bills and add up the kilowatt-hours. Ten minutes, "
    "and you will know whether you sit inside that band.",

    "A farm above it is usually the same kind of farm with something wrong, and "
    "the something is more often on the bill than in the barn. A rate class "
    "that fit in 2011. A multiplier applied twice. Demand set by one bad July "
    "reading and carried all year.",

    "We read twelve months line by line, then look at where the power goes and "
    "what it would cost to use less.",
]


def main():
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.canvas.draw()

    # Type sits on the page margin unless that would crowd the field edge.
    FL = max(L, EDGE + 0.030)

    # ------------------------------------------------------------ navy field
    FIELD_BOT = 0.754
    ax.add_patch(Rectangle((EDGE, FIELD_BOT), 1 - 2 * EDGE, TOP - FIELD_BOT,
                           facecolor=INK, edgecolor="none", zorder=0))

    ax.text(FL, 0.956, "METERED USAGE   66 EGG FARMS   RANDOLPH AND CLAY "
            "COUNTIES", family=MONO, size=6.6, color="#6E97BC", ha="left",
            va="center", zorder=2)

    # The one figure on the page set at size, and the only place the palette
    # allows the green to carry text.
    ax.text(FL, 0.888, "$12,000", family=DISPLAY, weight="bold", size=76,
            color=ACCENT, ha="left", va="center", zorder=2)
    ax.text(FL, 0.836, "a year to run one egg house.", family=BODY, size=14,
            color="#A9C4DC", ha="left", va="center", zorder=2)

    head = Flow(fig, ax, 0.812, x0=FL, x1=R - 0.06)
    head.text("How much of that is a billing mistake?", DISPLAY, 25,
              weight="bold", color=PAPER, leading=1.14)
    print(f"headline ends at y={head.y:.3f} (field bottom {FIELD_BOT})")

    # ----------------------------------------------------------- photograph
    photo_top = FIELD_BOT
    if PHOTO_HERO.exists():
        img = imread(str(PHOTO_HERO))
        width = 1 - 2 * EDGE
        height = width * (PAGE_W / PAGE_H) / (img.shape[1] / img.shape[0])
        ax.imshow(img, extent=(EDGE, EDGE + width, photo_top - height,
                               photo_top), aspect="auto", zorder=1)
        photo_bot = photo_top - height
    else:
        photo_bot = photo_top

    flow = Flow(fig, ax, photo_bot - 0.016)
    # Captions get read about twice as often as body copy, so this one carries a
    # point rather than naming the picture.
    flow.text("A ground mount NEA Solar built near here. It is the last thing "
              "we do, and only if the first four say it is worth doing.",
              BODY, 8.6, color=MUTE, leading=1.4, max_w=0.60)

    # ------------------------------------------------------------ stat strip
    flow.gap(0.026)
    ax.plot([L, R], [flow.y, flow.y], color=INK, lw=1.1, solid_capstyle="butt")
    flow.gap(0.026)
    strip_top = flow.y
    col = (R - L) / 3
    for i, (big, unit, note) in enumerate(STATS):
        x = L + i * col
        # The unit sits under the figure rather than beside it. Set alongside,
        # the widest value ran into the next column's number.
        ax.text(x, strip_top, big, family=DISPLAY, weight="bold", size=26,
                color=INK, ha="left", va="center", zorder=2)
        ax.text(x, strip_top - 0.023, unit, family=MONO, size=6.4,
                color=MUTE, ha="left", va="center", zorder=2)
        sub = Flow(fig, ax, strip_top - 0.040, x0=x, x1=x + col - 0.030)
        sub.text(note, BODY, 8.4, color=MUTE, leading=1.40)
        bottom = sub.y
    flow.y = bottom

    # ------------------------------------------------------------------ body
    flow.gap(0.030)
    for i, para in enumerate(COPY):
        flow.text(para, BODY, 10.0, leading=1.54, max_w=0.70,
                  gap_after=0.012 if i < len(COPY) - 1 else 0.0)
    print(f"body ends at y={flow.y:.3f}")

    # ----------------------------------------------------------------- close
    flow.gap(0.018)
    ax.plot([L, R], [flow.y, flow.y], color=ACCENT, lw=3.0,
            solid_capstyle="butt")
    flow.gap(0.018)
    flow.text("Send us twelve months of your billing history.", DISPLAY, 18,
              weight="bold", color=INK, leading=1.20, gap_after=0.012)
    flow.text(f"Email it to {EMAIL}. Photographs of the bills are fine. We will "
              "tell you what we find, including if that is nothing worth doing. "
              "That answer is free too.", BODY, 9.8, color=INK, leading=1.52,
              max_w=0.62)
    print(f"close ends at y={flow.y:.3f}")

    # ---------------------------------------------------------------- footer
    if LOGO_PATH.exists():
        img = imread(str(LOGO_PATH))
        h = 0.030
        w = h * (img.shape[1] / img.shape[0]) * (PAGE_H / PAGE_W)
        ax.imshow(img, extent=(L, L + w, 0.026, 0.026 + h), zorder=3,
                  aspect="auto")
    ax.text(R, 0.048, "Cleaner Greener Future, with NEA Solar", family=BODY,
            weight="bold", size=9.0, color=INK, ha="right", va="center")
    ax.text(R, 0.032, f"{PHONE}    {WEB}", family=BODY, size=8.2,
            color=MUTE, ha="right", va="center")
    ax.text(R, 0.018, ADDRESS, family=BODY, size=8.2, color=MUTE, ha="right",
            va="center")

    out_pdf = Path("out/cgf_test_flyer.pdf")
    out_pdf.parent.mkdir(exist_ok=True)
    fig.savefig(out_pdf, facecolor=PAPER, dpi=300)
    fig.savefig("out/cgf_test_flyer.png", facecolor=PAPER, dpi=200)
    plt.close(fig)
    print(f"wrote {out_pdf}")


if __name__ == "__main__":
    main()
