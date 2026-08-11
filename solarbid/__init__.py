"""solarbid -- preliminary solar sizing and quoting for Arkansas poultry farms.

Pipeline:
    data     fetch the poultry-cafos barn polygons
    sites    clip to the Peco draw area, screen, cluster houses into farms
    load     geometry -> annual kWh band (never a point estimate)
    siting   roof and ground capacity, Act 278-aware sizing
    incentives  dated ITC / REAP eligibility gates

Nothing here produces a bindable number. It produces a ranked prospect list and
a preliminary system concept; every quote needs interval data, a structural
review for roof mounts, parcel and land cover for ground mounts, and a live
check of the incentive stack.
"""

from .config import Assumptions
from .load import LoadBand, estimate_load
from .siting import recommend_size_kw, surface_capacity

__all__ = [
    "Assumptions",
    "LoadBand",
    "estimate_load",
    "recommend_size_kw",
    "surface_capacity",
]

__version__ = "0.1.0"
