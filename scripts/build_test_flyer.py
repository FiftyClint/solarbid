#!/usr/bin/env python3
"""Ogilvy-register test flyer for the 88 layer, pullet and breeder farms.

The A/B against the informational mailer. Same offer, same facts, different
register: a headline that has to earn the read on its own, long body copy in two
columns, a photograph carrying a caption, and one low-friction close.

Ogilvy's rules, the ones that apply here:
  - The headline is most of the money. Make it specific and give it news.
  - Long copy sells when the reader is interested. Do not trim to look clean.
  - Captions get read about twice as often as body copy, so put a selling
    point in the caption rather than a label.
  - Serif body. Never be clever at the cost of being clear.

Deliberately NOT solar-led. The layer load model is unvalidated, so the offer
here is the bill analysis, which does not depend on bird type. The array appears
once, low, captioned as the last step. That keeps this a test of register rather
than a claim we cannot size.

    python scripts/build_test_flyer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.image import imread  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from brand import (  # noqa: E402
    ADDRESS, BRAND, EMAIL, Flow, INK, L, LOGO_PATH, MUTE, PAGE_H, PAGE_W,
    PANEL, PAPER, PHONE, PHOTO_GROUND_WIDE, R, RULE_C, WEB,
)

HEAD = "Work Sans"
SERIF = "IBM Plex Serif"
MONO = "Geist Mono"

GUTTER = 0.042
COL_W = (R - L - GUTTER) / 2
COL2_X = L + COL_W + GUTTER

# Every figure below is farm-grain median from the co-op account file, derived
# the same way as the mailer table. Regenerate with scripts/segment_table.py
# style rollup if the workbook changes.
LEFT_COPY = [
    ("head", "Where most farms land"),
    ("body", "Metered usage on the 88 layer, pullet and breeder farms in this "
             "area puts the middle half between 89,832 and 138,000 "
             "kilowatt-hours a year. The median house runs 112,368."),
    ("body", "That is a narrow band for buildings of different ages, put up by "
             "different people, running different birds. Pull your last twelve "
             "bills and add up the kilowatt-hours. You will know in ten minutes "
             "whether you sit inside it."),
    ("head", "If you are above the band"),
    ("body", "A farm sitting above a cluster that tight is usually not a "
             "different kind of farm. It is the same kind of farm with "
             "something wrong, and the something is more often on the bill than "
             "in the barn."),
    ("body", "Look at the demand line while you are in there. The median on "
             "these farms is 31 kilowatts. A house billed well above that in a "
             "month when nothing on the farm changed is worth a question."),
]

RIGHT_COPY = [
    ("head", "What tends to be wrong"),
    ("body", "A rate class that fit the farm in 2011 and does not fit how it "
             "runs now. A meter multiplier applied twice. Demand set by one bad "
             "reading in July and carried on every bill for a year. Sales tax "
             "charged on power the farm may be exempt from."),
    ("body", "None of that is exotic. It is arithmetic, and it is sitting on "
             "paper you already receive every month."),
    ("head", "What we do about it"),
    ("body", "We read twelve months of billing line by line. What turns up "
             "there is money back with no capital spent and nothing bought. "
             "Then we look at where the power actually goes, which on a poultry "
             "farm is mostly ventilation, and what it would cost to use less."),
    ("body", "Only then do we look at what is available to pay for the work. "
             "Qualifying for an incentive and collecting one are two different "
             "jobs, and the second is where most of the money gets lost."),
]


def col_head(flow, title):
    flow.gap(0.021)
    flow.ax.text(flow.x0, flow.y, title, family=HEAD, weight="bold", size=10.5,
                 color=BRAND, ha="left", va="baseline")
    flow.gap(0.010)
    flow.ax.plot([flow.x0, flow.x1], [flow.y, flow.y], color=RULE_C, lw=0.7,
                 solid_capstyle="butt")
    flow.gap(0.004)


def render_column(flow, blocks):
    for kind, text in blocks:
        if kind == "head":
            col_head(flow, text)
        else:
            flow.text(text, SERIF, 9.0, leading=1.46, gap_after=0.008)
    return flow.y


def main():
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.canvas.draw()

    # No masthead band. Ogilvy put the advertiser's mark small and late; a
    # branded bar across the top announces an ad before the headline gets a
    # chance to earn the read.
    flow = Flow(fig, ax, 0.955)

    flow.text("About $13,500 a year to run one egg house. How much of that "
              "is a billing mistake?", SERIF, 24, weight="bold", leading=1.16,
              gap_after=0.012)
    flow.text("A year of metered usage on 176 poultry farms in Randolph and "
              "Clay counties shows where a house like yours should sit. If "
              "yours sits above it, the reason is usually on paper.",
              SERIF, 11.8, color=MUTE, leading=1.40, gap_after=0.010)

    ax.plot([L, R], [flow.y, flow.y], color=INK, lw=1.4, solid_capstyle="butt")
    flow.gap(0.004)

    # ---------------------------------------------------------------- columns
    top = flow.y
    left = Flow(fig, ax, top, x0=L, x1=L + COL_W)
    right = Flow(fig, ax, top, x0=COL2_X, x1=R)
    y_left = render_column(left, LEFT_COPY)
    y_right = render_column(right, RIGHT_COPY)
    print(f"columns end at left={y_left:.3f} right={y_right:.3f}")

    flow.y = min(y_left, y_right)

    # ----------------------------------------------------------------- photo
    have = [p for p in PHOTO_GROUND_WIDE if p.exists()]
    if have:
        flow.gap(0.018)
        gap = 0.014
        w = ((R - L) - gap * (len(have) - 1)) / len(have)
        height = w * (PAGE_W / PAGE_H) / 4.6
        top_y = flow.y
        for i, path in enumerate(have):
            x0 = L + i * (w + gap)
            ax.imshow(imread(str(path)),
                      extent=(x0, x0 + w, top_y - height, top_y),
                      aspect="auto", zorder=2)
        flow.gap(height + 0.011)
        # The caption gets read about twice as often as the body, so it carries
        # a point rather than naming the picture.
        flow.text("Arrays NEA Solar built for growers in this area. This is the "
                  "last thing we do, and only if the first four say it is worth "
                  "doing.", SERIF, 9.0, color=MUTE, leading=1.4)

    # ----------------------------------------------------------------- close
    flow.gap(0.016)
    box_top = flow.y
    pad = 0.017
    inner = Flow(fig, ax, box_top - pad, x0=L + 0.024, x1=R - 0.024)
    inner.text("Send us twelve months of your billing history.", SERIF, 15,
               weight="bold", color=INK, leading=1.25, gap_after=0.008)
    inner.text(f"Email it to {EMAIL}. Photographs of the bills are fine. We "
               "will read them and tell you what we find, including the "
               "possibility that we find nothing worth doing. That answer is "
               "free as well.", SERIF, 9.8, color=INK, leading=1.46)
    box_bottom = inner.y - pad
    ax.add_patch(Rectangle((L, box_bottom), R - L, box_top - box_bottom,
                           facecolor=PANEL, edgecolor="none", zorder=0))
    flow.y = box_bottom
    print(f"close box bottom at y={flow.y:.3f}")

    # ---------------------------------------------------------------- footer
    if LOGO_PATH.exists():
        img = imread(str(LOGO_PATH))
        h = 0.030
        w = h * (img.shape[1] / img.shape[0]) * (PAGE_H / PAGE_W)
        ax.imshow(img, extent=(L, L + w, 0.026, 0.026 + h), zorder=3,
                  aspect="auto")
    ax.text(R, 0.048, "Cleaner Greener Future, with NEA Solar", family=HEAD,
            weight="bold", size=9.2, color=INK, ha="right", va="center")
    ax.text(R, 0.032, f"{PHONE}   ·   {WEB}", family=HEAD, size=8.4,
            color=MUTE, ha="right", va="center")
    ax.text(R, 0.018, ADDRESS, family=HEAD, size=8.4, color=MUTE, ha="right",
            va="center")

    out_pdf = Path("out/cgf_test_flyer.pdf")
    out_pdf.parent.mkdir(exist_ok=True)
    fig.savefig(out_pdf, facecolor=PAPER, dpi=300)
    fig.savefig("out/cgf_test_flyer.png", facecolor=PAPER, dpi=200)
    plt.close(fig)
    print(f"wrote {out_pdf}")


if __name__ == "__main__":
    main()
