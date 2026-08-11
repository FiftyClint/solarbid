"""Tunable constants for the Peco/Pocahontas poultry solar pipeline.

Every number here is a modelling assumption, not a measurement. They are
collected in one module so a quote can be re-run against different assumptions
and so that anything we tighten with real audit data has exactly one home.
"""

from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Area of interest
# --------------------------------------------------------------------------
# Peco Foods' Pocahontas complex. Grower sheds follow drive distance from the
# plant, not county lines, so the AOI is a radius rather than a county list.
# Coordinates are the city centroid; swap for the plant's actual location on
# the southern industrial complex once we have it surveyed.
PECO_POCAHONTAS = (36.2615, -90.9712)  # (lat, lon) WGS84

# Peco reports ~1,000 contracted houses regionally and 400+ in Randolph County
# alone. 50 miles comfortably covers that shed without dragging in the
# Springdale/Batesville complexes.
AOI_RADIUS_MILES = 50.0

# Projected CRS for anything involving length or area. EPSG:26915 is UTM 15N
# (NAD83), which covers northeast Arkansas with sub-metre distortion.
WORKING_CRS = "EPSG:26915"


# --------------------------------------------------------------------------
# Barn detection filtering
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DetectionFilter:
    """Screens Microsoft poultry-cafos polygons down to credible barns.

    The published dataset is already filtered and deduplicated, but it is a
    model output over 1m NAIP and still contains machine sheds, long equipment
    barns and split detections. Poultry houses are unusually easy to screen on
    shape: they are long, narrow, and highly consistent.
    """

    min_probability: float = 0.5
    min_area_m2: float = 750.0      # ~8,000 ft2, below a real commercial house
    max_area_m2: float = 5000.0     # ~54,000 ft2, above the largest modern house
    min_aspect_ratio: float = 4.0   # houses run 8-15:1; 4 is a permissive floor
    min_length_m: float = 90.0      # ~300 ft
    min_width_m: float = 9.0        # ~30 ft; below this it is a fence or field edge
    max_width_m: float = 25.0       # ~82 ft


# --------------------------------------------------------------------------
# Farm clustering
# --------------------------------------------------------------------------
# Barns closer than this belong to one farm: one owner, one service, one quote.
# Poultry houses sit 40-60ft apart within a farm; neighbouring farms are
# typically a quarter mile or more away.
FARM_CLUSTER_DISTANCE_M = 200.0


# --------------------------------------------------------------------------
# Load model
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class LoadModel:
    """Floor area -> birds -> live weight sold -> annual kWh.

    The kWh coefficients are University of Arkansas audit results across real
    Arkansas broiler houses: a range of 20 to 83 kWh per 1,000 lb of broiler
    sold with a mean of 44. That 4x spread is the dominant uncertainty in the
    whole tool and is why every load estimate is returned as a band.
    """

    ft2_per_bird: float = 0.9          # big-bird programs run closer to 1.0+
    avg_market_weight_lb: float = 6.5
    flocks_per_year: float = 5.5

    kwh_per_1000lb_low: float = 20.0
    kwh_per_1000lb_mid: float = 44.0
    kwh_per_1000lb_high: float = 83.0

    # ~88% of house electricity is ventilation (69% tunnel/end-wall, 19%
    # sidewall) per the same audits. This drives the summer-afternoon peak that
    # makes solar coincidence unusually good on poultry.
    ventilation_share: float = 0.88


# --------------------------------------------------------------------------
# Array siting
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SitingModel:
    """Converts available surface into installable DC capacity.

    We quote roof and ground mount side by side, so both densities are here.
    """

    # Fraction of a single roof plane actually usable after ridge vents,
    # tunnel-fan ends, sidewall inlets, walkways and fire setbacks.
    roof_usable_fraction: float = 0.55

    # Modern modules land near 20 W/ft2 of module area; derate for racking gaps.
    roof_watts_per_ft2: float = 18.0

    # Ground mount at typical fixed-tilt row spacing for this latitude,
    # inclusive of inter-row shading gaps (~4 acres/MW).
    ground_watts_per_ft2: float = 7.0

    # How far from the barn cluster we will look for open ground before
    # trenching cost makes it uneconomic.
    ground_search_radius_m: float = 150.0

    # Roof structural capacity is a per-site engineering call. Light-gauge
    # metal over wood trusses frequently cannot take the added load, which is
    # why ground mount is quoted alongside rather than as a fallback.
    roof_requires_structural_review: bool = True


# --------------------------------------------------------------------------
# Arkansas economics (Act 278 of 2023)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class ArkansasTariff:
    """Post-Act-278 economics.

    Systems energised after 2024-09-30 no longer receive 1:1 net metering.
    On-site consumption avoids the retail rate; exports are credited at avoided
    cost. The gap between the two is roughly 5x, which means these systems must
    be sized to self-consumption rather than to annual bill offset. Sizing to
    "100% of the annual bill" produces economics that are wrong by a wide
    margin in Arkansas.
    """

    retail_rate_per_kwh: float = 0.12
    export_credit_per_kwh: float = 0.025   # avoided cost, utility-specific
    grandfathered_1to1_deadline: str = "2024-09-30"

    # Act 278 also caps projects at 5 MW, ends indefinite credit rollover, and
    # limits credit application to a 100-mile radius.
    max_project_kw: float = 5000.0

    # Co-ops in this footprint (Craighead, Clay County, Farmers, Woodruff) each
    # set their own tariffs and demand charges. There is no clean API for these
    # -- they are hand-entered per utility and must be verified per quote.
    tariff_verified: bool = False


@dataclass(frozen=True)
class Pricing:
    """Installed cost before incentives, in $/W DC.

    Roof carries no racking ballast, no trenching and no site prep, so it comes
    in a dime under ground. That 10c gap is what makes the mount comparison on
    a quote meaningful: roof wins on economics wherever the structure can
    actually carry it, which is exactly the question the structural review
    answers.
    """

    roof_cost_per_watt: float = 2.00
    ground_cost_per_watt: float = 2.10


@dataclass(frozen=True)
class Assumptions:
    """The full assumption set behind a single quote run."""

    detection: DetectionFilter = field(default_factory=DetectionFilter)
    load: LoadModel = field(default_factory=LoadModel)
    siting: SitingModel = field(default_factory=SitingModel)
    tariff: ArkansasTariff = field(default_factory=ArkansasTariff)
    pricing: Pricing = field(default_factory=Pricing)


# --------------------------------------------------------------------------
# Source data
# --------------------------------------------------------------------------
# Microsoft poultry-cafos national predictions: 360,857 filtered and
# deduplicated barn polygons derived from 1m USDA NAIP imagery.
# Code is MIT; the dataset is under the Open Use of Data Agreement v1.0.
CAFO_DATASET_URL = (
    "https://researchlabwuopendata.blob.core.windows.net/poultry-cafo/"
    "full-usa-3-13-2021_filtered_deduplicated.gpkg"
)

# The published predictions were generated 2021-03-13 from NAIP flown roughly
# 2019-2020. Peco expanded the Pocahontas complex through 2020-21, so houses
# built after the imagery date are absent. Re-running the released U-Net on
# current NAIP is the fix; until then treat counts as a floor, not a census.
CAFO_DATASET_VINTAGE = "2021-03-13"
CAFO_IMAGERY_ERA = "2019-2020 NAIP"
