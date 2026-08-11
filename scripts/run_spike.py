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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from solarbid import data, incentives, sites  # noqa: E402
from solarbid.config import AOI_RADIUS_MILES, PECO_POCAHONTAS, Assumptions  # noqa: E402
from solarbid.load import attach_load_estimates  # noqa: E402
from solarbid.siting import (  # noqa: E402
    open_ground_area_ft2,
    recommend_size_kw,
    roof_capacity_kw,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--radius", type=float, default=AOI_RADIUS_MILES)
    ap.add_argument("--out", type=Path, default=Path("out/peco_farms.csv"))
    ap.add_argument("--cache", type=Path, default=None)
    args = ap.parse_args()

    assumptions = Assumptions()

    try:
        gpkg = data.ensure_dataset(args.cache)
    except data.DatasetUnavailable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    prov = data.provenance()
    print(f"Source: {prov['source']}")
    print(f"  generated {prov['generated']} from {prov['imagery']}")
    print("  Houses built after the imagery date are absent; counts are a floor.\n")

    aoi = sites.build_aoi(PECO_POCAHONTAS, args.radius)
    barns = sites.load_barns(str(gpkg), aoi)
    print(f"Detections within {args.radius:.0f} mi of Pocahontas: {len(barns):,}")

    screened = sites.screen_barns(barns, assumptions.detection)
    print(f"  passing poultry-house shape screen: {len(screened):,}")

    clustered = sites.cluster_into_farms(screened)
    farms = sites.summarize_farms(clustered)
    farms = sites.to_latlon(farms)
    farms = attach_load_estimates(farms, assumptions.load)
    print(f"  grouped into farms: {len(farms):,}\n")

    # Incentive stack gates the economics, so resolve it once up front and
    # print it -- a run that silently assumes 30% ITC is worse than useless.
    stack = incentives.stack()
    print("Incentive stack:")
    for status in stack:
        print(f"  {status}")
    incentive_fraction = incentives.total_incentive_fraction(stack)
    print(f"  -> {incentive_fraction:.0%} of project cost covered\n")

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
                incentive_fraction=incentive_fraction,
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
