#!/usr/bin/env python3
"""One page: what solar looks like on a poultry farm in this area.

The companion to the how-we-work sheet, and the answer to "here is what that
might look like on your farm." One page, so the numbers carry it and the rules
get one line each rather than a section.

The two lines that cost us the sale stay in. REAP is halted and Arkansas pays
avoided cost for exports. Dropping them to save space would take out the
reason to believe the rest.
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

# Derived, not hand-entered. Regenerate with scripts/segment_table.py after any
# change to the account file or the pricing assumptions. Rows are at FARM grain:
# the workbook's grain is the meter, and a per-account median described half a
# farm for every grower carrying two meters.
TABLE = [
    ("3 houses", "232,080", "140 kW", "$294,000", "$147,000", "$19,400", "4.2 yrs"),
    ("4 houses", "247,200", "150 kW", "$315,000", "$157,500", "$20,700", "4.2 yrs"),
    ("5-6 houses", "331,200", "200 kW", "$420,000", "$210,000", "$27,700", "4.2 yrs"),
]
COLS = ["", "kWh/year", "System", "Installed", "Federal credit", "Saves/year",
        "Payback"]

CREDIT = [
    ("Federal investment credit, base rate", "30%"),
    ("Domestic content adder", "10%"),
    ("Energy community adder, all counties here", "10%"),
]


def section_head(flow, title):
    flow.gap(0.039)
    flow.ax.text(L, flow.y, title, family=HEAD, weight="bold", size=11.5,
                 color=INK, ha="left", va="baseline")
    flow.gap(0.009)
    flow.ax.plot([L, R], [flow.y, flow.y], color=RULE_C, lw=0.7,
                 solid_capstyle="butt")
    flow.gap(0.001)


def main():
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.canvas.draw()

    ax.add_patch(Rectangle((0, 0.940), 1, 0.060, facecolor=BRAND,
                           edgecolor="none"))
    if LOGO_PATH.exists():
        img = imread(str(LOGO_PATH))
        h = 0.038
        w = h * (img.shape[1] / img.shape[0]) * (PAGE_H / PAGE_W)
        ax.imshow(img, extent=(L, L + w, 0.951, 0.951 + h), zorder=3,
                  aspect="auto")
    ax.text(R, 0.978, "Cleaner Greener Future", family=HEAD, weight="bold",
            size=10, color=PAPER, ha="right", va="center")
    ax.text(R, 0.958, "with NEA Solar", family=HEAD, size=8, color="#BFD8F0",
            ha="right", va="center")

    flow = Flow(fig, ax, 0.930)

    flow.text("What Solar Looks Like on a Poultry Farm Here", HEAD, 19,
              weight="bold", leading=1.25, gap_after=0.008)
    flow.text("Figures from metered usage on 76 broiler farms in northeast "
              "Arkansas. Not a projection.", SERIF, 10.2, color=MUTE,
              leading=1.4)

    # ----------------------------------------------------------------- table
    section_head(flow, "By farm size")

    xs = [L, L + 0.135, L + 0.250, L + 0.360, L + 0.500, L + 0.660, R]
    flow.gap(0.013)
    for i, head in enumerate(COLS):
        ax.text(xs[i], flow.y, head, family=MONO, size=6.4, color=MUTE,
                ha="right" if i == 6 else "left", va="baseline")

    for row in TABLE:
        flow.gap(0.030)
        for i, cell in enumerate(row):
            ax.text(xs[i], flow.y, cell, family=SERIF,
                    weight="bold" if i in (0, 5, 6) else "normal", size=10.4,
                    color=BRAND if i == 5 else INK,
                    ha="right" if i == 6 else "left", va="baseline")
        flow.gap(0.011)
        ax.plot([L, R], [flow.y, flow.y], color=RULE_C, lw=0.6)

    flow.gap(0.011)
    flow.text("Ground mount at $2.10 per watt installed, as pictured. Roof runs "
              "about 5% less where the trusses will carry it, and gets quoted "
              "alongside.", SERIF, 8.8, color=MUTE, leading=1.45)

    # ---------------------------------------------------------------- credit
    section_head(flow, "Where half the cost goes")

    flow.gap(0.013)
    for label, pct in CREDIT:
        ax.text(L, flow.y, label, family=SERIF, size=9.8, color=INK,
                ha="left", va="baseline")
        ax.text(L + 0.40, flow.y, pct, family=SERIF, size=9.8, color=INK,
                ha="right", va="baseline")
        flow.gap(0.026)
    ax.plot([L, L + 0.40], [flow.y + 0.012, flow.y + 0.012], color=INK, lw=0.9)
    ax.text(L, flow.y - 0.004, "Credit against project cost", family=SERIF,
            weight="bold", size=10.4, color=INK, ha="left", va="baseline")
    ax.text(L + 0.40, flow.y - 0.004, "50%", family=SERIF, weight="bold",
            size=10.4, color=BRAND, ha="right", va="baseline")
    flow.gap(0.008)

    flow.text("Systems under 1 megawatt take the full rate without the "
              "prevailing wage paperwork, and most of what is left after the "
              "credit can be depreciated in year one. Both need tax liability "
              "to offset. The system has to be running by December 31, 2027, a "
              "federal date and not a sales deadline.", SERIF, 9.4, leading=1.48)

    # --------------------------------------------------------------- honesty
    section_head(flow, "Two things you should hear from us")

    flow.text("USDA halted REAP grant awards on March 31, 2026 pending new "
              "rules. There is no grant line on this sheet because there is no "
              "grant to show you right now.", SERIF, 9.4, leading=1.48,
              gap_after=0.010)
    flow.text("Arkansas pays avoided cost for power you send back, not the "
              "retail rate, since Act 278. That is why these systems are sized "
              "to what the houses draw in daylight rather than to your annual "
              "bill.", SERIF, 9.4, leading=1.48)

    print(f"content ends at y={flow.y:.3f}")

    # ---------------------------------------------------------------- photos
    have = [p for p in PHOTO_GROUND_WIDE if p.exists()]
    if have:
        flow.gap(0.016)
        gap = 0.014
        w = ((R - L) - gap * (len(have) - 1)) / len(have)
        height = w * (PAGE_W / PAGE_H) / 4.6
        top = flow.y
        for i, path in enumerate(have):
            left = L + i * (w + gap)
            ax.imshow(imread(str(path)),
                      extent=(left, left + w, top - height, top),
                      aspect="auto", zorder=2)
        flow.gap(height + 0.011)
        ax.text(L, flow.y, "Ground mount installations completed by NEA Solar.",
                family=MONO, size=6.4, color=MUTE, ha="left", va="baseline")

    rule_y = flow.y - 0.014
    ax.plot([L, R], [rule_y, rule_y], color=RULE_C, lw=0.7)
    print(f"footer rule at y={rule_y:.3f}")

    # ---------------------------------------------------------------- footer
    foot = Flow(fig, ax, rule_y - 0.012)
    foot.text("Email twelve months of billing history to " + EMAIL, HEAD,
              12.5, weight="bold", color=BRAND, gap_after=0.006)
    foot.text("Photos of the bills are fine. We will replace every figure here "
              "with your own. No charge, no obligation.", SERIF, 9.6,
              leading=1.45, gap_after=0.009)
    foot.text(f"Cleaner Greener Future, with NEA Solar   ·   {PHONE}   ·   "
              f"{WEB}", HEAD, 8.2, color=MUTE, gap_after=0.003)
    foot.text(ADDRESS, HEAD, 8.2, color=MUTE)
    print(f"footer ends at y={foot.y:.3f}")

    out_pdf = Path("out/cgf_solar_sheet.pdf")
    fig.savefig(out_pdf, facecolor=PAPER, dpi=300)
    fig.savefig("out/cgf_solar_sheet.png", facecolor=PAPER, dpi=200)
    plt.close(fig)
    print(f"wrote {out_pdf}")


if __name__ == "__main__":
    main()
