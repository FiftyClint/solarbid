#!/usr/bin/env python3
"""Count and characterise poultry farms in the Peco Pocahontas draw area.

This is the decisive cheap step: before building quoting machinery, confirm how
many real farms sit inside the catchment and what they look like. Peco reports
~1,000 contracted houses regionally and 400+ in Randolph County; this script
checks that against the imagery-derived polygons.

Usage:
    python scripts/run_spike.py [--radius 50] [--out out/peco_farms.csv]
"""

from __future__ import annotations

import argparse
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from solarbid import data, incentives, sites  # noqa: E402
from solarbid.config import AOI_RADIUS_MILES, PECO_POCAHONTAS, Assumptions  # noqa: E402
from solarbid.finance import project_finance  # noqa: E402
from solarbid.load import attach_load_estimates  # noqa: E402
from solarbid.siting import (  # noqa: E402
    open_ground_area_ft2,
    recommend_size_kw,
    roof_capacity_kw,
)


# Representative farm system size, used to resolve the ITC rate once for the
# whole run. Every system in this pipeline sits far under the 1 MW AC threshold,
# so the rate does not vary farm to farm.
REPRESENTATIVE_KW_AC = 50.0


def _tristate(value: str) -> bool | None:
    """yes/no/unknown -- unknown must never resolve to a favourable assumption."""
    return {"yes": True, "no": False, "unknown": None}[value]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--radius", type=float, default=AOI_RADIUS_MILES)
    ap.add_argument("--out", type=Path, default=Path("out/peco_farms.csv"))
    ap.add_argument("--cache", type=Path, default=None)
    ap.add_argument(
        "--placed-in-service",
        type=date.fromisoformat,
        default=date(2027, 12, 1),
        help="Target energisation date. Must be on or before 2027-12-31 for the ITC.",
    )
    ap.add_argument(
        "--domestic-content",
        type=_tristate,
        choices=["yes", "no", "unknown"],
        default="unknown",
    )
    ap.add_argument(
        "--energy-community",
        type=_tristate,
        choices=["yes", "no", "unknown"],
        default="unknown",
        help="Per census tract, from IRS Notice 2026-39. Do not infer from county.",
    )
    ap.add_argument(
        "--tax-rate",
        type=float,
        default=0.30,
        help="Grower's combined marginal rate for depreciation deductions.",
    )
    args = ap.parse_args()

    assumptions = Assumptions()

    try:
        gpkg, preclipped = data.resolve_barn_source(args.cache)
    except data.DatasetUnavailable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    prov = data.provenance()
    print(f"Source: {prov['source']}")
    print(f"  generated {prov['generated']} from {prov['imagery']}")
    if preclipped:
        print(f"  using committed AOI extract: {gpkg}")
    print("  Houses built after the imagery date are absent; counts are a floor.\n")

    # The committed extract is already clipped, so re-masking it is wasted work.
    aoi = None if preclipped else sites.build_aoi(PECO_POCAHONTAS, args.radius)
    barns = sites.load_barns(str(gpkg), aoi)
    print(f"Detections within {args.radius:.0f} mi of Pocahontas: {len(barns):,}")

    screened = sites.screen_barns(barns, assumptions.detection)
    print(f"  passing poultry-house shape screen: {len(screened):,}")

    clustered = sites.cluster_into_farms(screened)
    farms = sites.summarize_farms(clustered)
    farms = sites.to_latlon(farms)
    farms = attach_load_estimates(farms, assumptions.load)
    print(f"  grouped into farms: {len(farms):,}\n")

    # Resolve the incentive stack once up front and print it. A run that
    # silently assumes 30% ITC is worse than useless.
    itc = incentives.itc_rate(
        system_kw_ac=REPRESENTATIVE_KW_AC,
        expected_placed_in_service=args.placed_in_service,
        domestic_content=args.domestic_content,
        energy_community=args.energy_community,
    )
    print(f"Section 48E: {itc.summary()}")
    print(f"  {itc.basis}")
    for condition in itc.conditions:
        print(f"  [must hold]   {condition}")
    for open_item in itc.unresolved:
        print(f"  [UNRESOLVED]  {open_item}")
    print(f"  {incentives.reap_status()}\n")

    fin = project_finance(
        system_kw=REPRESENTATIVE_KW_AC,
        cost_per_watt=assumptions.pricing.ground_cost_per_watt,
        itc_rate=itc.total_rate,
        tax_rate=args.tax_rate,
    )
    print(
        f"Net cost: ${fin.net_cost_per_watt:.2f}/W "
        f"(gross ${fin.gross_cost_per_watt:.2f}/W, "
        f"{fin.total_benefit_fraction:.0%} covered by credit and depreciation)\n"
    )

    # Per-farm siting: both mounting options, then Act 278-aware sizing.
    roof_kw, ground_kw, rec_kw = [], [], []
    for _, farm in farms.iterrows():
        farm_barns = clustered[clustered["farm_id"] == farm["farm_id"]]
        r_kw = roof_capacity_kw(farm["floor_area_ft2"], assumptions.siting)
        g_kw = (
            open_ground_area_ft2(farm_barns, assumptions.siting)
            * assumptions.siting.ground_watts_per_ft2
            / 1000.0
        )
        roof_kw.append(r_kw)
        ground_kw.append(g_kw)
        rec_kw.append(
            recommend_size_kw(
                annual_load_kwh=farm["load_mid_kwh"],
                max_kw_dc=max(r_kw, g_kw),
                tariff=assumptions.tariff,
                pricing=assumptions.pricing,
                net_cost_per_watt=fin.net_cost_per_watt,
            )
        )

    farms["roof_capacity_kw"] = roof_kw
    farms["ground_capacity_kw"] = ground_kw
    farms["recommended_kw"] = rec_kw

    args.out.parent.mkdir(parents=True, exist_ok=True)
    farms.to_csv(args.out, index=False)

    print(f"Houses:            {int(farms['house_count'].sum()):,}")
    print(f"Farms:             {len(farms):,}")
    print(f"Median houses/farm:{farms['house_count'].median():.0f}")
    print(f"Total load (mid):  {farms['load_mid_kwh'].sum() / 1e6:,.1f} GWh/yr")
    print(f"Recommended DC:    {farms['recommended_kw'].sum() / 1000:,.1f} MW")
    print(f"\nWrote {args.out}")
    print(
        "\nEvery size above is pre-verification: no interval data, no structural "
        "review, no parcel or land cover check."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
