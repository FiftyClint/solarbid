"""Turn raw barn-detection polygons into farm-level sites we can quote.

Pipeline: load predictions -> clip to the Peco draw area -> screen out
non-poultry structures on shape -> derive per-house geometry -> cluster houses
into farms, because a farm is one owner, one service and one quote.
"""

from __future__ import annotations

import math

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon

from .config import (
    AOI_RADIUS_MILES,
    FARM_CLUSTER_DISTANCE_M,
    PECO_POCAHONTAS,
    WORKING_CRS,
    DetectionFilter,
)

METERS_PER_MILE = 1609.344
M2_PER_FT2 = 0.09290304


def build_aoi(
    center_latlon: tuple[float, float] = PECO_POCAHONTAS,
    radius_miles: float = AOI_RADIUS_MILES,
    crs: str = WORKING_CRS,
) -> gpd.GeoSeries:
    """Circular area of interest around the processing plant.

    Grower sheds are set by drive distance from the plant, so a radius models
    the real catchment better than a county list does.
    """
    lat, lon = center_latlon
    center = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(crs)
    return center.buffer(radius_miles * METERS_PER_MILE)


def load_barns(path: str, aoi: gpd.GeoSeries | None = None) -> gpd.GeoDataFrame:
    """Read the poultry-cafos GeoPackage, clipped to the AOI if given.

    The national file is 128 MB / 360k polygons, so we push the AOI down into
    the read as a spatial filter rather than loading the country into memory.
    """
    mask = None
    if aoi is not None:
        mask = aoi.to_crs("EPSG:4326")

    barns = gpd.read_file(path, mask=mask)
    if barns.crs is None:
        raise ValueError(f"{path} has no CRS; cannot place these polygons.")
    return barns.to_crs(WORKING_CRS)


def _oriented_dimensions(geom: Polygon) -> tuple[float, float, float]:
    """Length, width and ridge azimuth of a barn from its bounding rectangle.

    Poultry houses are near-perfect rectangles, so the minimum rotated
    rectangle recovers their true footprint closely. Azimuth is degrees
    clockwise from north along the long axis (the ridge line).
    """
    rect = geom.minimum_rotated_rectangle
    x, y = rect.exterior.coords.xy
    edges = [
        (
            math.hypot(x[i + 1] - x[i], y[i + 1] - y[i]),
            math.atan2(x[i + 1] - x[i], y[i + 1] - y[i]),
        )
        for i in range(4)
    ]
    edges.sort(key=lambda e: e[0], reverse=True)

    length, bearing = edges[0]
    width = edges[-1][0]
    azimuth = math.degrees(bearing) % 180.0  # ridge is undirected
    return length, width, azimuth


def screen_barns(
    barns: gpd.GeoDataFrame, flt: DetectionFilter | None = None
) -> gpd.GeoDataFrame:
    """Drop detections whose shape is not consistent with a poultry house.

    Machine sheds, hay barns and split detections all survive the published
    filtering. Poultry houses are distinctive: 300-600ft long, under ~70ft
    wide, and 8-15:1 in aspect. Screening on shape is far more reliable here
    than screening on the model's own confidence.
    """
    flt = flt or DetectionFilter()
    if barns.empty:
        return barns.assign(length_m=[], width_m=[], azimuth_deg=[], area_m2=[])

    dims = [_oriented_dimensions(g) for g in barns.geometry]
    out = barns.copy()
    out["length_m"] = [d[0] for d in dims]
    out["width_m"] = [d[1] for d in dims]
    out["azimuth_deg"] = [d[2] for d in dims]
    out["area_m2"] = out.geometry.area
    out["aspect_ratio"] = out["length_m"] / out["width_m"].replace(0, np.nan)

    keep = (
        out["area_m2"].between(flt.min_area_m2, flt.max_area_m2)
        & (out["aspect_ratio"] >= flt.min_aspect_ratio)
        & (out["length_m"] >= flt.min_length_m)
        & out["width_m"].between(flt.min_width_m, flt.max_width_m)
    )

    # The released dataset does not guarantee a probability column name across
    # versions; only apply the confidence gate when we actually find one.
    for col in ("probability", "prob", "pred_prob"):
        if col in out.columns:
            keep &= out[col].fillna(1.0) >= flt.min_probability
            break

    return out[keep].reset_index(drop=True)


def cluster_into_farms(
    barns: gpd.GeoDataFrame, distance_m: float = FARM_CLUSTER_DISTANCE_M
) -> gpd.GeoDataFrame:
    """Group neighbouring houses into farms.

    Houses on one farm sit 40-60ft apart; the next farm is typically a quarter
    mile away. Buffering by half the threshold and dissolving turns that
    spacing into connected components without needing a clustering library.
    """
    if barns.empty:
        return barns.assign(farm_id=[])

    merged = barns.geometry.buffer(distance_m / 2.0).union_all()
    clusters = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries(
            [merged] if merged.geom_type == "Polygon" else list(merged.geoms),
            crs=barns.crs,
        )
    )
    clusters["farm_id"] = [f"farm_{i:05d}" for i in range(len(clusters))]

    joined = gpd.sjoin(
        barns, clusters, how="left", predicate="intersects"
    ).drop(columns=["index_right"])
    # A barn can touch two buffers where clusters nearly merge; keep the first.
    return joined[~joined.index.duplicated(keep="first")].reset_index(drop=True)


def summarize_farms(barns: gpd.GeoDataFrame) -> pd.DataFrame:
    """Collapse screened, clustered houses into one row per farm.

    Ridge azimuth is taken from the largest house rather than averaged, since
    houses on a farm are near-always parallel and averaging across the 0/180
    wrap would produce nonsense.
    """
    if barns.empty:
        return pd.DataFrame(
            columns=["farm_id", "house_count", "floor_area_ft2", "ridge_azimuth_deg"]
        )

    def _reduce(group: pd.DataFrame) -> pd.Series:
        biggest = group.loc[group["area_m2"].idxmax()]
        centroid = group.geometry.union_all().centroid
        return pd.Series(
            {
                "house_count": len(group),
                "floor_area_ft2": group["area_m2"].sum() / M2_PER_FT2,
                "mean_house_length_ft": group["length_m"].mean() / 0.3048,
                "mean_house_width_ft": group["width_m"].mean() / 0.3048,
                "ridge_azimuth_deg": biggest["azimuth_deg"],
                "easting": centroid.x,
                "northing": centroid.y,
            }
        )

    farms = barns.groupby("farm_id", group_keys=False).apply(
        _reduce, include_groups=False
    )
    return farms.reset_index()


def to_latlon(farms: pd.DataFrame, crs: str = WORKING_CRS) -> pd.DataFrame:
    """Attach WGS84 lat/lon, which is what PVWatts and mapping links want."""
    if farms.empty:
        return farms.assign(lat=[], lon=[])
    pts = gpd.GeoSeries(
        gpd.points_from_xy(farms["easting"], farms["northing"]), crs=crs
    ).to_crs("EPSG:4326")
    return farms.assign(lat=pts.y.values, lon=pts.x.values)
