#!/usr/bin/env python3
"""CGF company flyer. Who we are, deliberately not a solar pitch.

Solar is one line item here, not the subject. The subject is that a business is
going to spend money on equipment anyway, and most of them never find out who
else would have helped pay for it.

Track record figures come from a public listing of the CGF site, which the
network here could not reach directly. Confirm against the live site before
printing. They are marked in the console output.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib.patches import Rectangle

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from brand import (  # noqa: E402
    BODY, BRAND, DISPLAY, INK, L, MONO, MUTE, PAGE_H, PAGE_W, PANEL, PAPER,
    PHOTO_TEAM, R, callbar, footer, masthead, rule, slot,
)

# Public case study. Confirm before printing.
CASE = {
    "client": "Newell Coach",
    "project": 1_070_600,
    "grant": 535_800,
    "itc": 160_440,
}

# The order is the pitch. Rate and efficiency come before anyone talks about
# equipment, and neither requires the customer to buy anything, which is what
# separates CGF from a company selling boxes.
METHOD = [
    ("01", "RATE ANALYSIS",
     "We read your bill first.\nRate class and demand\ncharges."),
    ("02", "ENERGY EFFICIENCY",
     "Cut the load before you\ncover it. Lighting, controls,\nmotors, HVAC."),
    ("03", "INCENTIVE CAPTURE",
     "Tax credit and adders,\nMACRS, depreciation,\nfederal and state grants."),
    ("04", "DESIGN AND EXECUTION",
     "Specification and the\npaperwork that actually\ncollects it."),
]

EQUIPMENT = ("Efficiency upgrades  ·  HVAC  ·  Refrigeration  ·  Lighting  ·  "
             "Controls  ·  Solar  ·  Storage")


def main():
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    masthead(ax, "ENERGY AND INCENTIVE SPECIALISTS")

    # ------------------------------------------------------------------ hook
    ax.text(L, 0.882, "YOU ARE GOING TO BUY", family=DISPLAY, weight="bold",
            size=40, color=INK, ha="left", va="center")
    ax.text(L, 0.828, "THE EQUIPMENT ANYWAY.", family=DISPLAY, weight="bold",
            size=40, color=INK, ha="left", va="center")
    ax.text(L, 0.762, "WE FIND OUT WHO ELSE PAYS FOR IT.",
            family=DISPLAY, weight="bold", size=36, color=BRAND,
            ha="left", va="center")

    ax.text(L, 0.726,
            "CGF is not an equipment company. We work the energy and incentive "
            "side of a project:\nwhat you use, what you qualify for, and what it "
            "takes to actually collect it.",
            family=BODY, size=9.6, color=MUTE, ha="left", va="top",
            linespacing=1.6)

    # ---------------------------------------------------------- the method
    ax.text(L, 0.660, "HOW WE WORK, IN THIS ORDER", family=DISPLAY,
            weight="bold", size=17, color=INK, ha="left", va="center")
    rule(ax, 0.645, lw=1.2, c=INK)

    for i, (num, head, body) in enumerate(METHOD):
        x = L + i * (R - L) / 4
        ax.text(x, 0.622, num, family=MONO, size=6.4, color=BRAND,
                ha="left", va="center")
        ax.text(x, 0.600, head, family=DISPLAY, weight="bold", size=13.5,
                color=INK, ha="left", va="center")
        ax.text(x, 0.580, body, family=BODY, size=8.4, color=MUTE,
                ha="left", va="top", linespacing=1.55)

    ax.text(L, 0.516,
            "The first two cost you no capital and often do not involve buying "
            "anything at all. We would rather tell you\nthat than sell you equipment "
            "you did not need.",
            family=BODY, size=9.4, color=INK, ha="left", va="top",
            linespacing=1.6)

    # -------------------------------------------------------------- the case
    ax.add_patch(Rectangle((L, 0.312), R - L, 0.148, facecolor=PANEL,
                           edgecolor="none"))
    ax.text(L + 0.024, 0.438, "ONE PROJECT", family=MONO, size=6.2,
            color=MUTE, ha="left", va="center")

    captured = CASE["grant"] + CASE["itc"]
    ax.text(L + 0.024, 0.396, f"${captured:,}", family=DISPLAY, weight="bold",
            size=50, color=BRAND, ha="left", va="center")
    ax.text(L + 0.024, 0.352,
            f"captured on a ${CASE['project']:,} energy project.",
            family=BODY, size=10.5, color=INK, ha="left", va="center")
    ax.text(L + 0.024, 0.330,
            f"${CASE['grant']:,} federal grant and ${CASE['itc']:,} investment "
            f"tax credit. {CASE['client']}.",
            family=BODY, size=8.6, color=MUTE, ha="left", va="center")

    pct = captured / CASE["project"]
    ax.text(R - 0.024, 0.396, f"{pct:.0%}", family=DISPLAY, weight="bold",
            size=50, color=INK, ha="right", va="center")
    ax.text(R - 0.024, 0.352, "of the project cost", family=BODY, size=10.5,
            color=MUTE, ha="right", va="center")

    # ---------------------------------------------------------- what it fits
    ax.text(L, 0.282, "ON WHAT KIND OF PROJECT", family=MONO, size=6.2,
            color=MUTE, ha="left", va="center")
    ax.text(L, 0.258, EQUIPMENT, family=BODY, size=10.0, color=INK,
            ha="left", va="center")

    # ------------------------------------------------------------ the terms
    ax.add_patch(Rectangle((L, 0.150), R - L, 0.072, facecolor=INK,
                           edgecolor="none"))
    ax.text(L + 0.024, 0.198, "NO FEE UNLESS YOU COLLECT.", family=DISPLAY,
            weight="bold", size=21, color=PAPER, ha="left", va="center")
    ax.text(L + 0.024, 0.170,
            "We are paid out of what we find. If we find nothing, you owe nothing.",
            family=BODY, size=9.0, color="#B9B0A4", ha="left", va="center")

    if PHOTO_TEAM.exists():
        ax.imshow(imread(str(PHOTO_TEAM)), extent=(R - 0.20, R, 0.150, 0.222),
                  aspect="auto", zorder=3)

    # ------------------------------------------------------------------ call
    callbar(ax, "LET US LOOK AT YOUR NEXT PROJECT.",
            "Tell us what you are planning. We come back with what it qualifies for.")
    footer(ax)

    out_pdf, out_png = Path("out/cgf_company.pdf"), Path("out/cgf_company.png")
    fig.savefig(out_pdf, facecolor=PAPER, dpi=300)
    fig.savefig(out_png, facecolor=PAPER, dpi=200)
    plt.close(fig)
    print("CONFIRM BEFORE PRINTING: case study figures and the $10M/300+ project "
          "track record come from a public listing, not the live site.")
    print(f"wrote {out_pdf} and {out_png}")


if __name__ == "__main__":
    main()
