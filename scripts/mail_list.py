#!/usr/bin/env python3
"""Mailing lists for both test cells, one row per envelope.

The account workbook is 222 rows and a row is a meter. Two collapses stand
between that and a mailing. Meters fold into farms on (Name, Service Address),
which is the grain the model wants, because two farms under one name are two
sets of houses drawing two loads. Farms then fold into recipients on (Name,
Mailing Address, ZIP), which is the grain an envelope wants: 25 people would
otherwise have received between two and four identical letters on the same day.

222 meters, 165 farms, 135 envelopes.

Two cells go out, and the handwritten note is held constant across both so that
the only thing varying is the printed piece:

    broiler     58 envelopes   two-page mailer, printed duplex
    flyer       77 envelopes   one-page Ogilvy-register flyer

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


def collapse_to_recipients(farms: pd.DataFrame) -> pd.DataFrame:
    """One row per envelope, not per farm.

    (Name, Service Address) is the right grain for the model, because two farms
    under one name are two sets of houses drawing two loads. It is the wrong
    grain for a mailbox: 25 people would have received between two and four
    identical envelopes on the same day, which is the fastest way to look like
    junk mail after going to the trouble of writing by hand.

    Houses and the segment medians add across a person's farms, so a grower with
    two four-house farms is written to about eight houses and the whole bill,
    which is both truer to his position and a larger number than either farm on
    its own. Where any one of his farms sits in a segment too thin to quote, the
    total would be short by an unknown amount, so he takes the version of the
    note that opens without a figure.
    """
    farms = farms.copy()
    farms["recipient"] = (
        farms.name.astype(str).str.strip().str.upper() + "|"
        + farms.mail_address.astype(str).str.strip().str.upper() + "|"
        + farms.zip_code.astype(str).str.strip())

    grouped = farms.groupby("recipient", sort=False)
    out = grouped.agg(
        name=("name", "first"),
        mail_address=("mail_address", "first"),
        city=("city", "first"),
        state=("state", "first"),
        zip_code=("zip_code", "first"),
        service_address=("service_address", "first"),
        district=("district", "first"),
        bird_type=("bird_type", "first"),
        houses=("houses", "sum"),
        farms=("name", "size"),
        meters=("meters", "sum"),
        annualized_kwh=("annualized_kwh", "sum"),
        segment=("segment", lambda s: " + ".join(sorted(set(s)))),
        segment_farms=("segment_farms", "min"),
    )
    quotable = grouped.median_kwh.apply(lambda s: s.notna().all())
    totals = grouped.median_kwh.sum()
    out["note_kwh"] = [round_kwh(totals[i]) if quotable[i] else ""
                       for i in out.index]
    return out.reset_index(drop=True)


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
    # Kept numeric so a person's farms can be added together before rounding.
    farms["median_kwh"] = farms.segment.map(
        lambda s: medians[s] if counts[s] >= MIN_SEGMENT else float("nan"))
    return farms


COLS = ["name", "mail_address", "city", "state", "zip_code", "service_address",
        "district", "bird_type", "houses", "farms", "meters", "annualized_kwh",
        "segment", "segment_farms", "note_kwh"]


def main() -> int:
    df = load_accounts(ACCOUNTS)
    OUT.mkdir(exist_ok=True)

    broiler, broiler_review = rollup(df, ["BROILER"])
    flyer, flyer_review = rollup(df, ["EGG", "PULLET", "BREEDER"])
    broiler = collapse_to_recipients(assign_broiler(broiler))
    flyer = collapse_to_recipients(assign_flyer(flyer))

    for name, cell in (("mail_list", broiler), ("mail_list_flyer", flyer)):
        cell.sort_values("annualized_kwh", ascending=False)[COLS].to_csv(
            OUT / f"{name}.csv", index=False)

    review = pd.concat([broiler_review, flyer_review])
    review.to_csv(OUT / "mail_list_review.csv", index=False)

    for label, cell in (("broiler cell", broiler), ("flyer cell", flyer)):
        no_number = (cell.note_kwh == "").sum()
        print(f"\n{label}: {len(cell)} envelopes, "
              f"{int(cell.farms.sum())} farms, {int(cell.meters.sum())} meters")
        multi = (cell.farms > 1).sum()
        print(f"  people with more than one farm: {multi}")
        print(f"  letters opening on a number: {len(cell) - no_number}")
        print(f"  letters opening on the bill: {no_number}")
        # Group on the figure as well as the segment. Two people can share a
        # segment label and carry different totals, because one of them owns
        # two farms in it.
        print(cell.groupby(["segment", "houses", "note_kwh"], dropna=False)
                  .size().rename("envelopes").to_string())

    print(f"\nheld for review: {len(review)} (meters disagree on house count)")
    print(f"wrote 3 files to {OUT}/. All hold personal data; out/ is gitignored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
