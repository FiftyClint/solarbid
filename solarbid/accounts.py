"""Ingest utility account data for poultry houses.

This is the best input the pipeline has. It replaces the two weakest links at
once: metered consumption instead of a geometry estimate spanning 4x, and a
named contact with a phone number instead of a polygon.

CONTAINS PERSONAL DATA. Names, service and mailing addresses, email addresses,
mobile numbers and utility account numbers. Keep the source file out of version
control -- `data/` is gitignored apart from two named extracts, so put it there.
Do not commit derived files that carry the identifying columns either. Anything
published or shared should go through `aggregate()`.

The account list also carries what nothing else does: `Service Description`
encodes bird type and house count directly, e.g. CH/BROILER/4 is a four-house
broiler farm. That is ground truth for validating barn detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

# Columns that identify a person. Never publish, never commit.
PII_COLUMNS = (
    "Account",
    "Name",
    "Service Address",
    "Address",
    "Misc E-Mail",
    "E-Bill E-Mail Addr",
    "Mobile Area Code",
    "Mobile Phone",
)

_HOUSE_COUNT = re.compile(r"/(\d+)")
_BIRD_TYPES = ("BROILER", "PULLET", "BREEDER", "EGG")

# A single billing period is not a year. Poultry load is ~88% ventilation and
# peaks on summer afternoons, so a summer reading annualizes high and a winter
# one low. The account file carries no read dates, so the month is unknown.
NAIVE_ANNUALIZATION_FACTOR = 12.0


@dataclass(frozen=True)
class AccountLoad:
    """Metered load for one account, with its provenance stated."""

    account_ref: str
    bird_type: str | None
    house_count: int | None
    period_kwh: float
    demand_kw: float
    annualized_kwh: float
    is_annualized_from_one_period: bool = True

    @property
    def kwh_per_house(self) -> float | None:
        if not self.house_count:
            return None
        return self.annualized_kwh / self.house_count

    @property
    def load_factor(self) -> float | None:
        """kWh over demand times hours. Low means a peaky, demand-driven bill."""
        if not self.demand_kw:
            return None
        return self.period_kwh / (self.demand_kw * 730.0)


def parse_service_description(value: str) -> tuple[str | None, int | None]:
    """Pull bird type and house count out of a service description.

    Formats seen: CH/BROILER/4, CH/EGG/1/VITAL, CH/BROILER/4/DRAFT, with
    inconsistent spacing and pluralization.
    """
    text = str(value).upper()
    bird = next((b for b in _BIRD_TYPES if b in text), None)
    match = _HOUSE_COUNT.search(text)
    return bird, int(match.group(1)) if match else None


def load_accounts(path: str, sheet: str | int = 0) -> pd.DataFrame:
    """Read the account workbook and normalize the columns we rely on."""
    raw = pd.read_excel(path, sheet_name=sheet)

    parsed = raw["Service Description"].apply(parse_service_description)
    out = raw.copy()
    out["bird_type"] = [p[0] for p in parsed]
    out["house_count"] = [p[1] for p in parsed]
    out["period_kwh"] = pd.to_numeric(out["kWh's used"], errors="coerce")
    out["demand_kw"] = pd.to_numeric(out["DEMAND in kW"], errors="coerce")
    out["annualized_kwh"] = out["period_kwh"] * NAIVE_ANNUALIZATION_FACTOR
    out["existing_estimate_kw_ac"] = pd.to_numeric(
        out["Estimated Solar in AC kW needed"], errors="coerce"
    )
    out["has_email"] = out["Misc E-Mail"].notna() | out["E-Bill E-Mail Addr"].notna()
    out["has_mobile"] = out["Mobile Phone"].notna()
    return out


def aggregate(accounts: pd.DataFrame) -> pd.DataFrame:
    """Summary safe to publish: no row identifies an account holder."""
    grouped = accounts.groupby(["bird_type", "house_count"], dropna=False)
    return grouped.agg(
        accounts=("period_kwh", "size"),
        median_period_kwh=("period_kwh", "median"),
        median_demand_kw=("demand_kw", "median"),
    ).reset_index()


def redact(accounts: pd.DataFrame) -> pd.DataFrame:
    """Drop every identifying column, keeping the analysis columns."""
    return accounts.drop(columns=[c for c in PII_COLUMNS if c in accounts.columns])


def calibration_against_geometry(
    accounts: pd.DataFrame, bird_type: str = "BROILER"
) -> dict[str, float]:
    """Annual kWh per house implied by real meters.

    Use this to check the geometry load model, which is all that is available
    for farms outside the account list.
    """
    subset = accounts[
        (accounts["bird_type"] == bird_type)
        & (accounts["house_count"] > 0)
        & (accounts["period_kwh"] > 0)
    ]
    if subset.empty:
        return {}

    per_house = subset["annualized_kwh"] / subset["house_count"]
    return {
        "accounts": float(len(subset)),
        "houses": float(subset["house_count"].sum()),
        "median_annual_kwh_per_house": float(per_house.median()),
        "p25_annual_kwh_per_house": float(per_house.quantile(0.25)),
        "p75_annual_kwh_per_house": float(per_house.quantile(0.75)),
    }


def compare_to_existing_estimate(accounts: pd.DataFrame) -> dict[str, float]:
    """How the workbook's own sizing column relates to demand.

    The existing figures track about 1.7x metered demand, which is a peak-based
    rule of thumb. It takes no view on how much generation the farm can actually
    consume, and under Act 278 that is the thing that decides whether a kW is
    worth installing. Expect our sizing to differ, and to differ downward on
    farms with low load factors.
    """
    subset = accounts[
        (accounts["existing_estimate_kw_ac"] > 0) & (accounts["demand_kw"] > 0)
    ]
    if subset.empty:
        return {}
    ratio = subset["existing_estimate_kw_ac"] / subset["demand_kw"]
    return {
        "accounts": float(len(subset)),
        "median_multiple_of_demand": float(ratio.median()),
        "median_estimate_kw_ac": float(subset["existing_estimate_kw_ac"].median()),
    }


ACCOUNT_CAVEATS = [
    "kWh and demand are a single billing period, not a year. Poultry load is "
    "roughly 88% ventilation and peaks in summer, so annualizing one reading "
    "overstates a summer month and understates a winter one. The file carries "
    "no read dates, so the month is unknown. Twelve months of history would "
    "remove this entirely and is the single highest-value thing to ask for.",
    "House counts come from the service description rather than a survey, and "
    "one meter does not always serve one farm.",
    "Demand readings enable demand-charge analysis, which matters on "
    "cooperative tariffs and is not yet modeled.",
]
