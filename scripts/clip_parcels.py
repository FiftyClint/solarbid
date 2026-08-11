#!/usr/bin/env python3
"""Clip Arkansas statewide parcel data to the Peco AOI, keeping owner fields.

Run once on a machine with normal internet. Produces a small file that can be
committed, after which owner names, mailing addresses and counties are
available to the pipeline everywhere.

Get the source first, free, from the Arkansas GIS Office:

    https://gis.arkansas.gov/product/parcel-polygon-county-assessor-mapping-program-polygon/

or by FTP:

    ftp://ftp.geostor.arkansas.gov/Public_Statewide/
      CADAS_PARCEL_POLYGON_CAMP     (polygons -- preferred, joins on house footprints)
      CADAS_PARCEL_CENTROID_CAMP    (centroids -- smaller, less precise)

Then:

    python scripts/clip_parcels.py --source ~/Downloads/CADAS_PARCEL_POLYGON_CAMP.shp
    git add data/peco_aoi_parcels.gpkg
    git commit -m "Add Peco AOI parcel extract"

The statewide file is large. Only geometry plus the owner, address and county
columns are kept, so the committed extract stays small.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd  # noqa: E402

from solarbid import sites  # noqa: E402
from solarbid.config import AOI_RADIUS_MILES, PECO_POCAHONTAS  # noqa: E402
from solarbid.owners import detect_columns  # noqa: E402

DEFAULT_OUT = Path("data/peco_aoi_parcels.gpkg")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, required=True,
                    help="Downloaded statewide parcel file (.shp, .gdb or .gpkg).")
    ap.add_argument("--radius", type=float, default=AOI_RADIUS_MILES)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--layer", default=None, help="Layer name, for .gdb sources.")
    args = ap.parse_args()

    if not args.source.exists():
        print(f"ERROR: {args.source} does not exist.", file=sys.stderr)
        return 1

    aoi = sites.build_aoi(PECO_POCAHONTAS, args.radius)
    read_kwargs = {"mask": aoi.to_crs("EPSG:4326")}
    if args.layer:
        read_kwargs["layer"] = args.layer

    parcels = gpd.read_file(args.source, **read_kwargs)
    print(f"Clipped {len(parcels):,} parcels within {args.radius:.0f} mi of Pocahontas.")

    if parcels.empty:
        print("ERROR: no parcels in the AOI -- wrong file or wrong layer?",
              file=sys.stderr)
        return 1

    cols = detect_columns(parcels)
    if not cols.usable:
        print(f"ERROR: no owner column found. Columns present:\n  "
              f"{sorted(parcels.columns)}", file=sys.stderr)
        return 1
    if cols.missing():
        print(f"WARNING: no column found for {', '.join(cols.missing())}.")

    keep = [c for c in (cols.owner, cols.address, cols.city, cols.state,
                        cols.zipcode, cols.county, cols.parcel_id) if c]
    print(f"Keeping: {', '.join(keep)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    parcels[keep + ["geometry"]].to_file(args.out, driver="GPKG")
    size_mb = args.out.stat().st_size / 1e6

    print(f"Wrote {args.out} ({size_mb:.1f} MB)")
    if size_mb > 80:
        print("Large for a commit -- try a tighter --radius, or the CENTROID file.")
    else:
        print(f"\nCommit it:\n  git add {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
