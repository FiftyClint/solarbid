#!/usr/bin/env python3
"""Informational fact sheet, in the register of a USDA or extension handout.

Not an ad. The job is to explain the rules plainly enough that a grower can
check them himself, including the ones that cost us the sale. Trust here comes
from saying REAP is halted and that Arkansas stopped paying retail for exports,
not from a headline.

Type is plain: sans heads, serif body, no condensed display caps. Color is one
header band and hairline rules. The phone number sits at the bottom at normal
size, because a fact sheet that shouts stops being a fact sheet.

Layout flows from a measured cursor rather than fixed coordinates, so editing
the copy cannot silently push a paragraph into the section below it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.image import imread  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from brand import (  # noqa: E402
    BRAND, Flow, INK, L, LOGO_PATH, MUTE, PAGE_H, PAGE_W, PAPER, PHONE,
    ADDRESS, PHOTO_GROUND, R, RULE_C, WEB,
)

HEAD = "Work Sans"
SERIF = "IBM Plex Serif"
MONO = "Geist Mono"

TABLE = [
    ("2 houses", "125,760", "75 kW", "$157,500", "$78,750", "$10,500", "4.1 yrs"),
    ("4 houses", "194,880", "115 kW", "$241,500", "$120,750", "$16,200", "4.1 yrs"),
    ("6 houses", "343,680", "205 kW", "$430,500", "$215,250", "$28,700", "4.1 yrs"),
]
COLS = ["", "kWh/year", "System", "Installed", "Federal credit", "Saves/year",
        "Payback"]

SECTIONS = [
    ("1", "The federal tax credit", [
        ("The Section 48E credit covers 30% of project cost. Systems under 1 "
         "megawatt count as meeting the prevailing wage and apprenticeship "
         "rules automatically, so a poultry system takes the full rate without "
         "that paperwork. Two adders apply on top.", 0.0),
        ("Domestic content, 10%, for equipment meeting the federal sourcing "
         "threshold.", 0.022),
        ("Energy community, 10%. Randolph, Clay, Lawrence, Greene, Independence, "
         "Izard, Sharp, Fulton, Jackson and Mississippi counties all qualify.",
         0.022),
        ("That is 50% of cost as a credit against federal tax, and most of the "
         "rest can be depreciated in year one. Both need tax liability to "
         "offset. Your CPA should confirm you have it.", 0.0),
    ]),
    ("2", "The deadline", [
        ("The system has to be running by December 31, 2027. That is a federal "
         "date from the July 2025 tax law, not a sales deadline. Battery storage "
         "is on a separate clock and keeps the full credit for projects starting "
         "construction through 2033.", 0.0),
    ]),
    ("3", "What is not available right now", [
        ("USDA halted REAP grant awards on March 31, 2026 pending new rules. "
         "Applications are not being processed and earlier applicants will have "
         "to reapply. Guaranteed loans continue. If anyone shows you a REAP "
         "grant line today, ask what date the program reopened.", 0.0),
    ]),
    ("4", "What Arkansas pays for power you send back", [
        ("Act 278 ended one-to-one net metering for systems energized after "
         "September 30, 2024. Power used in the houses offsets the full retail "
         "rate. Power exported is credited at avoided cost, a fraction of that. "
         "So systems get sized to what the houses draw in daylight, not to the "
         "annual bill.", 0.0),
    ]),
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


def new_page(continuation=False):
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.canvas.draw()

    band_h = 0.042 if continuation else 0.060
    ax.add_patch(Rectangle((0, 1 - band_h), 1, band_h, facecolor=BRAND,
                           edgecolor="none"))
    if LOGO_PATH.exists():
        img = imread(str(LOGO_PATH))
        h = 0.026 if continuation else 0.038
        w = h * (img.shape[1] / img.shape[0]) * (PAGE_H / PAGE_W)
        y0 = 1 - band_h + (band_h - h) / 2
        ax.imshow(img, extent=(L, L + w, y0, y0 + h), zorder=3, aspect="auto")

    if continuation:
        ax.text(R, 1 - band_h / 2, "Solar on a Poultry Farm in Northeast "
                "Arkansas   ·   page 2 of 2", family=HEAD, size=8.4,
                color="#BFD8F0", ha="right", va="center")
    else:
        ax.text(R, 0.978, "Cleaner Greener Future", family=HEAD, weight="bold",
                size=10, color=PAPER, ha="right", va="center")
        ax.text(R, 0.958,
                "with NEA Solar   ·   Energy and incentive specialists",
                family=HEAD, size=8, color="#BFD8F0", ha="right", va="center")

    return fig, ax, (0.930 if not continuation else 0.928)


def main():
    pages = []

    # ============================================================ front page
    fig, ax, top = new_page()
    flow = Flow(fig, ax, top)

    flow.text("Solar on a Poultry Farm in Northeast Arkansas", HEAD, 19,
              weight="bold", leading=1.25, gap_after=0.008)
    flow.text("What the federal credit is worth right now, the deadlines, and "
              "what a system looks like on a farm your size.",
              SERIF, 10.2, color=MUTE, leading=1.4, gap_after=0.004)
    flow.text("Prepared August 2026. Every figure below can be checked against "
              "the sources named.", MONO, 6.6, color=MUTE, gap_after=0.010)

    for number, title, paras in SECTIONS:
        section_head(flow, number, title)
        for text, indent in paras:
            flow.text(text, SERIF, 9.6, leading=1.5, indent=indent,
                      gap_after=0.008)

    ax.plot([L, R], [0.052, 0.052], color=RULE_C, lw=0.7)
    ax.text(L, 0.034, "Numbers by farm size, and how to get your own, "
            "on the back.", family=SERIF, size=9.2, color=MUTE, ha="left",
            va="center")
    ax.text(R, 0.034, f"{PHONE}", family=HEAD, weight="bold", size=9.4,
            color=BRAND, ha="right", va="center")
    print(f"front page content ends at y={flow.y:.3f}")
    pages.append(fig)

    # ============================================================= back page
    fig, ax, top = new_page(continuation=True)
    flow = Flow(fig, ax, top)

    section_head(flow, "5", "What it looks like by farm size")

    xs = [L, L + 0.135, L + 0.250, L + 0.360, L + 0.500, L + 0.660, R]
    flow.gap(0.014)
    for i, head in enumerate(COLS):
        ax.text(xs[i], flow.y, head, family=MONO, size=6.4, color=MUTE,
                ha="right" if i == 6 else "left", va="baseline")

    for row in TABLE:
        flow.gap(0.030)
        for i, cell in enumerate(row):
            ax.text(xs[i], flow.y, cell, family=SERIF,
                    weight="bold" if i in (0, 5, 6) else "normal", size=10.2,
                    color=BRAND if i == 5 else INK,
                    ha="right" if i == 6 else "left", va="baseline")
        flow.gap(0.011)
        ax.plot([L, R], [flow.y, flow.y], color=RULE_C, lw=0.6)

    flow.gap(0.012)
    flow.text("Ground mount at $2.10 per watt installed, as pictured below. "
              "Roof runs about 5% less where the trusses will carry it, and "
              "gets quoted alongside. Usage figures are medians from metered "
              "accounts on 115 broiler farms in this area, annualized from a "
              "single billing period. Your own twelve months would replace "
              "them.", SERIF, 8.8, color=MUTE, leading=1.45, gap_after=0.018)

    section_head(flow, "6", "What these look like on the ground")
    flow.gap(0.008)

    have = [p for p in PHOTO_GROUND if p.exists()]
    if have:
        gap = 0.014
        w = ((R - L) - gap * (len(have) - 1)) / len(have)
        height = w / 1.75 * (PAGE_W / PAGE_H)
        for i, path in enumerate(have):
            left = L + i * (w + gap)
            ax.imshow(imread(str(path)),
                      extent=(left, left + w, flow.y - height, flow.y),
                      aspect="auto", zorder=2)
        flow.gap(height + 0.012)
        flow.text("Ground mount installations completed by NEA Solar.",
                  MONO, 6.6, color=MUTE, gap_after=0.020)

    section_head(flow, "7", "If you want your own numbers")
    flow.text("Send twelve months of billing history from your co-op. We will "
              "read the rate, the demand charges and the usage, and tell you "
              "what the farm qualifies for. There is no charge for that and no "
              "obligation after it.", SERIF, 9.6, leading=1.5, gap_after=0.014)
    flow.text("If the answer is that your money is in the rate or in the fans "
              "rather than in a solar array, that is what we will tell you.",
              SERIF, 9.6, leading=1.5)
    print(f"back page content ends at y={flow.y:.3f}")

    ax.plot([L, R], [0.062, 0.062], color=RULE_C, lw=0.7)
    ax.text(L, 0.040, "Cleaner Greener Future, with NEA Solar", family=HEAD,
            weight="bold", size=9.6, color=INK, ha="left", va="center")
    ax.text(L, 0.022, f"{PHONE}   ·   {WEB}   ·   {ADDRESS}", family=HEAD,
            size=8.6, color=MUTE, ha="left", va="center")
    pages.append(fig)

    # ================================================================ output
    out_pdf = Path("out/cgf_factsheet.pdf")
    with PdfPages(out_pdf) as pdf:
        for fig in pages:
            pdf.savefig(fig, facecolor=PAPER)
    for i, fig in enumerate(pages, 1):
        fig.savefig(f"out/cgf_factsheet_p{i}.png", facecolor=PAPER, dpi=200)
        plt.close(fig)
    print(f"wrote {out_pdf} (2 pages)")


if __name__ == "__main__":
    main()
