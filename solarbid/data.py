"""Fetching and caching the source barn-detection dataset."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path

from .config import CAFO_DATASET_URL, CAFO_IMAGERY_ERA, CAFO_DATASET_VINTAGE

DEFAULT_CACHE = Path(os.environ.get("SOLARBID_CACHE", "./data")).expanduser()


class DatasetUnavailable(RuntimeError):
    """Raised when the source dataset cannot be retrieved."""


def dataset_path(cache_dir: Path | None = None) -> Path:
    cache = Path(cache_dir or DEFAULT_CACHE)
    return cache / "full-usa-3-13-2021_filtered_deduplicated.gpkg"


def ensure_dataset(cache_dir: Path | None = None, url: str = CAFO_DATASET_URL) -> Path:
    """Download the poultry-cafos national predictions if not already cached.

    The file is ~128 MB and hosted on Azure blob storage. Some managed network
    environments block that host at the egress policy layer; when that happens
    the fix is to allowlist the host or fetch the file out-of-band and drop it
    in the cache directory, not to hunt for a mirror.
    """
    target = dataset_path(cache_dir)
    if target.exists() and target.stat().st_size > 0:
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=300) as resp, open(target, "wb") as fh:
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        if target.exists():
            target.unlink()
        raise DatasetUnavailable(
            f"Could not download {url}: {exc}\n"
            f"If this is a 403 from an egress proxy, the host is blocked by policy. "
            f"Allowlist it or place the .gpkg at {target} manually."
        ) from exc

    return target


def provenance() -> dict[str, str]:
    """Where the barn polygons came from and how stale they are.

    Worth surfacing on any output: the predictions were generated from NAIP
    flown roughly 2019-2020, while Peco expanded the Pocahontas complex through
    2020-21. Houses built after the imagery date simply are not in this file,
    so counts derived from it are a floor rather than a census.
    """
    return {
        "source": "microsoft/poultry-cafos national predictions",
        "url": CAFO_DATASET_URL,
        "generated": CAFO_DATASET_VINTAGE,
        "imagery": CAFO_IMAGERY_ERA,
        "code_license": "MIT",
        "data_license": "Open Use of Data Agreement v1.0",
    }
