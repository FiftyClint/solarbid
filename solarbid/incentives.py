"""Incentive eligibility gates, as dated rules rather than constants.

The incentives that move a poultry solar deal are all mid-transition, so
nothing here is a constant. Every gate takes a date and returns a status with
its basis attached, and anything we cannot resolve from public data is reported
as unresolved rather than silently assumed favourable.

VERIFIED_AS_OF is the honesty marker. Re-verify against primary sources before
any quote leaves the building.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

VERIFIED_AS_OF = date(2026, 8, 11)

# --- Section 48E timing (One Big Beautiful Bill Act, signed 2025-07-04) -----
ITC_BEGIN_CONSTRUCTION_DEADLINE = date(2026, 7, 4)
ITC_PLACED_IN_SERVICE_FALLBACK = date(2027, 12, 31)
ITC_CONTINUITY_DEADLINE = date(2030, 12, 31)

# --- Credit rates ----------------------------------------------------------
ITC_BASE_RATE = 0.30
ITC_UNCREDITED_RATE = 0.06        # if PWA applies and is not met
DOMESTIC_CONTENT_ADDER = 0.10
ENERGY_COMMUNITY_ADDER = 0.10

# Facilities under 1 MW AC are deemed to satisfy prevailing wage and
# apprenticeship, so they take the full 30% and the full 10-point adders
# without any PWA compliance burden. Poultry farm systems run 50-150 kW, an
# order of magnitude inside this. It is the single most favourable structural
# fact in the whole model.
ONE_MW_AC_THRESHOLD_KW = 1000.0

# --- Domestic content ------------------------------------------------------
# "Adjusted percentage" of manufactured product cost that must be domestic,
# keyed to the year construction begins. Notice 2025-08 supplies elective
# safe harbor default values so this can be evidenced from a bill of materials
# rather than supplier cost data.
DOMESTIC_CONTENT_THRESHOLD_BY_BOC_YEAR = {
    2024: 0.40,
    2025: 0.45,
    2026: 0.50,
    2027: 0.55,
}

# --- Energy community ------------------------------------------------------
# Notice 2026-39 (issued 2026-06-10) is the current eligibility list, updating
# the Statistical Area and Coal Closure categories against MSHA/EIA data as of
# 2026-05-04. Eligibility is per census tract and cannot be inferred from a
# county name -- it must be looked up.
ENERGY_COMMUNITY_NOTICE = "Notice 2026-39 (2026-06-10)"
ENERGY_COMMUNITY_MAPPER = "https://energycommunities.gov/energy-community-tax-credit-bonus/"

# --- FEOC / material assistance --------------------------------------------
# OBBBA denies 48E entirely where a project receives material assistance from a
# prohibited foreign entity, measured by a material assistance cost ratio.
# Applies to facilities beginning construction after 2025-12-31 -- which is
# every project in this pipeline. Notice 2026-15 (2026-02-12) supplies safe
# harbor tables for common solar configurations.
FEOC_APPLIES_TO_CONSTRUCTION_AFTER = date(2025, 12, 31)
FEOC_GUIDANCE = "Notice 2026-15 (2026-02-12)"

# --- USDA REAP -------------------------------------------------------------
REAP_GRANTS_HALTED_ON = date(2026, 3, 31)


@dataclass(frozen=True)
class IncentiveStatus:
    """An eligibility determination with the reasoning attached."""

    name: str
    available: bool
    value_fraction: float
    basis: str
    verify_before_quoting: bool = True

    def __str__(self) -> str:
        state = "AVAILABLE" if self.available else "NOT AVAILABLE"
        return f"{self.name}: {state} -- {self.basis}"


@dataclass(frozen=True)
class ITCResult:
    """A resolved Section 48E rate, with its conditions and open questions."""

    total_rate: float
    base_rate: float
    domestic_content_adder: float
    energy_community_adder: float
    pwa_exempt: bool
    eligible: bool
    basis: str
    conditions: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    @property
    def is_fully_resolved(self) -> bool:
        return not self.unresolved

    def summary(self) -> str:
        parts = [f"{self.base_rate:.0%} base"]
        if self.domestic_content_adder:
            parts.append(f"+{self.domestic_content_adder:.0%} domestic content")
        if self.energy_community_adder:
            parts.append(f"+{self.energy_community_adder:.0%} energy community")
        return f"{self.total_rate:.0%} ITC ({', '.join(parts)})"


def _timing_gate(
    quote_date: date,
    began_construction_on: date | None,
    expected_placed_in_service: date | None,
) -> tuple[bool, str]:
    """Whether the project clears the OBBBA timing rules at all."""
    if began_construction_on and began_construction_on <= ITC_BEGIN_CONSTRUCTION_DEADLINE:
        pis = expected_placed_in_service
        if pis is None or pis <= ITC_CONTINUITY_DEADLINE:
            return True, (
                f"construction began {began_construction_on}, within the "
                f"{ITC_BEGIN_CONSTRUCTION_DEADLINE} deadline"
            )
        return False, (
            f"safe-harboured start but placed in service {pis}, after the "
            f"{ITC_CONTINUITY_DEADLINE} continuity deadline"
        )

    pis = expected_placed_in_service
    if pis is None:
        return False, (
            f"begin-construction deadline ({ITC_BEGIN_CONSTRUCTION_DEADLINE}) passed as "
            f"of {quote_date}; supply a placed-in-service date on or before "
            f"{ITC_PLACED_IN_SERVICE_FALLBACK}, or evidence of a safe-harboured start"
        )
    if pis <= ITC_PLACED_IN_SERVICE_FALLBACK:
        return True, (
            f"placed in service {pis}, on or before the "
            f"{ITC_PLACED_IN_SERVICE_FALLBACK} cutoff"
        )
    return False, (
        f"begin-construction deadline passed and placed in service {pis}, after "
        f"{ITC_PLACED_IN_SERVICE_FALLBACK}"
    )


def itc_rate(
    system_kw_ac: float,
    quote_date: date | None = None,
    expected_placed_in_service: date | None = None,
    began_construction_on: date | None = None,
    domestic_content: bool | None = None,
    energy_community: bool | None = None,
) -> ITCResult:
    """Resolve the Section 48E rate for one project.

    `domestic_content` and `energy_community` accept None for "not yet
    determined". Unknown never counts as qualifying -- it lands in
    `unresolved` so it shows up on the quote as an open item rather than
    quietly inflating the credit.
    """
    quote_date = quote_date or VERIFIED_AS_OF
    conditions: list[str] = []
    unresolved: list[str] = []

    eligible, timing_basis = _timing_gate(
        quote_date, began_construction_on, expected_placed_in_service
    )
    if not eligible:
        return ITCResult(
            total_rate=0.0,
            base_rate=0.0,
            domestic_content_adder=0.0,
            energy_community_adder=0.0,
            pwa_exempt=False,
            eligible=False,
            basis=f"Not eligible: {timing_basis}.",
        )

    pwa_exempt = system_kw_ac < ONE_MW_AC_THRESHOLD_KW
    if pwa_exempt:
        base = ITC_BASE_RATE
        conditions.append(
            f"System is {system_kw_ac:,.0f} kW AC, under the {ONE_MW_AC_THRESHOLD_KW:,.0f} kW "
            "threshold, so prevailing wage and apprenticeship do not apply and the "
            "full base rate and full 10-point adders are available."
        )
    else:
        base = ITC_BASE_RATE
        conditions.append(
            f"System is {system_kw_ac:,.0f} kW AC, at or above 1 MW: prevailing wage and "
            f"apprenticeship must be met or the credit drops to {ITC_UNCREDITED_RATE:.0%} "
            "and the adders to 2 points each."
        )

    # Domestic content
    dc_adder = 0.0
    boc_year = (began_construction_on or quote_date).year
    dc_threshold = DOMESTIC_CONTENT_THRESHOLD_BY_BOC_YEAR.get(boc_year, 0.55)
    if domestic_content is True:
        dc_adder = DOMESTIC_CONTENT_ADDER
        conditions.append(
            f"Domestic content claimed: must evidence {dc_threshold:.0%} adjusted "
            f"percentage for a {boc_year} construction start, via the Notice 2025-08 "
            "elective safe harbor tables or supplier cost data."
        )
    elif domestic_content is None:
        unresolved.append(
            f"Domestic content ({DOMESTIC_CONTENT_ADDER:.0%}) undetermined -- requires a "
            f"bill of materials meeting the {dc_threshold:.0%} threshold for a {boc_year} start."
        )

    # Energy community
    ec_adder = 0.0
    if energy_community is True:
        ec_adder = ENERGY_COMMUNITY_ADDER
        conditions.append(
            f"Energy community claimed: confirm the site's census tract appears in "
            f"{ENERGY_COMMUNITY_NOTICE}."
        )
    elif energy_community is None:
        unresolved.append(
            f"Energy community ({ENERGY_COMMUNITY_ADDER:.0%}) undetermined -- look the "
            f"site's census tract up against {ENERGY_COMMUNITY_NOTICE} at "
            f"{ENERGY_COMMUNITY_MAPPER}. Eligibility is per tract and cannot be "
            "inferred from the county."
        )

    # FEOC applies to every project starting construction now.
    boc = began_construction_on or quote_date
    if boc > FEOC_APPLIES_TO_CONSTRUCTION_AFTER:
        conditions.append(
            f"Construction begins {boc}, after {FEOC_APPLIES_TO_CONSTRUCTION_AFTER}, so the "
            f"material assistance cost ratio applies. Failing it denies the credit "
            f"entirely, not just the adders. Use the {FEOC_GUIDANCE} safe harbor tables "
            "and obtain supplier attestations before ordering."
        )

    return ITCResult(
        total_rate=base + dc_adder + ec_adder,
        base_rate=base,
        domestic_content_adder=dc_adder,
        energy_community_adder=ec_adder,
        pwa_exempt=pwa_exempt,
        eligible=True,
        basis=f"Eligible: {timing_basis}.",
        conditions=conditions,
        unresolved=unresolved,
    )


def reap_status(quote_date: date | None = None) -> IncentiveStatus:
    """USDA REAP grant availability.

    Historically the strongest lever on poultry solar economics at up to 50% of
    eligible cost. Currently not awarding grants.
    """
    quote_date = quote_date or VERIFIED_AS_OF

    if quote_date >= REAP_GRANTS_HALTED_ON:
        return IncentiveStatus(
            name="USDA REAP (grant)",
            available=False,
            value_fraction=0.0,
            basis=(
                f"Grant awards halted {REAP_GRANTS_HALTED_ON} pending new regulations "
                "under EO 14315; processing stopped and prior applicants must reapply. "
                "Guaranteed loans still accepted. Do not show a grant line until this "
                "reopens."
            ),
        )

    return IncentiveStatus(
        name="USDA REAP (grant)",
        available=True,
        value_fraction=0.50,
        basis="Historic REAP terms: up to 50% of eligible project cost.",
    )
