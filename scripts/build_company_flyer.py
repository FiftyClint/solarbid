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
    ACCENT, BODY, BRAND, DISPLAY, INK, L, MONO, MUTE, PAGE_H, PAGE_W, PANEL, PAPER,
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

# The hook has to name equipment the reader is actually going to buy, or it is
# an assumption dressed as a fact. For a contract grower that is not solar. It
# is the integrator-specified kit on a replacement cycle: exhaust fans and
# structural components run 10-15 years, controls turn over faster.
VERTICALS = {
    "poultry": {
        "hook": ("YOUR POWER BILL WENT UP", "6.5% LAST YEAR."),
        "offer": "WE READ THE BILL AND FIND WHERE TO STOP IT.",
        "offer_sub": ("No charge for the look. Arkansas rates rose 6.5% in 2025 "
                      "and the next increase is already filed."),
        "agitate_head": "AND THE PART THAT IS RISING IS NOT THE PART YOU WATCH",
        "agitate": ("Arkansas co-ops are adding demand charges to general "
                    "service. One just put $1 to $2 per kW on the bill, charged "
                    "on your highest\nfew hours rather than your usage. Broiler "
                    "farms here run a load factor near 0.35. You pay for a July "
                    "afternoon all year."),
        "cost_rows": [("Two houses", 38), ("Four houses", 74), ("Six houses", 115)],
        "equipment": ("Tunnel fans  ·  Cool cells  ·  Controllers  ·  Lighting  "
                      "·  Brooders  ·  Insulation  ·  Generators  ·  Solar  ·  "
                      "Storage"),
    },
    "general": {
        "hook": ("YOUR POWER BILL WENT UP", "6.5% LAST YEAR."),
        "offer": "WE READ THE BILL AND FIND WHERE TO STOP IT.",
        "offer_sub": ("No charge for the look. Arkansas rates rose 6.5% in 2025 "
                      "and the next increase is already filed."),
        "agitate_head": "AND THE PART THAT IS RISING IS NOT THE PART YOU WATCH",
        "agitate": ("Arkansas co-ops are adding demand charges to general "
                    "service. One just put $1 to $2 per kW on the bill, charged "
                    "on your highest\nfew hours rather than your usage. The lower "
                    "your load factor, the more of the bill is not power at all."),
        "cost_rows": [("50 kW peak", 50), ("100 kW peak", 100), ("200 kW peak", 200)],
        "equipment": ("Efficiency upgrades  ·  HVAC  ·  Refrigeration  ·  "
                      "Lighting  ·  Controls  ·  Solar  ·  Storage"),
    },
}


