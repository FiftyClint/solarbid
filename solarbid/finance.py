"""Net project cost after the ITC, bonus depreciation and any grant.

Separated from `incentives` because eligibility and monetization are different
questions. A grower can be fully eligible for a 50% credit and still be unable
to use it, which is the single most common way a poultry solar proposal falls
apart after signature.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# OBBBA restored 100% bonus depreciation permanently for qualified property
# acquired after 2025-01-19.
BONUS_DEPRECIATION_FRACTION = 1.0

# Claiming the ITC reduces depreciable basis by half the credit, so a 50% ITC
# leaves 75% of cost depreciable.
ITC_BASIS_REDUCTION_SHARE = 0.50

# OBBBA also removed the 5-year MACRS classification for solar energy property
# where construction began after 2024-12-31. With 100% bonus depreciation the
# recovery period is largely moot -- it only bites if the taxpayer elects out
# of bonus, at which point the schedule is materially slower than the 5-year
# MACRS most poultry solar proposals still assume.
MACRS_5YR_REPEALED_FOR_CONSTRUCTION_AFTER = "2024-12-31"

# Section 6418 lets an unusable credit be sold for cash. Market clearing prices
# for small credits sit below par and small transactions carry fixed diligence
# cost, so a 50 kW farm system will rarely transfer economically on its own.
TRANSFER_DISCOUNT = 0.92


@dataclass(frozen=True)
class ProjectFinance:
    """Gross-to-net cost for one system, with monetization caveats attached."""

    system_kw: float
    gross_cost: float
    itc_rate: float
    itc_amount: float
    depreciable_basis: float
    depreciation_shield: float
    grant_amount: float
    net_cost: float
    caveats: list[str] = field(default_factory=list)

    @property
    def net_cost_per_watt(self) -> float:
        return self.net_cost / (self.system_kw * 1000.0) if self.system_kw else 0.0

    @property
    def gross_cost_per_watt(self) -> float:
        return self.gross_cost / (self.system_kw * 1000.0) if self.system_kw else 0.0

    @property
    def total_benefit_fraction(self) -> float:
        return (
            (self.gross_cost - self.net_cost) / self.gross_cost if self.gross_cost else 0.0
        )

    def simple_payback_years(self, annual_savings: float) -> float:
        if annual_savings <= 0:
            return float("inf")
        return self.net_cost / annual_savings


def project_finance(
    system_kw: float,
    cost_per_watt: float,
    itc_rate: float,
    tax_rate: float = 0.30,
    grant_fraction: float = 0.0,
    bonus_depreciation: float = BONUS_DEPRECIATION_FRACTION,
) -> ProjectFinance:
    """Net cost after credit, depreciation and grant.

    `tax_rate` is the combined marginal federal and Arkansas rate at which
    depreciation deductions are actually used. It is a property of the grower,
    not the project, and assuming a high rate is the easiest way to make a bad
    deal look good.

    Order of operations: a grant reduces eligible basis before the credit is
    computed, then the credit reduces depreciable basis by half its value.
    """
    gross = system_kw * 1000.0 * cost_per_watt
    caveats: list[str] = []

    grant = gross * grant_fraction
    eligible_basis = gross - grant

    itc_amount = eligible_basis * itc_rate
    depreciable_basis = eligible_basis - (itc_amount * ITC_BASIS_REDUCTION_SHARE)
    shield = depreciable_basis * bonus_depreciation * tax_rate

    net = gross - grant - itc_amount - shield

    if itc_rate > 0:
        caveats.append(
            f"Assumes the grower can absorb ${itc_amount:,.0f} of credit and "
            f"${shield:,.0f} of first-year deduction against actual tax liability. "
            "Contract growers frequently cannot. Confirm tax capacity with their CPA "
            "before this number is presented as the price."
        )
    if bonus_depreciation >= 1.0:
        caveats.append(
            "Assumes 100% bonus depreciation taken in year one. If the grower elects "
            "out, note that OBBBA repealed 5-year MACRS for solar where construction "
            f"began after {MACRS_5YR_REPEALED_FOR_CONSTRUCTION_AFTER}, so the fallback "
            "schedule is slower than most proposals assume."
        )
    if tax_rate > 0:
        caveats.append(
            "Passive activity rules may defer credit and deduction use where the "
            "grower is not materially participating in the entity holding the system."
        )

    return ProjectFinance(
        system_kw=system_kw,
        gross_cost=gross,
        itc_rate=itc_rate,
        itc_amount=itc_amount,
        depreciable_basis=depreciable_basis,
        depreciation_shield=shield,
        grant_amount=grant,
        net_cost=net,
        caveats=caveats,
    )


def transfer_value(itc_amount: float, discount: float = TRANSFER_DISCOUNT) -> float:
    """Cash a Section 6418 credit sale would realize.

    Relevant when the grower lacks tax appetite. Small credits clear below par
    and carry fixed diligence cost, so aggregating several farms into one
    transfer is usually the only way this works at poultry-farm scale.
    """
    return itc_amount * discount
