#!/usr/bin/env python3
"""CGF solar flyer, sized to the reader's farm. Goes out with the company
flyer and a handwritten note.

Every figure comes from metered usage across 115 broiler accounts in the Peco
footprint, priced at $2.00/W roof with the 50% credit and bonus depreciation.

Palette, type and furniture come from brand.py, so all three pieces move
together when the real brand colors land.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.image import imread  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from brand import (  # noqa: E402
    ACCENT, BODY, BRAND, DISPLAY, INK, L, MONO, MUTE, PAGE_H, PAGE_W, PAPER,
    PHOTO_GROUND, PHOTO_ROOF, R, callbar, footer, masthead, photo_band,
    rule, slot,
)

# Metered medians across 115 broiler accounts, priced at $2.10/W GROUND, with
# the 50% credit and 100% bonus depreciation at a 30% marginal rate.
#
# Ground, not roof, because the photographs above are ground mounts. Pricing a
# roof table under ground-mount pictures is the kind of mismatch a grower
# notices. Roof comes in about 5% cheaper and lands at 3.9 years, which is why
# the headline says about four rather than under four.
TABLE = [
    ("2 houses", "125,760", "75 kW", "$157,500", "$10,500", "4.1 yrs"),
    ("4 houses", "194,880", "115 kW", "$241,500", "$16,200", "4.1 yrs"),
    ("6 houses", "343,680", "205 kW", "$430,500", "$28,700", "4.1 yrs"),
]


def main():
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    masthead(ax, "ENERGY AND INCENTIVE SPECIALISTS")

    # ------------------------------------------------------------------ hook
    ax.text(L, 0.884, "FOUR-HOUSE FARM.", family=DISPLAY, weight="bold",
            size=42, color=INK, ha="left", va="center")
    ax.text(L, 0.810, "$16,000 A YEAR.", family=DISPLAY, weight="bold",
            size=58, color=BRAND, ha="left", va="center")
    ax.text(L, 0.746, "PAID BACK IN ABOUT FOUR YEARS.", family=DISPLAY,
            weight="bold", size=31, color=INK, ha="left", va="center")

    ax.text(L, 0.712,
            "Figures from metered usage on 115 broiler farms in this area. Not a projection.",
            family=BODY, size=8.2, color=MUTE, ha="left", va="center")

    # ----------------------------------------------------------------- photo
    shown = photo_band(ax, L, R, 0.505, 0.690, [PHOTO_ROOF] + PHOTO_GROUND,
                       "PHOTOGRAPHS", "real installs, landscape crop")

    # ----------------------------------------------------------------- table
    ax.text(L, 0.470, "WHAT IT LOOKS LIKE BY FARM SIZE", family=DISPLAY,
            weight="bold", size=17, color=INK, ha="left", va="center")
    rule(ax, 0.455, lw=1.2, c=INK)

    cols = [L, L + 0.175, L + 0.315, L + 0.455, L + 0.625, R]
    heads = ["", "POWER USED", "SYSTEM", "INSTALLED", "SAVES", "PAYBACK"]
    for i, head in enumerate(heads):
        ha = "right" if i == 5 else "left"
        ax.text(cols[i], 0.438, head, family=MONO, size=5.9, color=MUTE,
                ha=ha, va="center")

    y = 0.410
    for row in TABLE:
        for i, cell in enumerate(row):
            ha = "right" if i == 5 else "left"
            is_key = i in (4, 5)
            ax.text(cols[i], y, cell,
                    family=DISPLAY if is_key or i == 0 else BODY,
                    weight="bold" if is_key or i == 0 else "normal",
                    size=15 if is_key else (13 if i == 0 else 10.5),
                    color=BRAND if i == 4 else INK, ha=ha, va="center")
        y -= 0.040
        rule(ax, y + 0.018)

    ax.text(L, 0.294,
            "Ground mount at $2.10 a watt, as pictured. Roof runs about 5% less "
            "where the trusses allow, and is quoted alongside.",
            family=BODY, size=8.0, color=MUTE, ha="left", va="center")

    # ----------------------------------------------------------------- proof
    rule(ax, 0.272)
    points = [
        ("HALF THE COST IS FEDERAL",
         "30% credit, plus 10% domestic content\nand 10% energy community."),
        ("YOUR COUNTY QUALIFIES",
         "Randolph, Clay, Lawrence, Greene,\nIndependence, Izard, Sharp, Fulton,\nJackson and Mississippi."),
        ("WE READ THE BILL FIRST",
         "Rate class and demand charges cost\nyou nothing to fix."),
    ]
    for i, (head, body) in enumerate(points):
        x = L + i * (R - L) / 3
        ax.text(x, 0.250, head, family=DISPLAY, weight="bold", size=13.5,
                color=INK, ha="left", va="center")
        ax.text(x, 0.232, body, family=BODY, size=8.2, color=MUTE,
                ha="left", va="top", linespacing=1.5)

    # -------------------------------------------------------------- deadline
    ax.add_patch(Rectangle((L, 0.116), R - L, 0.030, facecolor=INK,
                           edgecolor="none"))
    ax.text(L + 0.016, 0.131, "THE CREDIT REQUIRES YOUR SYSTEM RUNNING BY 12.31.2027",
            family=DISPLAY, weight="bold", size=15, color=ACCENT,
            ha="left", va="center")
    ax.text(R - 0.016, 0.131, "THAT IS A FEDERAL DATE, NOT OURS",
            family=MONO, size=6.2, color="#9FBBD4", ha="right", va="center")

    callbar(ax, "SEND US TWELVE MONTHS OF BILLS.",
            "One call to your co-op. We come back with your real number, at no cost.")
    footer(ax)

    out_pdf, out_png = Path("out/cgf_ad.pdf"), Path("out/cgf_ad.png")
    fig.savefig(out_pdf, facecolor=PAPER, dpi=300)
    fig.savefig(out_png, facecolor=PAPER, dpi=200)
    plt.close(fig)
    if not shown:
        print("no photos found in assets/; placeholder slot rendered")
    else:
        print(f"{shown} photo(s) placed")
    print(f"wrote {out_pdf} and {out_png}")


if __name__ == "__main__":
    main()
