#!/usr/bin/env python3
"""The mailer as one file: how we work on the front, solar on the back.

Two pieces of paper in the envelope, not three. This is one sheet printed
duplex, and the handwritten note goes in with it.

Page order is the argument. The front is what CGF does, five steps, with solar
appearing once at the end as the handoff. The back is the example. Reversing
them would make it a solar mailer with a company page stapled to it.

    python scripts/build_mailer.py

Both page scripts still run standalone for previewing a single side.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

import build_company_sheet  # noqa: E402
import build_solar_sheet  # noqa: E402
from brand import PAPER  # noqa: E402

OUT = Path("out/cgf_mailer.pdf")


def main():
    pages = [build_company_sheet.build(), build_solar_sheet.build()]

    OUT.parent.mkdir(exist_ok=True)
    with PdfPages(OUT) as pdf:
        for fig in pages:
            pdf.savefig(fig, facecolor=PAPER)
    for i, fig in enumerate(pages, 1):
        fig.savefig(f"out/cgf_mailer_p{i}.png", facecolor=PAPER, dpi=200)
        plt.close(fig)

    print(f"wrote {OUT} (2 pages, print duplex on one sheet)")
    print("CONFIRM BEFORE PRINTING: the Newell Coach figures on page 1.")


if __name__ == "__main__":
    main()
