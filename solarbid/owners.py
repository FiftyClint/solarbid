"""Attach owner names and mailing addresses to farms from county parcel data.

A quote addressed to nobody is worthless, so this is the step that turns a
detected roof into a lead you can actually mail.

Source: the Arkansas GIS Office statewide parcel layer (CADAS_PARCEL_POLYGON_CAMP
/ CADAS_PARCEL_CENTROID_CAMP), published free from GeoStor and built from the
Computer Aided Mass Appraisal systems each county assessor maintains. It carries
owner of record, mailing address and county.

That county field matters twice over: it is also what resolves the 10-point
energy community adder, so one dataset closes both open questions.

What this cannot tell you: the Arkansas Poultry Feeding Operations registry
would name the actual operator, but Ark. Code Ann. 15-20-901 et seq. makes
information about an individual operation confidential -- only aggregate
summaries are public. There is no public operator list. Parcel ownership is the
best available proxy, and the gap between owner of record and the person running
the houses is real and flagged below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import geopandas as gpd
import pandas as pd

# Candidate column names, in preference order. The statewide layer is assembled
# from per-county CAMA exports and field naming is not perfectly consistent.
_OWNER_FIELDS = ("OWNER_NAME", "OWNER", "OWNERNAME", "NAME", "OWN_NAME", "DEED_HOLDR")
_ADDR_FIELDS = ("MAIL_ADDRESS", "OWNER_ADDRESS", "MAILADD", "ADDRESS", "MAIL_ADDR1")
_CITY_FIELDS = ("MAIL_CITY", "CITY", "MAILCITY", "OWNER_CITY")
_STATE_FIELDS = ("MAIL_STATE", "STATE", "MAILSTATE", "OWNER_STATE")
_ZIP_FIELDS = ("MAIL_ZIP", "ZIP", "MAILZIP", "ZIPCODE", "OWNER_ZIP")
_COUNTY_FIELDS = ("COUNTY_NAME", "COUNTY", "CO_NAME", "CNTY_NAME")
_PARCEL_FIELDS = ("PARCEL_ID", "PARCELID", "PIN", "PARCEL", "APN")

# Owner-of-record strings that are not a person you can write to by name.
_ENTITY_PATTERN = re.compile(
    r"\b(LLC|L\.L\.C|INC|CORP|COMPANY|CO\b|TRUST|TRUSTEE|ESTATE|FARMS?|"
    r"PARTNERSHIP|LP\b|LTD|ENTERPRISES|PROPERTIES|HOLDINGS|CHURCH|BANK)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParcelColumns:
    """Resolved column names for one parcel file."""

    owner: str | None
    address: str | None
    city: str | None
    state: str | None
    zipcode: str | None
    county: str | None
    parcel_id: str | None

    @property
    def usable(self) -> bool:
        return self.owner is not None

    def missing(self) -> list[str]:
        return [
            name
            for name, value in (
                ("owner", self.owner),
                ("mailing address", self.address),
                ("county", self.county),
            )
            if value is None
        ]


def detect_columns(parcels: pd.DataFrame) -> ParcelColumns:
    """Guess which columns hold owner, address and county.

    County CAMA exports differ in naming, so match case-insensitively against
    known candidates rather than requiring one exact schema.
    """
    lookup = {c.upper(): c for c in parcels.columns}

    def pick(candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in lookup:
                return lookup[candidate]
        return None

    return ParcelColumns(
        owner=pick(_OWNER_FIELDS),
        address=pick(_ADDR_FIELDS),
        city=pick(_CITY_FIELDS),
        state=pick(_STATE_FIELDS),
        zipcode=pick(_ZIP_FIELDS),
        county=pick(_COUNTY_FIELDS),
        parcel_id=pick(_PARCEL_FIELDS),
    )


def is_entity(owner: str | None) -> bool:
    """Whether the owner of record is an entity rather than a named person.

    Worth knowing before a mail merge: "SMITH FARMS LLC" needs a contact name
    attached before a letter addressed to it gets opened, and a trust or estate
    often means the person running the houses is not the person on the deed.
    """
    if not owner or not str(owner).strip():
        return False
    return bool(_ENTITY_PATTERN.search(str(owner)))


def attach_owners(
    barns: gpd.GeoDataFrame,
    parcels: gpd.GeoDataFrame,
    farm_id_col: str = "farm_id",
) -> pd.DataFrame:
    """Resolve one owner per farm by spatial join against parcels.

    Joins on the house polygons rather than the farm centroid, because a farm's
    centroid can land in a gap between parcels or on a neighboring tract. Where
    a farm's houses straddle several parcels -- common, since poultry houses are
    often built along a property line -- the parcel carrying the most house area
    wins, and the count of parcels touched is reported so those can be checked
    by hand.
    """
    cols = detect_columns(parcels)
    if not cols.usable:
        raise ValueError(
            "No owner column found in the parcel file. Columns present: "
            f"{sorted(parcels.columns)}"
        )

    parcels = parcels.to_crs(barns.crs)
    joined = gpd.sjoin(
        barns[[farm_id_col, "geometry"]], parcels, how="left", predicate="intersects"
    )
    joined["_house_area"] = joined.geometry.area

    keep = [c for c in (cols.owner, cols.address, cols.city, cols.state,
                        cols.zipcode, cols.county, cols.parcel_id) if c]

    rows = []
    for farm_id, group in joined.groupby(farm_id_col):
        matched = group.dropna(subset=[cols.owner])
        parcels_touched = matched[cols.parcel_id].nunique() if cols.parcel_id else len(
            matched.drop_duplicates(subset=[cols.owner])
        )

        if matched.empty:
            rows.append(
                {farm_id_col: farm_id, "owner": None, "parcels_touched": 0,
                 "owner_is_entity": False, "needs_manual_lookup": True}
            )
            continue

        dominant = (
            matched.groupby(keep, dropna=False)["_house_area"].sum().idxmax()
        )
        record = dict(zip(keep, dominant if isinstance(dominant, tuple) else (dominant,)))

        owner = record.get(cols.owner)
        rows.append(
            {
                farm_id_col: farm_id,
                "owner": owner,
                "mail_address": record.get(cols.address) if cols.address else None,
                "mail_city": record.get(cols.city) if cols.city else None,
                "mail_state": record.get(cols.state) if cols.state else None,
                "mail_zip": record.get(cols.zipcode) if cols.zipcode else None,
                "county": record.get(cols.county) if cols.county else None,
                "parcel_id": record.get(cols.parcel_id) if cols.parcel_id else None,
                "parcels_touched": int(parcels_touched),
                "owner_is_entity": is_entity(owner),
                "needs_manual_lookup": False,
            }
        )

    return pd.DataFrame(rows)


def mailability_report(owners: pd.DataFrame) -> dict[str, int]:
    """How much of the list is actually mailable, before anyone licks a stamp."""
    total = len(owners)
    if total == 0:
        return {"total": 0}

    has_owner = owners["owner"].notna()
    has_address = (
        owners["mail_address"].notna() if "mail_address" in owners else pd.Series(False, index=owners.index)
    )
    return {
        "total": total,
        "with_owner": int(has_owner.sum()),
        "with_mailing_address": int(has_address.sum()),
        "entity_owned": int(owners["owner_is_entity"].sum()),
        "straddling_multiple_parcels": int((owners["parcels_touched"] > 1).sum()),
        "need_manual_lookup": int(owners["needs_manual_lookup"].sum()),
    }


OWNER_CAVEATS = [
    "Parcel owner of record is not always the grower. Land can sit in a family "
    "trust, an LLC, or a parent's name while an adult child runs the houses.",
    "Mailing address is the assessor's tax-bill address, which for absentee "
    "owners is not the farm.",
    "Arkansas parcel boundaries from the assessor mapping program are explicitly "
    "not legal boundaries; treat them as approximate.",
    "There is no public list of poultry operators. Arkansas makes individual "
    "poultry feeding operation registrations confidential by statute, so the "
    "deed is the best available proxy.",
]
