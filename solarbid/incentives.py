"""Incentive eligibility gates, as dated rules rather than constants.

The two incentives that move a poultry solar deal -- the federal ITC and USDA
REAP -- are both mid-transition right now. Hard-coding "30% ITC" or "REAP pays
50%" would put stale claims in front of growers, so both are modelled as gates
that take a date and return a status with its basis.

Every fact here is time-sensitive and must be re-verified against primary
sources before a quote is issued. VERIFIED_AS_OF is the honesty marker.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

VERIFIED_AS_OF = date(2026, 8, 11)

# One Big Beautiful Bill Act (signed 2025-07-04) rewrote the Sec. 48E timeline
# for solar and wind.
ITC_BEGIN_CONSTRUCTION_DEADLINE = date(2026, 7, 4)
ITC_PLACED_IN_SERVICE_FALLBACK = date(2027, 12, 31)
ITC_CONTINUITY_DEADLINE = date(2030, 12, 31)
ITC_BASE_RATE = 0.30

# USDA Rural Business Cooperative Service halted all REAP grant awards pending
# new regulations under EO 14315. Guaranteed loans continue.
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


def itc_status(
    quote_date: date | None = None,
    began_construction_on: date | None = None,
    expected_placed_in_service: date | None = None,
) -> IncentiveStatus:
    """Section 48E eligibility for a project quoted on `quote_date`.

    Two surviving paths as of the OBBBA rewrite:

    1. Construction began on or before 2026-07-04 (typically via safe-harboured
       equipment), then placed in service by the continuity deadline.
    2. Missed that, but placed in service by 2027-12-31.

    Note that path 1's deadline has already passed. For any farm we approach
    today, eligibility turns on whether the project can be energised by the end
    of 2027 -- or whether we can place it under safe-harboured equipment already
    procured. That is a real, closing window and it belongs in the sales
    conversation, not buried in a footnote.
    """
    quote_date = quote_date or VERIFIED_AS_OF

    if began_construction_on and began_construction_on <= ITC_BEGIN_CONSTRUCTION_DEADLINE:
        pis = expected_placed_in_service
        if pis is None or pis <= ITC_CONTINUITY_DEADLINE:
            return IncentiveStatus(
                name="Federal ITC (Sec. 48E)",
                available=True,
                value_fraction=ITC_BASE_RATE,
                basis=(
                    f"Construction began {began_construction_on} (on or before the "
                    f"{ITC_BEGIN_CONSTRUCTION_DEADLINE} deadline); must be placed in "
                    f"service by {ITC_CONTINUITY_DEADLINE}."
                ),
            )
        return IncentiveStatus(
            name="Federal ITC (Sec. 48E)",
            available=False,
            value_fraction=0.0,
            basis=(
                f"Safe-harboured start, but placed-in-service date {pis} falls after "
                f"the {ITC_CONTINUITY_DEADLINE} continuity deadline."
            ),
        )

    pis = expected_placed_in_service
    if pis is None:
        return IncentiveStatus(
            name="Federal ITC (Sec. 48E)",
            available=False,
            value_fraction=0.0,
            basis=(
                f"Begin-construction deadline ({ITC_BEGIN_CONSTRUCTION_DEADLINE}) has "
                f"passed as of {quote_date}. Eligibility now requires a placed-in-service "
                f"date on or before {ITC_PLACED_IN_SERVICE_FALLBACK}, or documented "
                f"safe-harboured equipment. Supply one to resolve this."
            ),
        )

    if pis <= ITC_PLACED_IN_SERVICE_FALLBACK:
        return IncentiveStatus(
            name="Federal ITC (Sec. 48E)",
            available=True,
            value_fraction=ITC_BASE_RATE,
            basis=(
                f"No safe-harboured start, but placed in service {pis}, on or before "
                f"the {ITC_PLACED_IN_SERVICE_FALLBACK} cutoff."
            ),
        )

    return IncentiveStatus(
        name="Federal ITC (Sec. 48E)",
        available=False,
        value_fraction=0.0,
        basis=(
            f"Begin-construction deadline passed and placed-in-service date {pis} is "
            f"after {ITC_PLACED_IN_SERVICE_FALLBACK}. Sec. 48E is not available."
        ),
    )


def reap_status(quote_date: date | None = None) -> IncentiveStatus:
    """USDA REAP grant availability.

    REAP has historically been the single strongest lever on poultry solar
    economics, covering up to 50% of eligible project cost. It is currently not
    awarding grants. Any proposal that shows a REAP grant line today is quoting
    a program that is not accepting grant applications.
    """
    quote_date = quote_date or VERIFIED_AS_OF

    if quote_date >= REAP_GRANTS_HALTED_ON:
        return IncentiveStatus(
            name="USDA REAP (grant)",
            available=False,
            value_fraction=0.0,
            basis=(
                f"Grant awards halted {REAP_GRANTS_HALTED_ON} pending new regulations "
                "under EO 14315; application processing stopped and prior applicants "
                "must reapply once new rules are issued. Guaranteed loans are still "
                "being accepted. Do not show a grant line until this reopens."
            ),
        )

    return IncentiveStatus(
        name="USDA REAP (grant)",
        available=True,
        value_fraction=0.50,
        basis="Historic REAP terms: up to 50% of eligible project cost.",
    )


def stack(
    quote_date: date | None = None,
    began_construction_on: date | None = None,
    expected_placed_in_service: date | None = None,
) -> list[IncentiveStatus]:
    """Full incentive stack for a quote, each entry carrying its own basis."""
    return [
        itc_status(quote_date, began_construction_on, expected_placed_in_service),
        reap_status(quote_date),
    ]


def total_incentive_fraction(statuses: list[IncentiveStatus]) -> float:
    """Combined fraction of project cost covered by available incentives.

    Naive sum. Real stacking has ordering and basis-reduction rules -- REAP
    grant proceeds reduce the ITC basis, for one -- so this is a screening
    figure only and must not drive a binding proposal.
    """
    return sum(s.value_fraction for s in statuses if s.available)
