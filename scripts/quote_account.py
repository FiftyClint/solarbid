#!/usr/bin/env python3
"""Render a budgetary quote from a utility account row.

Uses metered consumption rather than a geometry estimate, so the load band is
seasonal uncertainty only rather than the 4x dimensional spread.

    python scripts/quote_account.py --row 12 --accounts data/accounts.xlsx \
        --html out/quote.html

The source workbook holds personal data and is gitignored. Rendered quotes go
to out/, which is gitignored too.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from solarbid import incentives  # noqa: E402
from solarbid.accounts import (  # noqa: E402
    county_for_account,
    load_accounts,
    metered_load_band,
)
from solarbid.config import Pricing, SitingModel  # noqa: E402
from solarbid.finance import project_finance  # noqa: E402
from solarbid.quote import budgetary_quote  # noqa: E402
from solarbid.siting import recommend_size_kw  # noqa: E402

# Floor area per house when the account has no matched detection, used only for
# roof capacity. Median detected house in the Peco AOI.
DEFAULT_HOUSE_FT2 = 31_000.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--accounts", type=Path, required=True)
    ap.add_argument("--row", type=int, help="0-based row index.")
    ap.add_argument("--account", help="Match on the Account column instead.")
    ap.add_argument("--html", type=Path, default=None)
    ap.add_argument("--tax-rate", type=float, default=0.30)
    ap.add_argument("--prepared-by", default="Cleaner Greener Future LLC")
    ap.add_argument(
        "--placed-in-service", type=date.fromisoformat, default=date(2027, 12, 1)
    )
    args = ap.parse_args()

    accounts = load_accounts(args.accounts)
    if args.account:
        match = accounts[accounts["Account"].astype(str) == str(args.account)]
        if match.empty:
            print(f"ERROR: account {args.account} not found.", file=sys.stderr)
            return 1
        row = match.iloc[0]
    elif args.row is not None:
        row = accounts.iloc[args.row]
    else:
        print("ERROR: pass --row or --account.", file=sys.stderr)
        return 1

    county = county_for_account(row["District Office"])
    if county is None:
        print(f"WARNING: unknown district office {row['District Office']!r}; "
              "energy community will be treated as undetermined.", file=sys.stderr)

    houses = int(row["house_count"]) if row["house_count"] else 1
    load = metered_load_band(float(row["annualized_kwh"]))
    floor_ft2 = houses * DEFAULT_HOUSE_FT2

    siting = SitingModel()
    roof_kw = floor_ft2 / 2.0 * siting.roof_usable_fraction * siting.roof_watts_per_ft2 / 1000.0

    itc = incentives.itc_rate(
        system_kw_ac=200,
        expected_placed_in_service=args.placed_in_service,
        domestic_content=True,
        energy_community=(
            incentives.energy_community_by_county(county) if county else None
        ),
    )

    fin = project_finance(100, Pricing().roof_cost_per_watt, itc.total_rate, args.tax_rate)
    sized = recommend_size_kw(load.mid_kwh, roof_kw, net_cost_per_watt=fin.net_cost_per_watt)

    quote = budgetary_quote(
        farm_id=str(row["Name"]).strip(),
        county=county or "Unknown",
        house_count=houses,
        floor_area_ft2=floor_ft2,
        load=load,
        roof_capacity_kw=roof_kw,
        ground_capacity_kw=max(sized * 2, roof_kw),
        itc=itc,
        tax_rate=args.tax_rate,
        quote_date=date.today(),
        load_source="metered",
    )

    print(quote.render())
    print(f"\nService address: {row['Service Address']}")
    print(f"Metered: {row['period_kwh']:,.0f} kWh and {row['demand_kw']:,.0f} kW demand "
          f"in one billing period")

    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(quote.render_html(args.prepared_by), encoding="utf-8")
        print(f"\nWrote {args.html}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
