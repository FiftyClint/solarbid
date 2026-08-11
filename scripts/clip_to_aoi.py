#!/usr/bin/env python3
"""Clip the national barn dataset down to a committable AOI extract.

Run this ONCE on a machine that can reach Azure blob storage. It writes a small
GeoPackage covering only the Peco draw area, which is small enough to commit to
the repo -- after which the whole pipeline runs anywhere, with no network access
and no 128 MB download.

    python scripts/clip_to_aoi.py                  # downloads, clips, writes
    python scripts/clip_to_aoi.py --source ~/full-usa.gpkg   # already have it

Then commit the result:

    git add -f data/peco_aoi_barns.gpkg
    git commit -m "Add Peco AOI barn extract"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd  # noqa: E402

from solarbid import data, sites  # noqa: E402
from solarbid.config import AOI_RADIUS_MILES, PECO_POCAHONTAS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Path to an already-downloaded national .gpkg. Downloads if omitted.",
    )
    ap.add_argument("--radius", type=float, default=AOI_RADIUS_MILES)
    ap.add_argument("--out", type=Path, default=data.AOI_EXTRACT_PATH)
    args = ap.parse_args()

    if args.source:
        source = args.source
        if not source.exists():
            print(f"ERROR: {source} does not exist.", file=sys.stderr)
            return 1
    else:
        try:
            source = data.ensure_dataset()
        except data.DatasetUnavailable as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    aoi = sites.build_aoi(PECO_POCAHONTAS, args.radius)
    barns = gpd.read_file(source, mask=aoi.to_crs("EPSG:4326"))
    print(f"Clipped {len(barns):,} polygons within {args.radius:.0f} mi of Pocahontas.")

    if barns.empty:
        print("ERROR: no polygons in the AOI -- check the source file.", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    barns.to_file(args.out, driver="GPKG")
    size_mb = args.out.stat().st_size / 1e6

    print(f"Wrote {args.out} ({size_mb:.1f} MB)")
    if size_mb > 50:
        print("That is large for a commit -- consider a tighter --radius.")
    else:
        print(f"\nCommit it so the pipeline runs anywhere:\n  git add -f {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
