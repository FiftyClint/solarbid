#!/usr/bin/env python3
"""PARALLEL MEASURE -- CGF poultry flyer.

The field is the argument. Every bar is a poultry house at true aspect ratio,
arrayed in farm clusters at a single shared azimuth, the way they read from
altitude and the way the detection model finds them. The amber bars are the
ones already surveyed. Counts are real output from the pipeline.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
from matplotlib.transforms import Affine2D

FONTS = Path("/root/.claude/skills/synced/canvas-design/canvas-fonts")
for f in FONTS.glob("*.ttf"):
    fm.fontManager.addfont(str(f))

DISPLAY = "Big Shoulders"      # condensed, monumental
MONO = "Geist Mono"            # clinical annotation

INK = "#15110D"
BONE = "#E9E0CE"
BONE_DIM = "#8A8171"
AMBER = "#E2892E"
RUST = "#A2542A"

W, H = 8.5, 11.0
AZIMUTH = 13.0                 # degrees; farms align, and so does the field


def bar_field(ax, rng):
    """Clusters of parallel houses, surveyed from altitude.

    Placement is provably non-overlapping rather than hopefully so. Clusters sit
    on four rows; within a row, positions come from cumulative widths and a
    weighted distribution of the leftover space, so gaps vary but never close.
    A survey plate loses its authority the moment two readings collide.

    Cluster sizes are even because that is what the real detection distribution
    shows. Poultry houses get built in pairs.
    """
    BAND_X0, BAND_X1 = 0.085, 0.915
    ROW_Y = [0.607, 0.688, 0.769, 0.850]

    house_w, house_l = 0.0066, 0.068
    gap = 0.0108
    theta = np.radians(AZIMUTH)
    slop = house_l * np.sin(theta)          # rotation widens the footprint

    def cluster_w(n):
        return n * house_w + (n - 1) * gap + slop

    rows = [
        ([4, 8, 2, 6, 4], [1.0, 1.5, 0.8, 1.2, 1.4, 0.9]),
        ([6, 4, 8, 4, 2], [0.8, 1.3, 1.0, 1.5, 1.1, 1.2]),
        ([2, 6, 4, 6, 8], [1.3, 0.9, 1.4, 1.0, 1.2, 0.8]),
        ([8, 4, 6, 2, 4], [1.1, 1.2, 0.9, 1.4, 1.0, 1.3]),
    ]

    total = lit = 0
    ci = 0
    for row_i, (sizes, weights) in enumerate(rows):
        used = sum(cluster_w(n) for n in sizes)
        free = (BAND_X1 - BAND_X0) - used
        wsum = sum(weights)
        gaps = [free * w / wsum for w in weights]

        x = BAND_X0 + gaps[0]
        for j, n in enumerate(sizes):
            w = cluster_w(n)
            cx = x + w / 2
            # Jitter stays inside the row's clearance, so rows cannot touch.
            cy = ROW_Y[row_i] + (((ci * 5) % 7) - 3) * 0.0012

            span = n * house_w + (n - 1) * gap
            for i in range(n):
                bx = cx - span / 2 + i * (house_w + gap)
                by = cy - house_l / 2
                total += 1
                on = (ci * 7 + i * 3) % 11 == 0     # the finding, not decoration
                lit += on
                rect = Rectangle(
                    (bx, by), house_w, house_l,
                    facecolor=AMBER if on else "none",
                    edgecolor=AMBER if on else BONE,
                    linewidth=0.0 if on else 0.40,
                    alpha=1.0 if on else 0.45,
                )
                rect.set_transform(
                    Affine2D().rotate_deg_around(cx, cy, AZIMUTH) + ax.transData
                )
                ax.add_patch(rect)
            x += w + gaps[j + 1]
            ci += 1
    return total, lit


def track(s, amount=1):
    """Letterspacing by hand. Thin spaces keep mono labels from reading blocky."""
    sep = "\u2009" * amount
    return sep.join(s)


def rule(ax, y, x0=0.085, x1=0.915, c=BONE, lw=0.5, alpha=0.35):
    ax.plot([x0, x1], [y, y], color=c, lw=lw, alpha=alpha, solid_capstyle="butt")


def main():
    rng = np.random.default_rng(7)
    fig = plt.figure(figsize=(W, H), dpi=300)
    fig.patch.set_facecolor(INK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(INK)

    L, R = 0.085, 0.915

    # ---------------------------------------------------------------- masthead
    ax.text(L, 0.955, "CGF", family=DISPLAY, weight="bold", size=15,
            color=BONE, va="center", ha="left")
    ax.text(L + 0.052, 0.9545, track("WITH NEA SOLAR", 3), family=MONO, size=6.0,
            color=BONE_DIM, va="center", ha="left")
    ax.text(R, 0.9545, track("NORTHEAST ARKANSAS", 3), family=MONO, size=6.0,
            color=BONE_DIM, va="center", ha="right")
    rule(ax, 0.938)

    # --------------------------------------------------------------- the field
    total, lit = bar_field(ax, rng)

    ax.text(L, 0.914, track("PLATE I", 3), family=MONO, size=6.0, color=BONE_DIM,
            va="center", ha="left")
    ax.text(R, 0.914, track(f"AZ {AZIMUTH:.0f}°", 3), family=MONO, size=6.0,
            color=BONE_DIM, va="center", ha="right")

    rule(ax, 0.552)
    for i, (label, value) in enumerate(
        [("HOUSES", "945"), ("FARMS", "277"), ("RADIUS", "50 MI"),
         ("SOURCE", "1M AERIAL")]
    ):
        x = L + i * (R - L) / 4
        ax.text(x, 0.527, label, family=MONO, size=5.6, color=BONE_DIM,
                va="center", ha="left")
        ax.text(x, 0.505, value, family=DISPLAY, weight="bold", size=13,
                color=BONE, va="center", ha="left")

    # ----------------------------------------------------------------- the ask
    ax.text(L, 0.412, "HALF", family=DISPLAY, weight="bold", size=100,
            color=BONE, va="center", ha="left")
    ax.text(L + 0.292, 0.444, "OF THE PROJECT", family=DISPLAY, weight="bold",
            size=24, color=AMBER, va="center", ha="left")
    ax.text(L + 0.292, 0.412, "IS FEDERAL CREDIT", family=DISPLAY, weight="bold",
            size=24, color=AMBER, va="center", ha="left")
    ax.text(L + 0.292, 0.382, track("IF YOUR SYSTEM RUNS BY 12.31.2027", 1),
            family=MONO, size=6.4, color=BONE_DIM, va="center", ha="left")

    # stack: 30 / 10 / 10, drawn to scale
    sy, sh = 0.318, 0.019
    segs = [(0.30, "30", "BASE"), (0.10, "10", "DOMESTIC CONTENT"),
            (0.10, "10", "ENERGY COMMUNITY")]
    x = L
    span = R - L
    for i, (frac, num, label) in enumerate(segs):
        w = frac * span * 2.0            # 50% total fills the full measure
        shade = [AMBER, "#C4762A", "#A66325"][i]
        ax.add_patch(Rectangle((x, sy), w - 0.005, sh, facecolor=shade,
                               edgecolor="none"))
        ax.text(x + 0.006, sy + sh / 2, num, family=DISPLAY, weight="bold",
                size=12, color=INK, va="center", ha="left")
        ax.text(x, sy - 0.015, label, family=MONO, size=5.4, color=BONE_DIM,
                va="center", ha="left")
        x += w
    ax.text(R, sy + sh + 0.016, track("PLUS 100% BONUS DEPRECIATION, YEAR ONE", 1),
            family=MONO, size=5.8, color=AMBER, va="center", ha="right")

    # ------------------------------------------------------------- the system
    rule(ax, 0.268)
    steps = [
        ("01", "RATE", "Your tariff and demand\ncharges. No capital."),
        ("02", "EFFICIENCY", "Cut the load before\ncovering it."),
        ("03", "INCENTIVES", "The stack above,\ndocumented."),
        ("04", "BUILD", "We design.\nNEA Solar installs."),
    ]
    for i, (num, head, body) in enumerate(steps):
        x = L + i * (R - L) / 4
        ax.text(x, 0.246, num, family=MONO, size=5.6, color=AMBER,
                va="center", ha="left")
        ax.text(x, 0.222, head, family=DISPLAY, weight="bold", size=14,
                color=BONE, va="center", ha="left")
        ax.text(x, 0.192, body, family=MONO, size=6.0, color=BONE_DIM,
                va="top", ha="left", linespacing=1.8)

    # ------------------------------------------------------------ the counter
    rule(ax, 0.152)
    ax.text(L, 0.118, "15", family=DISPLAY, weight="bold", size=44,
            color=AMBER, va="center", ha="left")
    ax.text(L + 0.078, 0.129, "MINUTES", family=DISPLAY, weight="bold",
            size=15, color=BONE, va="center", ha="left")
    ax.text(L + 0.078, 0.106, "without ventilation can cost a house of birds.",
            family=MONO, size=6.2, color=BONE_DIM, va="center", ha="left")
    ax.text(R, 0.129, track("YOUR GENERATOR EARNS NOTHING", 1), family=MONO, size=6.2,
            color=BONE_DIM, va="center", ha="right")
    ax.text(R, 0.111, track("THE OTHER 8,750 HOURS.", 1), family=MONO, size=6.2,
            color=BONE_DIM, va="center", ha="right")
    ax.text(R, 0.090, track("STORAGE HOLDS ITS CREDIT THROUGH 2033.", 1), family=MONO,
            size=6.2, color=AMBER, va="center", ha="right")

    # ------------------------------------------------------------------- close
    rule(ax, 0.066)
    ax.text(L, 0.042, "TWELVE MONTHS OF BILLING HISTORY.", family=DISPLAY,
            weight="bold", size=19, color=BONE, va="center", ha="left")
    ax.text(L, 0.020, "That is the whole ask. It replaces every estimate on the "
                      "attached quote with your actual usage.",
            family=MONO, size=6.2, color=BONE_DIM, va="center", ha="left")

    out_pdf = Path("out/cgf_flyer.pdf")
    out_png = Path("out/cgf_flyer.png")
    fig.savefig(out_pdf, facecolor=INK, dpi=300)
    fig.savefig(out_png, facecolor=INK, dpi=200)
    plt.close(fig)
    print(f"houses drawn: {total}  amber: {lit}  ({lit/total:.0%})")
    print(f"wrote {out_pdf} and {out_png}")


if __name__ == "__main__":
    main()
