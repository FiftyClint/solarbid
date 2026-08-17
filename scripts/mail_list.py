#!/usr/bin/env python3
"""Build the mailing list for the broiler drop, one letter per farm.

The account workbook is 222 rows, but a row is a meter. Mailing off it would
send four envelopes to one grower and none to the farms that share a name. This
collapses to (Name, Service Address), which is the grain a letter goes to.

Non-broiler accounts are held out. The sheet's sizing argument rests on how much
of the load lands in daylight, and that is a broiler pattern; layer and pullet
barns run different lighting and ventilation. They come back in when there are
real bills to build a variant on.

    python scripts/mail_list.py

Writes out/mail_list.csv and out/mail_list_review.csv. Both carry names and
addresses, so both land in out/, which is gitignored. Nothing here is committed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from solarbid.accounts import load_accounts  # noqa: E402

ACCOUNTS = Path("data/accounts.xlsx")
OUT = Path("out")

# Which table row each farm's sheet points at. Two-house farms are not on the
# table (three of them, one with a bad house count), so they get the sheet with
# no row of their own and the standing invitation to send a bill.
def band_for(houses: float) -> str:
    if houses <= 2:
        return "no row, send a bill"
    if houses == 3:
        return "3 houses"
    if houses == 4:
        return "4 houses"
    return "5-6 houses"


def main() -> int:
    df = load_accounts(ACCOUNTS)
    b = df[df.bird_type == "BROILER"].dropna(subset=["house_count"]).copy()
    b["farm"] = (b["Name"].astype(str).str.strip() + "|"
                 + b["Service Address"].astype(str).str.strip())

    grp = b.groupby("farm")
    agree = grp["house_count"].nunique() == 1

    roll = grp.agg(
        name=("Name", "first"),
        mail_address=("Address", "first"),
        service_address=("Service Address", "first"),
        city=("City", "first"),
        state=("State", "first"),
        zip_code=("ZIP Code", "first"),
        district=("District Office", "first"),
        houses=("house_count", "max"),
        houses_disagree=("house_count", "nunique"),
        meters=("period_kwh", "size"),
        annualized_kwh=("annualized_kwh", "sum"),
    )

    clean = roll[agree.reindex(roll.index).fillna(False)].copy()
    clean["sheet_row"] = clean.houses.map(band_for)
    review = roll[~agree.reindex(roll.index).fillna(True)].copy()

    OUT.mkdir(exist_ok=True)
    # mail_address is where the letter goes. service_address is where the houses
    # are, and for 3 of these farms they are in different states.
    cols = ["name", "mail_address", "city", "state", "zip_code",
            "service_address", "district", "houses", "meters",
            "annualized_kwh", "sheet_row"]
    clean.sort_values(["houses", "name"])[cols].to_csv(OUT / "mail_list.csv",
                                                       index=False)
    review.to_csv(OUT / "mail_list_review.csv", index=False)

    print(f"broiler accounts:        {len(b)}")
    print(f"farms to mail:           {len(clean)}")
    print(f"held for review:         {len(review)}  (meters disagree on house count)")
    print(f"farms with >1 meter:     {(clean.meters > 1).sum()}")
    print(f"out-of-state mailing:    {(clean.state.astype(str).str.strip() != 'AR').sum()}")
    print()
    print(clean.sheet_row.value_counts().to_string())
    print(f"\nwrote {OUT/'mail_list.csv'} and {OUT/'mail_list_review.csv'}")
    print("Both hold personal data. out/ is gitignored; keep them out of the repo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
