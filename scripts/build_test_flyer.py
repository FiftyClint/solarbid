#!/usr/bin/env python3
"""The test cell's flyer. 77 envelopes, 86 layer, pullet and breeder farms.

The B side of an A/B on register. The mailer is a document; this has to be a
different animal or the test measures nothing.

Two earlier versions failed, and the second failed worse than the first:

  - It gave the largest element on the page to a photograph of a solar array
    while the offer was bill analysis. The caption conceded the array was "the
    last thing we do", so the eye landed first on the one thing this cell is not
    being sold. Nothing after that could make sense of it.
  - The headline set $12,000 against "how much of that is a billing mistake",
    which implies the whole bill is recoverable. An error is a slice of it.
    Overclaiming by implication is still overclaiming.
  - It asked for two things: add up twelve bills yourself, and send us your
    bills. The homework competed with the ask.
  - Three statistics that all said "here is how much power you use".

So: no photograph, because the only one on hand argues against the offer. The
page is about the bill, and the substance is the four things that actually go
wrong on one, which is the most interesting true thing we have to say to a man
who has never had his read. One ask, at the end, and it is free.

    python scripts/build_test_flyer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.image import imread  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from brand import (  # noqa: E402
    ACCENT, ADDRESS, BRAND, EMAIL, Flow, INK, L, LOGO_PATH, MUTE, PAGE_H,
    PAGE_W, PAPER, PHONE, R, WEB,
)

DISPLAY = "Bricolage Grotesque"
BODY = "Instrument Sans"
MONO = "Geist Mono"

# An office laser cannot print to the paper edge. See copy/print_spec.md.
BLEED = False
EDGE = 0.0 if BLEED else 0.034
TOP = 1.0 if BLEED else 1.0 - EDGE * (PAGE_W / PAGE_H)

# The substance of the page. These are the four errors named on the how-we-work
# sheet, which Clint confirmed, written out far enough that a grower could go
# and look for them himself.
FAULTS = [
    ("Rate class",
     "The tariff that fit when the meter went in, still applied after the farm "
     "changed. A co-op will not move you. There is no reason it would."),
    ("Meter multiplier",
     "Applied twice, or to the wrong register. It does not look like anything "
     "on the bill. It just makes every month bigger."),
    ("Demand",
     "One bad reading in July, and the ratchet carries it on every bill for the "
     "eleven months after."),
    ("Sales tax",
     "Charged on power a farm may be exempt from, going back further than most "
     "people expect."),
]


def main():
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.canvas.draw()

    FL = max(L, EDGE + 0.032)
    FIELD_BOT = 0.630
    ax.add_patch(Rectangle((EDGE, FIELD_BOT), 1 - 2 * EDGE, TOP - FIELD_BOT,
                           facecolor=INK, edgecolor="none", zorder=0))

    ax.text(FL, 0.950, "66 EGG FARMS     RANDOLPH AND CLAY COUNTIES",
            family=MONO, size=6.6, color="#6E97BC", ha="left", va="center",
            zorder=2)

    head = Flow(fig, ax, 0.898, x0=FL, x1=R - 0.05)
    head.text("You paid this bill twelve times last year.", DISPLAY, 33,
              weight="bold", color=PAPER, leading=1.14, gap_after=0.006)
    # The question is the whole pitch, so it takes the one colour the palette
    # allows at size, and only against dark ground.
    head.text("Did anyone read it?", DISPLAY, 33, weight="bold", color=ACCENT,
              leading=1.14)
    head.gap(0.024)
    head.text("A single egg house around here runs about 107,958 kilowatt-hours "
              "a year. At eleven cents that is roughly $12,000 nobody has ever "
              "audited.", BODY, 11.0, color="#A9C4DC", leading=1.52, max_w=0.60)
    print(f"field text ends at y={head.y:.3f} (field bottom {FIELD_BOT})")

    # ---------------------------------------------------------------- faults
    flow = Flow(fig, ax, FIELD_BOT - 0.044)
    flow.text("Four things that go wrong on a bill like yours", DISPLAY, 15,
              weight="bold", color=INK, gap_after=0.006)
    # The items demonstrate that these are not exotic. A line saying so was
    # costing three lines of page to make a point they already make.
    flow.text("All arithmetic, on paper you already receive.", BODY, 9.6,
              color=MUTE, leading=1.5, gap_after=0.006)

    for i, (title, body) in enumerate(FAULTS):
        # Proximity: the description has to sit nearer its own heading than the
        # next rule, or the eye groups it with the item below.
        flow.gap(0.018)
        ax.plot([L, R], [flow.y, flow.y], color="#DCE6EF", lw=0.9,
                solid_capstyle="butt")
        flow.gap(0.016)
        y = flow.y
        ax.text(L, y, f"0{i + 1}", family=MONO, size=7.2, color=BRAND,
                ha="left", va="baseline", zorder=2)
        ax.text(L + 0.042, y, title, family=DISPLAY, weight="bold", size=13,
                color=INK, ha="left", va="baseline", zorder=2)
        sub = Flow(fig, ax, y - 0.005, x0=L + 0.042, x1=R - 0.03)
        sub.text(body, BODY, 9.3, color=INK, leading=1.44)
        flow.y = sub.y
    print(f"faults end at y={flow.y:.3f}")

    # ----------------------------------------------------------------- close
    flow.gap(0.024)
    ax.plot([L, R], [flow.y, flow.y], color=ACCENT, lw=3.0,
            solid_capstyle="butt")
    flow.gap(0.022)
    flow.text("Send us twelve months and we will read it.", DISPLAY, 19,
              weight="bold", color=INK, leading=1.20, gap_after=0.010)
    flow.text(f"Email your billing history to {EMAIL}. Photographs are fine. No "
              "charge for the reading and no obligation after it, including "
              "when the answer is that we found nothing.",
              BODY, 9.8, color=INK, leading=1.52, max_w=0.64)
    print(f"close ends at y={flow.y:.3f}")

    # ---------------------------------------------------------------- footer
    if LOGO_PATH.exists():
        img = imread(str(LOGO_PATH))
        h = 0.030
        w = h * (img.shape[1] / img.shape[0]) * (PAGE_H / PAGE_W)
        ax.imshow(img, extent=(L, L + w, 0.026, 0.026 + h), zorder=3,
                  aspect="auto")
    ax.text(R, 0.048, "Cleaner Greener Future", family=BODY, weight="bold",
            size=9.0, color=INK, ha="right", va="center")
    ax.text(R, 0.032, f"{PHONE}    {WEB}", family=BODY, size=8.2, color=MUTE,
            ha="right", va="center")
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