def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vertical", choices=sorted(VERTICALS), default="poultry")
    args = ap.parse_args()
    v = VERTICALS[args.vertical]

    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    masthead(ax, "ENERGY AND INCENTIVE SPECIALISTS")

    # ------------------------------------------------------------------ hook
    ax.text(L, 0.876, v["hook"][0], family=DISPLAY, weight="bold", size=38,
            color=INK, ha="left", va="center")
    ax.text(L, 0.826, v["hook"][1], family=DISPLAY, weight="bold", size=38,
            color=INK, ha="left", va="center")

    # ----------------------------------------------------------------- offer
    ax.text(L, 0.766, v["offer"], family=DISPLAY, weight="bold", size=31,
            color=BRAND, ha="left", va="center")
    ax.text(L, 0.734, v["offer_sub"], family=BODY, size=9.4, color=MUTE,
            ha="left", va="center")

    # -------------------------------------------------------------- agitate
    ax.add_patch(Rectangle((L, 0.556), R - L, 0.156, facecolor=PANEL,
                           edgecolor="none"))
    ax.text(L + 0.024, 0.694, v["agitate_head"], family=DISPLAY, weight="bold",
            size=15, color=INK, ha="left", va="center")
    ax.text(L + 0.024, 0.672, v["agitate"], family=BODY, size=8.8, color=MUTE,
            ha="left", va="top", linespacing=1.6)

    for i, (label, kw) in enumerate(v["cost_rows"]):
        x = L + 0.024 + i * 0.278
        ax.text(x, 0.616, label, family=MONO, size=6.0, color=MUTE,
                ha="left", va="center")
        ax.text(x, 0.594, f"${kw * 24:,}", family=DISPLAY, weight="bold",
                size=20, color=BRAND, ha="left", va="center")
    ax.text(L + 0.024, 0.570,
            "a year, at $2 per kW, before a single kilowatt-hour of actual power.",
            family=BODY, size=8.4, color=MUTE, ha="left", va="center")

    # ---------------------------------------------------------- the method
    ax.text(L, 0.540, "HOW WE WORK, IN THIS ORDER", family=DISPLAY,
            weight="bold", size=17, color=INK, ha="left", va="center")
    rule(ax, 0.525, lw=1.2, c=INK)

    for i, (num, head, body) in enumerate(METHOD):
        x = L + i * (R - L) / 4
        ax.text(x, 0.502, num, family=MONO, size=6.4, color=BRAND,
                ha="left", va="center")
        ax.text(x, 0.480, head, family=DISPLAY, weight="bold", size=13.5,
                color=INK, ha="left", va="center")
        ax.text(x, 0.460, body, family=BODY, size=8.4, color=MUTE,
                ha="left", va="top", linespacing=1.55)

    # -------------------------------------------------------------- the case
    ax.add_patch(Rectangle((L, 0.268), R - L, 0.124, facecolor=PANEL,
                           edgecolor="none"))
    ax.text(L + 0.024, 0.372, "ONE PROJECT", family=MONO, size=6.2,
            color=MUTE, ha="left", va="center")

    captured = CASE["grant"] + CASE["itc"]
    ax.text(L + 0.024, 0.334, f"${captured:,}", family=DISPLAY, weight="bold",
            size=44, color=BRAND, ha="left", va="center")
    ax.text(L + 0.024, 0.296,
            f"captured on a ${CASE['project']:,} project. ${CASE['grant']:,} "
            f"federal grant, ${CASE['itc']:,} tax credit. {CASE['client']}.",
            family=BODY, size=8.8, color=INK, ha="left", va="center")

    pct = captured / CASE["project"]
    ax.text(R - 0.024, 0.334, f"{pct:.0%}", family=DISPLAY, weight="bold",
            size=44, color=INK, ha="right", va="center")
    ax.text(R - 0.024, 0.296, "of the project cost", family=BODY, size=9.4,
            color=MUTE, ha="right", va="center")

    # ---------------------------------------------------------- what it fits
    ax.text(L, 0.240, "ON WHAT KIND OF WORK", family=MONO, size=6.2,
            color=MUTE, ha="left", va="center")
    ax.text(L, 0.218, v["equipment"], family=BODY, size=9.4, color=INK,
            ha="left", va="center")

    # ------------------------------------------------------------ the terms
    ax.add_patch(Rectangle((L, 0.120), R - L, 0.072, facecolor=INK,
                           edgecolor="none"))
    ax.text(L + 0.024, 0.168, "NO FEE UNLESS YOU COLLECT.", family=DISPLAY,
            weight="bold", size=21, color=ACCENT, ha="left", va="center")
    ax.text(L + 0.024, 0.140,
            "We are paid out of what we find. If we find nothing, you owe nothing.",
            family=BODY, size=9.0, color="#9FBBD4", ha="left", va="center")

    if PHOTO_TEAM.exists():
        ax.imshow(imread(str(PHOTO_TEAM)), extent=(R - 0.20, R, 0.120, 0.192),
                  aspect="auto", zorder=3)

    # ------------------------------------------------------------------ call
    callbar(ax, "SEND US TWELVE MONTHS OF BILLS.",
            "One call to your co-op. We tell you where your money is going, at no cost.")
    footer(ax)

    stem = "cgf_company" if args.vertical == "poultry" else f"cgf_company_{args.vertical}"
    out_pdf, out_png = Path(f"out/{stem}.pdf"), Path(f"out/{stem}.png")
    fig.savefig(out_pdf, facecolor=PAPER, dpi=300)
    fig.savefig(out_png, facecolor=PAPER, dpi=200)
    plt.close(fig)
    print("CONFIRM BEFORE PRINTING: case study figures and the $10M/300+ project "
          "track record come from a public listing, not the live site.")
    print(f"wrote {out_pdf} and {out_png}")


if __name__ == "__main__":
    main()
