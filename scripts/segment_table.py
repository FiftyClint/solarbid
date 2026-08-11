#!/usr/bin/env python3
"""Derive the by-farm-size table on the print pieces from the account file.

The figures on the solar sheet used to be hand-copied constants, computed from
per-account medians. That was wrong in a way that mattered: the workbook's grain
is the METER, not the farm. Eighteen of the four-house broiler growers carry two
meters, so a per-account median describes half a farm. The four-house row, which
is 61% of the broiler list, came out 27% low, and everything downstream of the
load -- system size, cost, credit, savings -- was low with it.

Rolling up to (Name, Service Address) fixes it. That grain is tighter than Name
alone, which would merge two growers who share a surname, and tighter than
address alone, which would merge a landlord's separate farms.

Bands rather than one row per house count. Discrete rows look more precise but
are not: at farm grain there are three 2-house farms, and a median of three is
not a number to print. Each band below carries n >= 13.

    python scripts/segment_table.py

Prints the TABLE literal for the build scripts. The workbook is gitignored, so
the derived rows are committed rather than the source.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from solarbid import incentives  # noqa: E402
from solarbid.accounts import load_accounts, metered_load_band  # noqa: E402
from solarbid.config import ArkansasTariff, Pricing, SitingModel  # noqa: E402
from solarbid.quote import _mount_option  # noqa: E402

ACCOUNTS = Path("data/accounts.xlsx")

# Median detected house in the Peco AOI, used for roof capacity only.
DEFAULT_HOUSE_FT2 = 31_000.0

# Every account in this file resolves to Randolph or Clay through the district
# office, and both are on the energy community list. Verified, not assumed.
PLACED_IN_SERVICE = date(2027, 12, 1)
TAX_RATE = 0.30

# Two-house farms are left off. There are three of them at farm grain, and one
# draws 349,440 kWh/yr -- as much as a six-house farm -- which is a bad house
# count rather than a real outlier. A median of three, one of them wrong, is not
# a number to print. Those growers get the same invitation as everyone else at
# the bottom of the sheet: send a bill.
BANDS = [
    ("3 houses", (3, 3)),
    ("4 houses", (4, 4)),
    ("5-6 houses", (5, 6)),
]


def farm_rollup(df: pd.DataFrame, bird_type: str = "BROILER") -> pd.DataFrame:
    """Collapse meters to farms, dropping the ones we cannot collapse safely."""
    b = df[(df.bird_type == bird_type)].dropna(subset=["house_count"]).copy()
    b["farm"] = b["Name"].astype(str).str.strip() + "|" + \
        b["Service Address"].astype(str).str.strip()
    grp = b.groupby("farm")

    # Meters that disagree on house count usually mean two separate farms filed
    # under one name. Summing those would invent a farm that does not exist, so
    # they are excluded here and flagged for a human.
    agree = grp["house_count"].nunique() == 1
    roll = grp.agg(houses=("house_count", "max"),
                   annualized_kwh=("annualized_kwh", "sum"),
                   demand_kw=("demand_kw", "sum"),
                   meters=("period_kwh", "size"))
    excluded = int((~agree).sum())
    if excluded:
        print(f"note: {excluded} farms excluded, meters disagree on house count",
              file=sys.stderr)
    return roll[agree.reindex(roll.index).fillna(False)]


def quote_band(annual_kwh: float, houses: int) -> dict:
    """Size and price one representative farm through the real pipeline.

    Goes through the same _mount_option the individual quotes use, so a grower
    who sends a bill gets a number built the same way as the one on the sheet.
    """
    load = metered_load_band(annual_kwh)
    floor_ft2 = houses * DEFAULT_HOUSE_FT2
    siting = SitingModel()
    pricing = Pricing()
    tariff = ArkansasTariff()
    roof_kw = (floor_ft2 / 2.0 * siting.roof_usable_fraction
               * siting.roof_watts_per_ft2 / 1000.0)

    itc = incentives.itc_rate(
        system_kw_ac=200,
        expected_placed_in_service=PLACED_IN_SERVICE,
        domestic_content=True,
        energy_community=True,
    )

    # Ground mount is what gets pictured and priced on the sheet. Land is not
    # the binding constraint on these farms, so let load set the size and give
    # capacity plenty of headroom above the roof.
    opt = _mount_option(
        mount="ground",
        capacity_kw=roof_kw * 4,
        annual_load_kwh=load.mid_kwh,
        itc_rate=itc.total_rate,
        tax_rate=TAX_RATE,
        pricing=pricing,
        tariff=tariff,
        siting=siting,
    )
    return {"kwh": annual_kwh, "kw": opt.recommended_kw,
            "gross": opt.gross_cost, "credit": opt.gross_cost * itc.total_rate,
            "savings": opt.annual_savings, "payback": opt.payback_years,
            "itc": itc.total_rate}


def main() -> int:
    roll = farm_rollup(load_accounts(ACCOUNTS))
    rows = []
    for label, (lo, hi) in BANDS:
        seg = roll[(roll.houses >= lo) & (roll.houses <= hi)]
        kwh = float(seg.annualized_kwh.median())
        rep = int(seg.houses.median())
        q = quote_band(kwh, rep)
        rows.append((label, seg, q))
        print(f"{label:<12} farms={len(seg):>3}  meters/farm={seg.meters.mean():.1f}  "
              f"kWh/yr={kwh:>9,.0f}  {q['kw']:>6.0f} kW  "
              f"${q['gross']:>9,.0f}  credit ${q['credit']:>9,.0f}  "
              f"saves ${q['savings']:>7,.0f}  {q['payback']:.1f} yr",
              file=sys.stderr)

    print("\nTABLE = [")
    for label, seg, q in rows:
        # Savings rounds to the hundred. It is the one column carrying a real
        # modeling assumption rather than a measurement, and printing it to the
        # dollar would claim a precision the yield estimate does not have.
        saves = round(q["savings"] / 100) * 100
        print(f'    ("{label}", "{q["kwh"]:,.0f}", "{q["kw"]:.0f} kW", '
              f'"${q["gross"]:,.0f}", "${q["credit"]:,.0f}", '
              f'"${saves:,.0f}", "{q["payback"]:.1f} yrs"),')
    print("]")
    total = sum(len(seg) for _, seg, _ in rows)
    print(f"\n# {total} broiler farms, rolled up from "
          f"{int(sum(seg.meters.sum() for _, seg, _ in rows))} metered accounts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
