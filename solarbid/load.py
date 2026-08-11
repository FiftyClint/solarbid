"""Estimate annual electricity use for a poultry farm from its geometry.

Chain: roof/floor area -> bird capacity -> live weight sold per year -> kWh.

Every step compounds error, and the final coefficient carries a 4x spread on
its own, so results are always a band. A single-point kWh number from this
module would be false precision and must not be quoted to a grower as fact.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import LoadModel


@dataclass(frozen=True)
class LoadBand:
    """Annual consumption estimate with an explicit uncertainty range."""

    low_kwh: float
    mid_kwh: float
    high_kwh: float
    birds_per_flock: float
    lb_sold_per_year: float

    @property
    def spread_ratio(self) -> float:
        return self.high_kwh / self.low_kwh if self.low_kwh else float("nan")

    def summary(self) -> str:
        return (
            f"{self.mid_kwh:,.0f} kWh/yr "
            f"(range {self.low_kwh:,.0f}-{self.high_kwh:,.0f})"
        )


def estimate_load(floor_area_ft2: float, model: LoadModel | None = None) -> LoadBand:
    """Annual kWh for a farm with the given total house floor area.

    The kWh/1,000 lb coefficients come from University of Arkansas audits of
    real Arkansas broiler houses: 20 low, 44 mean, 83 high. The spread reflects
    genuine farm-to-farm variation in house age, fan efficiency, insulation and
    management -- not measurement noise -- so it cannot be averaged away.
    """
    model = model or LoadModel()

    birds = floor_area_ft2 / model.ft2_per_bird
    lb_per_year = birds * model.avg_market_weight_lb * model.flocks_per_year
    thousand_lb = lb_per_year / 1000.0

    return LoadBand(
        low_kwh=thousand_lb * model.kwh_per_1000lb_low,
        mid_kwh=thousand_lb * model.kwh_per_1000lb_mid,
        high_kwh=thousand_lb * model.kwh_per_1000lb_high,
        birds_per_flock=birds,
        lb_sold_per_year=lb_per_year,
    )


def attach_load_estimates(
    farms: pd.DataFrame, model: LoadModel | None = None
) -> pd.DataFrame:
    """Add load band columns to a farm table from summarize_farms()."""
    if farms.empty:
        return farms.assign(load_low_kwh=[], load_mid_kwh=[], load_high_kwh=[])

    bands = [estimate_load(a, model) for a in farms["floor_area_ft2"]]
    return farms.assign(
        birds_per_flock=[b.birds_per_flock for b in bands],
        lb_sold_per_year=[b.lb_sold_per_year for b in bands],
        load_low_kwh=[b.low_kwh for b in bands],
        load_mid_kwh=[b.mid_kwh for b in bands],
        load_high_kwh=[b.high_kwh for b in bands],
    )


def ventilation_kwh(band: LoadBand, model: LoadModel | None = None) -> float:
    """Portion of annual load attributable to ventilation fans.

    Roughly 88% of poultry house electricity is fans, which is why load is
    concentrated in summer afternoons. That shape is what makes solar
    self-consumption viable here despite Arkansas paying near-nothing for
    exports -- the generation peak and the load peak genuinely coincide.
    """
    model = model or LoadModel()
    return band.mid_kwh * model.ventilation_share


def requires_metered_validation(band: LoadBand, threshold_ratio: float = 3.0) -> bool:
    """Whether this estimate is too wide to quote without interval data.

    At the published coefficient spread essentially every farm trips this. That
    is the honest answer: geometry alone cannot size a system tightly enough to
    bid, and 12 months of utility interval data (or a University of Arkansas
    farm energy audit) is the cheapest way to collapse the band.
    """
    return band.spread_ratio >= threshold_ratio
