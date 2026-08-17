#!/usr/bin/env python3
"""What CGF does, in the informational register.

The pitch in Clint's words: we analyze bills for errors, we find ways to
reduce consumption, we try to find money to pay for those upgrades, we help
navigate the red tape to capture the incentives, and we help on implementation.

Order matters and is the argument. The first two steps cost the farm no capital
and can end with us telling him there is no project worth doing. The last step
hands off to a local contractor rather than pretending we swing hammers.

Solar is not the subject here. It shows up once, at the end, as the handoff to
the companion sheet.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.image import imread  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from brand import (  # noqa: E402
    ADDRESS, BRAND, EMAIL, Flow, INK, L, LOGO_PATH, MUTE, PAGE_H, PAGE_W,
    PANEL, PAPER, PHONE, R, RULE_C, WEB,
)

HEAD = "Work Sans"
SERIF = "IBM Plex Serif"
MONO = "Geist Mono"

# Public case study. Confirm against the live site before printing.
CASE = {"client": "Newell Coach", "project": 1_070_600,
        "grant": 535_800, "itc": 160_440}

STEPS = [
    ("1", "We analyze your bills for errors.",
     "Twelve months of billing, read line by line. Wrong rate class for how the "
     "farm actually runs. Meter multipliers applied wrong. Demand billed off a "
     "bad read and ratcheted forward for a year. Sales tax charged on power a "
     "farm may be exempt from. What we find here is money back with no capital "
     "spent and nothing bought."),
    ("2", "We find ways to reduce what you use.",
     "The same analysis shows where the consumption goes. On a poultry farm "
     "most of it is ventilation, so fans, controls and insulation come first. "
     "Every kilowatt-hour you stop using is one you never have to generate or "
     "pay for again."),
    ("3", "We find money to pay for those upgrades.",
     "Federal tax credits and their adders. Depreciation. Federal and state "
     "grant programs. Utility programs. Which apply depends on the work, where "
     "the farm sits and what the calendar says, and it changes often."),
    ("4", "We navigate the red tape to capture it.",
     "This is where most of the money gets lost. The programs exist, but "
     "collecting means deadlines, documentation, sourcing thresholds and "
     "filings that have to be right the first time. Qualifying for an "
     "incentive and receiving it are two different jobs."),
    ("5", "We help with implementation.",
     "For implementation in your area we use a local, experienced solar "
     "contractor, NEA Solar. They are close enough to answer a service call in "
     "July. We stay on the analysis, the design and the incentive work."),
]


def section_head(flow, number, title):
    flow.gap(0.032)
    y = flow.y
    flow.ax.text(L, y, number, family=MONO, size=7.0, color=BRAND,
                 ha="left", va="baseline")
    flow.ax.text(L + 0.030, y, title, family=HEAD, weight="bold", size=11.5,
                 color=INK, ha="left", va="baseline")
    flow.gap(0.009)
    flow.ax.plot([L, R], [flow.y, flow.y], color=RULE_C, lw=0.7,
                 solid_capstyle="butt")
    flow.gap(0.001)


def new_page():
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
    ax.text(R, 0.958, "Energy and incentive specialists", family=HEAD, size=8,
            color="#BFD8F0", ha="right", va="center")
    return fig, ax


def build():
    """Return the figure. Page 1 of the mailer, and printable on its own."""
    fig, ax = new_page()
    flow = Flow(fig, ax, 0.930)

    flow.text("How We Cut What a Farm Spends on Power", HEAD, 19,
              weight="bold", leading=1.25, gap_after=0.008)
    flow.text("Five things, in this order. The first two cost you no capital, "
              "and sometimes end with us saying there is no project worth doing.",
              SERIF, 10.2, color=MUTE, leading=1.4, gap_after=0.004)
    flow.text("Cleaner Greener Future is not an equipment company. We work the "
              "energy and incentive side.", MONO, 6.6, color=MUTE,
              gap_after=0.008)

    for number, title, body in STEPS:
        section_head(flow, number, title)
        flow.text(body, SERIF, 9.5, leading=1.48, gap_after=0.006)

    # ------------------------------------------------------------ the terms
    # Draw the text first, then put the panel behind it at zorder 0, so the box
    # is sized by its contents instead of by a hardcoded height that stops
    # being right the moment the copy changes.
    flow.gap(0.016)
    box_top = flow.y
    pad = 0.018
    inner = Flow(fig, ax, box_top - pad, x0=L + 0.020, x1=R - 0.020)
    inner.text("No fee unless you collect.", HEAD, 11, weight="bold",
               color=INK, gap_after=0.006)
    inner.text("We are paid out of what we find. Find nothing, owe nothing. On "
               f"one recent project we captured ${CASE['grant'] + CASE['itc']:,} "
               f"of a ${CASE['project']:,} job, 65% of its cost.",
               SERIF, 9.2, color=INK, leading=1.45)
    box_bottom = inner.y - pad
    ax.add_patch(Rectangle((L, box_bottom), R - L, box_top - box_bottom,
                           facecolor=PANEL, edgecolor="none", zorder=0))
    flow.y = box_bottom
    flow.gap(0.010)

    # ---------------------------------------------------------- the handoff
    section_head(flow, "→", "Here is what that might look like on your farm")
    flow.text("The back of this page runs the numbers at three, four, and five "
              "to six houses: cost, credit, savings and payback. Those figures "
              "come from metered usage on 76 broiler farms around here.",
              SERIF, 9.5, leading=1.48)

    print(f"content ends at y={flow.y:.3f}")

    # ---------------------------------------------------------------- footer
    ax.plot([L, R], [0.062, 0.062], color=RULE_C, lw=0.7)
    ax.text(L, 0.040, f"Send twelve months of billing history to {EMAIL} and we "
            "will start at step one.", family=SERIF, size=9.6, color=INK,
            ha="left", va="center")
    ax.text(L, 0.020, f"Cleaner Greener Future   ·   {PHONE}   ·   {WEB}   ·   "
            f"{ADDRESS}", family=HEAD, size=8.6, color=MUTE, ha="left",
            va="center")

    return fig


def main():
    fig = build()
    fig.savefig("out/cgf_how_we_work.png", facecolor=PAPER, dpi=200)
    plt.close(fig)
    print("wrote out/cgf_how_we_work.png")


if __name__ == "__main__":
    main()
