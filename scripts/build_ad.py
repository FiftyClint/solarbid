#!/usr/bin/env python3
"""CGF farm trade ad. Light stock, dollars first, one phone number.

Built to read like something in Poultry Times, not a design annual. Every
figure comes from metered usage across 115 broiler accounts in the Peco
footprint, priced at $2.00/W roof with the 50% credit and bonus depreciation.

ASSET SLOTS are marked below. Drop in the real logo, photo and brand colors and
re-run; nothing else needs to change.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.image import imread
from matplotlib.patches import FancyBboxPatch, Rectangle

FONTS = Path("/root/.claude/skills/synced/canvas-design/canvas-fonts")
for f in FONTS.glob("*.ttf"):
    fm.fontManager.addfont(str(f))

DISPLAY = "Big Shoulders"
BODY = "Work Sans"
MONO = "Geist Mono"

# ---------------------------------------------------------------- ASSET SLOTS
# Replace with the real brand colors.
BRAND = "#9E2B20"          # primary
BRAND_DK = "#6E1E16"
PAPER = "#F7F3EA"
INK = "#1A1713"
MUTE = "#6B635A"
RULE = "#CFC6B6"

LOGO_PATH = Path("assets/cgf_logo.png")      # drop the logo here
PHOTO_PATH = Path("assets/poultry_roof.jpg")  # roof install photo here
PHONE = "(000) 000-0000"                      # real number here

W, H = 8.5, 11.0
L, R = 0.075, 0.925

# Metered medians across 115 broiler accounts, priced at $2.00/W roof,
# 50% ITC and 100% bonus depreciation at a 30% marginal rate.
TABLE = [
    ("2 houses", "125,760", "75 kW", "$150,000", "$10,500", "3.9 yrs"),
    ("4 houses", "194,880", "115 kW", "$230,000", "$16,200", "3.9 yrs"),
    ("6 houses", "343,680", "205 kW", "$410,000", "$28,700", "3.9 yrs"),
]


def slot(ax, x0, y0, x1, y1, label, sub=""):
    """A placeholder that looks deliberate rather than broken."""
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#EDE7DA",
                           edgecolor=RULE, linewidth=0.8, linestyle=(0, (4, 3))))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + (0.008 if sub else 0), label,
            family=MONO, size=7.0, color=MUTE, ha="center", va="center")
    if sub:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 - 0.014, sub, family=MONO,
                size=5.8, color=MUTE, ha="center", va="center")


def rule(ax, y, x0=L, x1=R, c=RULE, lw=0.8):
    ax.plot([x0, x1], [y, y], color=c, lw=lw, solid_capstyle="butt", zorder=1)


def main():
    fig = plt.figure(figsize=(W, H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # ------------------------------------------------------------- identity bar
    if LOGO_PATH.exists():
        ax.imshow(imread(str(LOGO_PATH)), extent=(L, L + 0.16, 0.938, 0.972),
                  aspect="auto", zorder=3)
    else:
        slot(ax, L, 0.936, L + 0.16, 0.974, "CGF LOGO")

    ax.text(R, 0.966, PHONE, family=DISPLAY, weight="bold", size=21,
            color=BRAND, ha="right", va="center")
    ax.text(R, 0.941, "CGF  with  NEA SOLAR", family=MONO, size=6.4,
            color=MUTE, ha="right", va="center")
    rule(ax, 0.921, lw=1.6, c=INK)

    # ------------------------------------------------------------------ hook
    ax.text(L, 0.884, "FOUR-HOUSE FARM.", family=DISPLAY, weight="bold",
            size=42, color=INK, ha="left", va="center")
    ax.text(L, 0.810, "$16,000 A YEAR.", family=DISPLAY, weight="bold",
            size=58, color=BRAND, ha="left", va="center")
    ax.text(L, 0.746, "PAID BACK IN UNDER FOUR YEARS.", family=DISPLAY,
            weight="bold", size=31, color=INK, ha="left", va="center")

    ax.text(L, 0.712,
            "Figures from metered usage on 115 broiler farms in this area. Not a projection.",
            family=BODY, size=8.2, color=MUTE, ha="left", va="center")

    # ----------------------------------------------------------------- photo
    if PHOTO_PATH.exists():
        ax.imshow(imread(str(PHOTO_PATH)), extent=(L, R, 0.505, 0.690),
                  aspect="auto", zorder=2)
    else:
        slot(ax, L, 0.505, R, 0.690, "PHOTOGRAPH",
             "poultry house with roof array, landscape, 3:1")

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

    ax.text(L, 0.294, "Roof mount at $2.00 a watt. Ground mount quoted alongside.",
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
            family=DISPLAY, weight="bold", size=15, color=PAPER,
            ha="left", va="center")
    ax.text(R - 0.016, 0.131, "THAT IS A FEDERAL DATE, NOT OURS",
            family=MONO, size=6.2, color="#9A9186", ha="right", va="center")

    # ------------------------------------------------------------------- call
    ax.add_patch(FancyBboxPatch((L, 0.028), R - L, 0.072,
                                boxstyle="round,pad=0,rounding_size=0.006",
                                facecolor=BRAND, edgecolor="none"))
    ax.text(L + 0.024, 0.079, "SEND US TWELVE MONTHS OF BILLS.",
            family=DISPLAY, weight="bold", size=23, color=PAPER,
            ha="left", va="center")
    ax.text(L + 0.024, 0.051,
            "One call to your co-op. We come back with your real number, at no cost.",
            family=BODY, size=9.0, color="#F0D9D5", ha="left", va="center")
    ax.text(R - 0.024, 0.064, PHONE, family=DISPLAY, weight="bold", size=26,
            color=PAPER, ha="right", va="center")

    out_pdf, out_png = Path("out/cgf_ad.pdf"), Path("out/cgf_ad.png")
    fig.savefig(out_pdf, facecolor=PAPER, dpi=300)
    fig.savefig(out_png, facecolor=PAPER, dpi=200)
    plt.close(fig)
    missing = [p.name for p in (LOGO_PATH, PHOTO_PATH) if not p.exists()]
    if missing:
        print(f"placeholder slots still open: {', '.join(missing)}")
    print(f"wrote {out_pdf} and {out_png}")


if __name__ == "__main__":
    main()
