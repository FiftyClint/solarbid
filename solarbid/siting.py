"""Roof and ground mount capacity, and Act 278-aware system sizing.

We quote both mounting types side by side. On a poultry farm neither surface is
the binding constraint -- a single house roof could hold several hundred kW,
far more than the meter can absorb. The binding constraint in Arkansas is how
much generation the farm can consume on site, because exports are credited at
roughly a fifth of the retail rate.
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd

from .config import ArkansasTariff, Pricing, SitingModel

M2_PER_FT2 = 0.09290304


@dataclass(frozen=True)
class SurfaceCapacity:
    """What each mounting option could physically hold, before economics."""

    roof_kw_dc: float
    ground_kw_dc: float
    roof_needs_structural_review: bool
    ground_area_unverified: bool

    @property
    def best_kw_dc(self) -> float:
        return max(self.roof_kw_dc, self.ground_kw_dc)


def roof_capacity_kw(
    floor_area_ft2: float, siting: SitingModel | None = None
) -> float:
    """Installable DC capacity on the better-oriented roof plane.

    A gabled poultry house presents two planes; only one is worth using when
    the ridge runs east-west, and both are mediocre when it runs north-south.
    We size the single best plane, which is half the footprint, then derate for
    ridge vents, tunnel-fan ends, sidewall inlets and setbacks.
    """
    siting = siting or SitingModel()
    best_plane_ft2 = floor_area_ft2 / 2.0
    usable_ft2 = best_plane_ft2 * siting.roof_usable_fraction
    return usable_ft2 * siting.roof_watts_per_ft2 / 1000.0


def ground_capacity_kw(
    open_area_ft2: float, siting: SitingModel | None = None
) -> float:
    """Installable DC capacity on adjacent open ground at fixed-tilt spacing."""
    siting = siting or SitingModel()
    return open_area_ft2 * siting.ground_watts_per_ft2 / 1000.0


def open_ground_area_ft2(
    farm_barns: gpd.GeoDataFrame, siting: SitingModel | None = None
) -> float:
    """Rough open area near the barn cluster available for a ground array.

    This is land that is merely *not built on* -- the polygons tell us nothing
    about whether it is cropped, wooded, in a floodplain, or even owned by the
    grower. It is a screening number for ranking prospects, and every ground
    quote needs parcel boundaries and land cover before it goes out.
    """
    siting = siting or SitingModel()
    if farm_barns.empty:
        return 0.0

    envelope = farm_barns.geometry.buffer(siting.ground_search_radius_m).union_all()
    built = farm_barns.geometry.union_all()
    return (envelope.area - built.area) / M2_PER_FT2


def surface_capacity(
    floor_area_ft2: float,
    open_area_ft2: float,
    siting: SitingModel | None = None,
) -> SurfaceCapacity:
    """Capacity for both mounting options on one farm."""
    siting = siting or SitingModel()
    return SurfaceCapacity(
        roof_kw_dc=roof_capacity_kw(floor_area_ft2, siting),
        ground_kw_dc=ground_capacity_kw(open_area_ft2, siting),
        roof_needs_structural_review=siting.roof_requires_structural_review,
        ground_area_unverified=True,
    )


# --------------------------------------------------------------------------
# Act 278 sizing
# --------------------------------------------------------------------------
# Self-consumed fraction as a function of annual PV production divided by
# annual load. Poultry holds high self-consumption further up this curve than a
# typical commercial site because ~88% of its load is ventilation fans running
# on summer afternoons, coincident with peak generation.
#
# PLACEHOLDER: these anchors are engineering judgement, not measurement. They
# must be replaced with an 8760 simulation against real interval data before
# any of this reaches a binding proposal.
_SELF_CONSUMPTION_CURVE = [
    (0.00, 1.00),
    (0.30, 0.95),
    (0.50, 0.88),
    (0.75, 0.80),
    (1.00, 0.70),
    (1.50, 0.55),
    (2.00, 0.44),
]


def self_consumed_fraction(pv_to_load_ratio: float) -> float:
    """Interpolate the share of generation consumed on site."""
    pts = _SELF_CONSUMPTION_CURVE
    if pv_to_load_ratio <= pts[0][0]:
        return pts[0][1]
    if pv_to_load_ratio >= pts[-1][0]:
        return pts[-1][1]

    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= pv_to_load_ratio <= x1:
            span = x1 - x0
            return y0 + (y1 - y0) * ((pv_to_load_ratio - x0) / span)
    return pts[-1][1]


def blended_value_per_kwh(
    pv_to_load_ratio: float, tariff: ArkansasTariff | None = None
) -> float:
    """Average value of a generated kWh once exports are priced at avoided cost."""
    tariff = tariff or ArkansasTariff()
    sc = self_consumed_fraction(pv_to_load_ratio)
    return sc * tariff.retail_rate_per_kwh + (1 - sc) * tariff.export_credit_per_kwh


def recommend_size_kw(
    annual_load_kwh: float,
    max_kw_dc: float,
    specific_yield_kwh_per_kw: float = 1450.0,
    tariff: ArkansasTariff | None = None,
    pricing: Pricing | None = None,
    mount: str = "ground",
    target_payback_years: float = 12.0,
    incentive_fraction: float = 0.0,
) -> float:
    """Largest array whose marginal kW still pays back inside the target.

    This is the core of the Arkansas logic. Under 1:1 net metering the answer
    was simply "offset the annual bill". Post-Act 278 each additional kW is
    worth progressively less, because the incremental generation increasingly
    spills to export at avoided cost. We walk the array up in 5 kW steps and
    stop when the marginal kW no longer earns out.

    `incentive_fraction` matters more than it looks. At current pricing and a
    12c retail rate, unsubsidised simple payback is roughly 13.5 years, which
    clears no reasonable target -- so with the ITC gone and REAP halted, this
    function correctly returns zero. That is not a bug to work around; it is
    the finding. Pass the fraction actually available from incentives.stack().
    """
    tariff = tariff or ArkansasTariff()
    pricing = pricing or Pricing()
    gross_cost_per_watt = (
        pricing.ground_cost_per_watt if mount == "ground" else pricing.roof_cost_per_watt
    )
    cost_per_watt = gross_cost_per_watt * (1.0 - incentive_fraction)

    if annual_load_kwh <= 0 or max_kw_dc <= 0:
        return 0.0

    step_kw = 5.0
    chosen = 0.0
    size = step_kw
    while size <= min(max_kw_dc, tariff.max_project_kw):
        prev_prod = (size - step_kw) * specific_yield_kwh_per_kw
        prod = size * specific_yield_kwh_per_kw

        prev_val = prev_prod * blended_value_per_kwh(prev_prod / annual_load_kwh, tariff)
        val = prod * blended_value_per_kwh(prod / annual_load_kwh, tariff)

        marginal_annual_value = val - prev_val
        marginal_cost = step_kw * 1000.0 * cost_per_watt

        if marginal_annual_value <= 0:
            break
        if marginal_cost / marginal_annual_value > target_payback_years:
            break

        chosen = size
        size += step_kw

    return chosen
