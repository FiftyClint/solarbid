#!/usr/bin/env python3
"""Render a stage-one budgetary quote for one farm from the spike output.

    python scripts/make_quote.py farm_00167 --county Randolph

County is required and not inferred. It drives the 10-point energy community
adder, and getting it wrong overstates the credit by a fifth. Pass --county
explicitly until per-farm county assignment is wired from TIGER boundaries.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from solarbid import incentives  # noqa: E402
from solarbid.load import estimate_load  # noqa: E402
from solarbid.quote import budgetary_quote  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("farm_id")
    ap.add_argument("--county", required=True)
    ap.add_argument("--farms", type=Path, default=Path("out/peco_farms.csv"))
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--html", type=Path, default=None, help="Write an HTML one-pager.")
    ap.add_argument("--prepared-by", default="")
    ap.add_argument(
        "--placed-in-service", type=date.fromisoformat, default=date(2027, 12, 1)
    )
    ap.add_argument("--tax-rate", type=float, default=0.30)
    ap.add_argument(
        "--domestic-content",
        action="store_true",
        help="Claim the 10-point adder. Needs a bill of materials to evidence.",
    )
    args = ap.parse_args()

    if not args.farms.exists():
        print(f"ERROR: {args.farms} not found. Run scripts/run_spike.py first.",
              file=sys.stderr)
        return 1

    farms = pd.read_csv(args.farms)
    match = farms[farms["farm_id"] == args.farm_id]
    if match.empty:
        print(f"ERROR: {args.farm_id} not in {args.farms}.", file=sys.stderr)
        return 1
    farm = match.iloc[0]

    ec = incentives.energy_community_by_county(args.county)
    if ec is None:
        print(
            f"WARNING: no energy community list for {args.county}; treating as "
            "undetermined, which quotes the adder at zero.",
            file=sys.stderr,
        )

    load = estimate_load(farm["floor_area_ft2"])
    itc = incentives.itc_rate(
        system_kw_ac=float(farm["recommended_kw"]),
        expected_placed_in_service=args.placed_in_service,
        domestic_content=True if args.domestic_content else None,
        energy_community=ec,
    )

    quote = budgetary_quote(
        farm_id=str(farm["farm_id"]),
        county=args.county,
        house_count=int(farm["house_count"]),
        floor_area_ft2=float(farm["floor_area_ft2"]),
        load=load,
        roof_capacity_kw=float(farm["roof_capacity_kw"]),
        ground_capacity_kw=float(farm["ground_capacity_kw"]),
        itc=itc,
        tax_rate=args.tax_rate,
        quote_date=date.today(),
    )

    text = quote.render()
    text += f"\n\nSite: {farm['lat']:.5f}, {farm['lon']:.5f}"
    print(text)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"\nWrote {args.out}", file=sys.stderr)
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(quote.render_html(args.prepared_by), encoding="utf-8")
        print(f"Wrote {args.html}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
