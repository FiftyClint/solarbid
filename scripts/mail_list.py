#!/usr/bin/env python3
"""Mailing lists for both test cells, one row per farm.

The account workbook is 222 rows, but a row is a meter. Mailing off it would
send four envelopes to one grower and none to the farms that share a name. This
collapses to (Name, Service Address), which is the grain a letter goes to.

Two cells go out, and the handwritten note is held constant across both so that
the only thing varying is the printed piece:

    broiler     79 farms   two-page mailer, printed duplex
    flyer       86 farms   one-page Ogilvy-register flyer

Segment still differs between the cells, which the flyer cannot control for. It
tells you whether the second register pulls at all, not that it beats the first.

Each row carries note_kwh, the figure that goes in that farm's letter. It is the
farm-grain median for that farm's segment, and it is blank where the segment has
fewer than ten farms, because a median of three or six is a number we would be
inventing. Those growers get the version of the note that opens on the bill.

    python scripts/mail_list.py

Writes out/mail_list.csv, out/mail_list_flyer.csv and out/mail_list_review.csv.
All three carry names and addresses, so all three stay in out/, which is
gitignored. Nothing here is committed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from solarbid.accounts import load_accounts  # noqa: E402

ACCOUNTS = Path("data/accounts.xlsx")
OUT = Path("out")

# Below this, a segment median is a number about three or six farms, not about
# the reader's farm. Same threshold the printed table uses.
MIN_SEGMENT = 10

BROILER_BANDS = [("3 houses", (3, 3)), ("4 houses", (4, 4)),
                 ("5-6 houses", (5, 6))]


def rollup(df: pd.DataFrame, bird_types: list[str]):
    """Collapse meters to farms. Returns (usable, held_for_review)."""
    b = df[df.bird_type.isin(bird_types)].dropna(subset=["house_count"]).copy()
    b["farm"] = (b["Name"].astype(str).str.strip() + "|"
                 + b["Service Address"].astype(str).str.strip())
    grp = b.groupby("farm")

    # Meters that disagree on house count usually mean two separate farms filed
    # under one name. Summing those would invent a farm that does not exist.
    agree = grp["house_count"].nunique() == 1
    roll = grp.agg(
        name=("Name", "first"),
        mail_address=("Address", "first"),
        service_address=("Service Address", "first"),
        city=("City", "first"),
        state=("State", "first"),
        zip_code=("ZIP Code", "first"),
        district=("District Office", "first"),
        bird_type=("bird_type", "first"),
        houses=("house_count", "max"),
        meters=("period_kwh", "size"),
        annualized_kwh=("annualized_kwh", "sum"),
    )
    ok = agree.reindex(roll.index).fillna(False)
    return roll[ok].copy(), roll[~ok].copy()


def round_kwh(value: float) -> str:
    """Round to the nearest 10,000. These stand in for a farm, not measure one."""
    return f"{round(value / 10_000) * 10_000:,.0f}"


def assign_broiler(farms: pd.DataFrame) -> pd.DataFrame:
    farms["segment"] = "2 houses"
    for label, (lo, hi) in BROILER_BANDS:
        farms.loc[farms.houses.between(lo, hi), "segment"] = label
    return with_note_kwh(farms)


def assign_flyer(farms: pd.DataFrame) -> pd.DataFrame:
    # House count is the useful split for broilers. For layers it is not: 66 of
    # these farms are single-house egg operations, so the segment is bird type
    # and house count together.
    farms["segment"] = (farms.bird_type.str.title() + ", "
                        + farms.houses.astype(int).astype(str) + " house"
                        + farms.houses.gt(1).map({True: "s", False: ""}))
    return with_note_kwh(farms)


def with_note_kwh(farms: pd.DataFrame) -> pd.DataFrame:
    counts = farms.groupby("segment").size()
    medians = farms.groupby("segment").annualized_kwh.median()
    farms["segment_farms"] = farms.segment.map(counts)
    farms["note_kwh"] = farms.segment.map(
        lambda s: round_kwh(medians[s]) if counts[s] >= MIN_SEGMENT else ""
    )
    return farms


COLS = ["name", "mail_address", "city", "state", "zip_code", "service_address",
        "district", "bird_type", "houses", "meters", "annualized_kwh",
        "segment", "segment_farms", "note_kwh"]


def main() -> int:
    df = load_accounts(ACCOUNTS)
    OUT.mkdir(exist_ok=True)

    broiler, broiler_review = rollup(df, ["BROILER"])
    flyer, flyer_review = rollup(df, ["EGG", "PULLET", "BREEDER"])
    broiler = assign_broiler(broiler)
    flyer = assign_flyer(flyer)

    for name, cell in (("mail_list", broiler), ("mail_list_flyer", flyer)):
        cell.sort_values("annualized_kwh", ascending=False)[COLS].to_csv(
            OUT / f"{name}.csv", index=False)

    review = pd.concat([broiler_review, flyer_review])
    review.to_csv(OUT / "mail_list_review.csv", index=False)

    for label, cell in (("broiler cell", broiler), ("flyer cell", flyer)):
        no_number = (cell.note_kwh == "").sum()
        print(f"\n{label}: {len(cell)} farms, {int(cell.meters.sum())} meters")
        print(f"  letters opening on a number: {len(cell) - no_number}")
        print(f"  letters opening on the bill: {no_number}")
        print(cell.groupby("segment")
                  .agg(farms=("name", "size"), note_kwh=("note_kwh", "first"))
                  .to_string())

    print(f"\nheld for review: {len(review)} (meters disagree on house count)")
    print(f"wrote 3 files to {OUT}/. All hold personal data; out/ is gitignored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
