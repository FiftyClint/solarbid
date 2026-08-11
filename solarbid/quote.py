"""Budgetary quotes: the stage-one artifact.

This pipeline has two stages with very different economics.

Stage one is screening. Everything is derived from aerial imagery and public
data, costs nothing per farm, and exists to get a grower to raise their hand.
Precision is not the goal here and chasing it is wasted money -- a farm that
never responds does not deserve an 8760 simulation.

Stage two starts when they respond: twelve months of interval data, a
structural review for roof mounts, parcel and land cover for ground, real
irradiance modelling, and a firm bid.

This module produces stage one. Its numbers carry a range rather than a point,
because the honest uncertainty at this stage is wide and pretending otherwise
is how a screening figure gets mistaken for a bid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .config import ArkansasTariff, Pricing, SitingModel
from .finance import project_finance
from .incentives import ITCResult
from .load import LoadBand
from .siting import blended_value_per_kwh, recommend_size_kw

# Flat planning yield for northeast Arkansas, kWh per kW DC per year. Coarse on
# purpose: at stage one the load band spans 4x, so a precise irradiance model
# would be false precision bolted onto a rough number. PVWatts belongs in
# stage two.
PLANNING_YIELD_KWH_PER_KW = 1450.0


@dataclass(frozen=True)
class MountOption:
    """One mounting approach for a farm."""

    mount: str
    capacity_kw: float
    recommended_kw: float
    gross_cost: float
    net_cost: float
    annual_savings: float
    payback_years: float
    blockers: list[str] = field(default_factory=list)

    @property
    def viable(self) -> bool:
        return self.recommended_kw > 0


@dataclass(frozen=True)
class BudgetaryQuote:
    """A stage-one quote for one farm, with its range and its caveats."""

    farm_id: str
    county: str
    house_count: int
    floor_area_ft2: float

    load_low_kwh: float
    load_mid_kwh: float
    load_high_kwh: float

    system_kw_low: float
    system_kw_mid: float
    system_kw_high: float

    roof: MountOption
    ground: MountOption

    itc: ITCResult
    quote_date: date
    caveats: list[str] = field(default_factory=list)

    @property
    def preferred(self) -> MountOption:
        """Cheaper payback wins, but only among options that are actually viable."""
        options = [o for o in (self.ground, self.roof) if o.viable]
        if not options:
            return self.ground
        return min(options, key=lambda o: o.payback_years)

    def render(self) -> str:
        """Plain-text budgetary summary, suitable for a one-pager."""
        lines = [
            f"BUDGETARY SOLAR ESTIMATE -- {self.farm_id}",
            f"{self.county} County, Arkansas | {self.house_count} houses | "
            f"{self.floor_area_ft2:,.0f} sq ft under roof",
            f"Prepared {self.quote_date}. Budgetary only -- not a bid.",
            "",
            "ESTIMATED ELECTRICITY USE",
            f"  {self.load_mid_kwh:,.0f} kWh/yr, likely range "
            f"{self.load_low_kwh:,.0f} to {self.load_high_kwh:,.0f}",
            "  Derived from house geometry and University of Arkansas audit data.",
            "  Twelve months of your utility bills would narrow this considerably.",
            "",
            "INDICATIVE SYSTEM SIZE",
            f"  {self.system_kw_mid:,.0f} kW DC, range {self.system_kw_low:,.0f} to "
            f"{self.system_kw_high:,.0f} kW depending on actual usage",
            "",
            f"SECTION 48E: {self.itc.summary()}",
        ]

        for option in (self.ground, self.roof):
            lines.append("")
            lines.append(f"{option.mount.upper()} MOUNT")
            if not option.viable:
                lines.append("  Not recommended at this site.")
            else:
                lines.append(f"  System            {option.recommended_kw:,.0f} kW DC")
                lines.append(f"  Installed cost    ${option.gross_cost:,.0f}")
                lines.append(f"  Net after credit  ${option.net_cost:,.0f}")
                lines.append(f"  Annual savings    ${option.annual_savings:,.0f}")
                lines.append(f"  Simple payback    {option.payback_years:.1f} years")
            for blocker in option.blockers:
                lines.append(f"  NOTE: {blocker}")

        if self.itc.unresolved:
            lines.append("")
            lines.append("OPEN ITEMS AFFECTING THE CREDIT")
            for item in self.itc.unresolved:
                lines.append(f"  - {item}")

        lines.append("")
        lines.append("BEFORE THIS BECOMES A BID")
        for caveat in self.caveats:
            lines.append(f"  - {caveat}")

        return "\n".join(lines)


def _mount_option(
    mount: str,
    capacity_kw: float,
    annual_load_kwh: float,
    itc_rate: float,
    tax_rate: float,
    pricing: Pricing,
    tariff: ArkansasTariff,
    siting: SitingModel,
) -> MountOption:
    cost_per_watt = (
        pricing.ground_cost_per_watt if mount == "ground" else pricing.roof_cost_per_watt
    )
    fin_unit = project_finance(1.0, cost_per_watt, itc_rate, tax_rate=tax_rate)

    kw = recommend_size_kw(
        annual_load_kwh=annual_load_kwh,
        max_kw_dc=capacity_kw,
        tariff=tariff,
        pricing=pricing,
        mount=mount,
        net_cost_per_watt=fin_unit.net_cost_per_watt,
    )

    blockers: list[str] = []
    if mount == "roof" and siting.roof_requires_structural_review:
        blockers.append(
            "Roof mount is subject to a structural review. Light-gauge metal over "
            "wood trusses often cannot carry the added load."
        )
    if mount == "ground":
        blockers.append(
            "Ground area estimated from imagery only. Not checked for cropping, "
            "land cover, floodplain or ownership."
        )

    if kw <= 0:
        return MountOption(mount, capacity_kw, 0.0, 0.0, 0.0, 0.0, float("inf"), blockers)

    fin = project_finance(kw, cost_per_watt, itc_rate, tax_rate=tax_rate)
    production = kw * PLANNING_YIELD_KWH_PER_KW
    savings = production * blended_value_per_kwh(production / annual_load_kwh, tariff)

    return MountOption(
        mount=mount,
        capacity_kw=capacity_kw,
        recommended_kw=kw,
        gross_cost=fin.gross_cost,
        net_cost=fin.net_cost,
        annual_savings=savings,
        payback_years=fin.simple_payback_years(savings),
        blockers=blockers,
    )


def budgetary_quote(
    farm_id: str,
    county: str,
    house_count: int,
    floor_area_ft2: float,
    load: LoadBand,
    roof_capacity_kw: float,
    ground_capacity_kw: float,
    itc: ITCResult,
    tax_rate: float = 0.30,
    quote_date: date | None = None,
    pricing: Pricing | None = None,
    tariff: ArkansasTariff | None = None,
    siting: SitingModel | None = None,
) -> BudgetaryQuote:
    """Build a stage-one quote for one farm.

    System size is quoted as a range driven by the load band, not by anything
    to do with irradiance. A farm consuming at the low end of the audit range
    warrants a materially smaller array than one at the high end, and that
    spread dwarfs any error in the yield assumption.
    """
    pricing = pricing or Pricing()
    tariff = tariff or ArkansasTariff()
    siting = siting or SitingModel()
    quote_date = quote_date or date.today()

    best_capacity = max(roof_capacity_kw, ground_capacity_kw)
    unit = project_finance(1.0, pricing.ground_cost_per_watt, itc.total_rate, tax_rate)
    sizes = [
        recommend_size_kw(
            annual_load_kwh=kwh,
            max_kw_dc=best_capacity,
            tariff=tariff,
            pricing=pricing,
            net_cost_per_watt=unit.net_cost_per_watt,
        )
        for kwh in (load.low_kwh, load.mid_kwh, load.high_kwh)
    ]

    ground = _mount_option(
        "ground", ground_capacity_kw, load.mid_kwh, itc.total_rate, tax_rate,
        pricing, tariff, siting,
    )
    roof = _mount_option(
        "roof", roof_capacity_kw, load.mid_kwh, itc.total_rate, tax_rate,
        pricing, tariff, siting,
    )

    caveats = [
        "Twelve months of interval data to confirm consumption and load shape.",
        "Structural review if roof mounted; parcel and land cover if ground mounted.",
        "Utility tariff and interconnection terms confirmed for this meter.",
        "Tax capacity confirmed with your CPA -- the credit and first-year "
        "depreciation only help if there is liability to offset.",
        f"Production modelled at a flat {PLANNING_YIELD_KWH_PER_KW:,.0f} kWh per kW "
        "planning figure; site-specific modelling comes with the firm proposal.",
    ]
    if itc.eligible:
        caveats.append(
            "System energised by 2027-12-31. The credit is not available after that."
        )

    return BudgetaryQuote(
        farm_id=farm_id,
        county=county,
        house_count=house_count,
        floor_area_ft2=floor_area_ft2,
        load_low_kwh=load.low_kwh,
        load_mid_kwh=load.mid_kwh,
        load_high_kwh=load.high_kwh,
        system_kw_low=sizes[0],
        system_kw_mid=sizes[1],
        system_kw_high=sizes[2],
        roof=roof,
        ground=ground,
        itc=itc,
        quote_date=quote_date,
        caveats=caveats,
    )
