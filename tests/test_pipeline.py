"""Logic tests using synthetic barn geometry.

The real barn polygons live behind a 128 MB download, so these build houses of
known dimensions in the working CRS and assert the pipeline recovers them.
"""

from __future__ import annotations

from datetime import date

import geopandas as gpd
import pytest
from shapely.geometry import box

from solarbid import incentives, sites
from solarbid.config import WORKING_CRS, ArkansasTariff, LoadModel, SitingModel
from solarbid.load import estimate_load, requires_metered_validation
from solarbid.siting import (
    blended_value_per_kwh,
    recommend_size_kw,
    roof_capacity_kw,
    self_consumed_fraction,
)

FT = 0.3048
HOUSE_LEN_M = 500 * FT   # 152.4 m, a typical modern tunnel house
HOUSE_WID_M = 43 * FT    # 13.1 m

# Somewhere in Randolph County in UTM 15N.
ORIGIN_E, ORIGIN_N = 320_000.0, 4_015_000.0


def _house(offset_e: float, offset_n: float):
    return box(
        ORIGIN_E + offset_e,
        ORIGIN_N + offset_n,
        ORIGIN_E + offset_e + HOUSE_WID_M,
        ORIGIN_N + offset_n + HOUSE_LEN_M,
    )


@pytest.fixture
def synthetic_barns() -> gpd.GeoDataFrame:
    """Two farms: four houses together, two houses 2 km away."""
    geoms = [_house(i * 25.0, 0.0) for i in range(4)]
    geoms += [_house(2000.0 + i * 25.0, 0.0) for i in range(2)]
    return gpd.GeoDataFrame(geometry=geoms, crs=WORKING_CRS)


class TestGeometry:
    def test_screen_recovers_house_dimensions(self, synthetic_barns):
        screened = sites.screen_barns(synthetic_barns)
        assert len(screened) == 6
        assert screened["length_m"].iloc[0] == pytest.approx(HOUSE_LEN_M, rel=1e-6)
        assert screened["width_m"].iloc[0] == pytest.approx(HOUSE_WID_M, rel=1e-6)
        # Ridge runs north-south, so azimuth is ~0 (mod 180).
        assert screened["azimuth_deg"].iloc[0] % 180 == pytest.approx(0.0, abs=1e-6)

    def test_screen_rejects_a_square_machine_shed(self):
        shed = gpd.GeoDataFrame(
            geometry=[box(ORIGIN_E, ORIGIN_N, ORIGIN_E + 40, ORIGIN_N + 40)],
            crs=WORKING_CRS,
        )
        assert len(sites.screen_barns(shed)) == 0

    def test_screen_rejects_an_overlong_narrow_sliver(self):
        # A field edge or fence line: long enough, but far too thin to be a house.
        sliver = gpd.GeoDataFrame(
            geometry=[box(ORIGIN_E, ORIGIN_N, ORIGIN_E + 2, ORIGIN_N + 400)],
            crs=WORKING_CRS,
        )
        assert len(sites.screen_barns(sliver)) == 0

    def test_clustering_separates_distant_farms(self, synthetic_barns):
        screened = sites.screen_barns(synthetic_barns)
        clustered = sites.cluster_into_farms(screened)
        assert clustered["farm_id"].nunique() == 2

        farms = sites.summarize_farms(clustered)
        assert sorted(farms["house_count"]) == [2, 4]

    def test_empty_input_survives_the_whole_chain(self):
        empty = gpd.GeoDataFrame(geometry=[], crs=WORKING_CRS)
        farms = sites.summarize_farms(sites.cluster_into_farms(sites.screen_barns(empty)))
        assert farms.empty


class TestLoad:
    def test_single_house_lands_in_the_expected_range(self):
        """A 500x43 ft house should land in the tens of MWh/yr."""
        floor_ft2 = 500 * 43
        band = estimate_load(floor_ft2)

        assert 15_000 < band.low_kwh < 30_000
        assert 30_000 < band.mid_kwh < 55_000
        assert 60_000 < band.high_kwh < 110_000
        assert band.low_kwh < band.mid_kwh < band.high_kwh

    def test_band_is_ordered_and_wide_enough_to_flag(self):
        band = estimate_load(500 * 43)
        # The published coefficients span 20-83 kWh/1000lb: a >4x spread.
        assert band.spread_ratio == pytest.approx(83 / 20, rel=1e-9)
        assert requires_metered_validation(band), (
            "geometry alone must never be treated as quote-grade"
        )

    def test_load_scales_linearly_with_floor_area(self):
        one = estimate_load(500 * 43)
        four = estimate_load(4 * 500 * 43)
        assert four.mid_kwh == pytest.approx(4 * one.mid_kwh, rel=1e-9)

    def test_big_bird_program_raises_load(self):
        standard = estimate_load(500 * 43, LoadModel())
        big_bird = estimate_load(500 * 43, LoadModel(avg_market_weight_lb=9.2))
        assert big_bird.mid_kwh > standard.mid_kwh


class TestSiting:
    def test_roof_capacity_far_exceeds_house_load(self):
        """Roof area is not the constraint -- this is the core design insight."""
        floor_ft2 = 4 * 500 * 43
        roof_kw = roof_capacity_kw(floor_ft2)
        load = estimate_load(floor_ft2)

        # A four-house farm could physically hold enough DC to generate several
        # times its own annual consumption.
        assert roof_kw * 1450 > 3 * load.mid_kwh

    def test_self_consumption_declines_with_array_size(self):
        assert self_consumed_fraction(0.25) > self_consumed_fraction(1.0)
        assert self_consumed_fraction(1.0) > self_consumed_fraction(2.0)
        assert self_consumed_fraction(0.0) == 1.0

    def test_export_is_worth_far_less_than_self_consumption(self):
        tariff = ArkansasTariff()
        assert tariff.export_credit_per_kwh < tariff.retail_rate_per_kwh / 4
        small = blended_value_per_kwh(0.2, tariff)
        large = blended_value_per_kwh(2.0, tariff)
        assert small > large, "oversizing must dilute value under Act 278"

    def test_act_278_sizing_stays_well_under_physical_capacity(self):
        """The binding constraint is self-consumption, not available surface."""
        floor_ft2 = 4 * 500 * 43
        load = estimate_load(floor_ft2)
        roof_kw = roof_capacity_kw(floor_ft2)

        recommended = recommend_size_kw(
            annual_load_kwh=load.mid_kwh, max_kw_dc=roof_kw, incentive_fraction=0.30
        )
        assert 0 < recommended < roof_kw, (
            "sizing to the roof rather than to the load is the Arkansas trap"
        )
        # The gap is the whole point: hundreds of kW of surface, tens of kW of
        # economically sensible array.
        assert recommended < roof_kw / 4

    def test_nothing_pencils_without_incentives(self):
        """With the ITC gone and REAP halted, the honest answer is zero.

        At $2.35/W and a 12c retail rate, unsubsidised simple payback is about
        13.5 years even at perfect self-consumption. The tool must return no
        system rather than invent one.
        """
        floor_ft2 = 4 * 500 * 43
        load = estimate_load(floor_ft2)
        roof_kw = roof_capacity_kw(floor_ft2)

        assert recommend_size_kw(load.mid_kwh, roof_kw, incentive_fraction=0.0) == 0.0

    def test_one_to_one_net_metering_would_justify_a_bigger_array(self):
        """Sanity check that the tariff, not the geometry, drives the answer."""
        floor_ft2 = 4 * 500 * 43
        load = estimate_load(floor_ft2)
        roof_kw = roof_capacity_kw(floor_ft2)

        act278 = recommend_size_kw(
            load.mid_kwh, roof_kw, tariff=ArkansasTariff(), incentive_fraction=0.30
        )
        grandfathered = recommend_size_kw(
            load.mid_kwh,
            roof_kw,
            tariff=ArkansasTariff(export_credit_per_kwh=0.12),
            incentive_fraction=0.30,
        )
        assert grandfathered > act278

    def test_zero_load_yields_no_system(self):
        assert recommend_size_kw(0.0, 500.0) == 0.0

    def test_ground_mount_is_quoted_alongside_not_instead(self):
        siting = SitingModel()
        assert siting.roof_requires_structural_review
        assert siting.ground_watts_per_ft2 < siting.roof_watts_per_ft2


class TestIncentives:
    def test_itc_blocked_without_safe_harbor_or_2027_completion(self):
        status = incentives.itc_status(quote_date=date(2026, 8, 11))
        assert not status.available
        assert "2027-12-31" in status.basis

    def test_itc_available_if_energised_before_2028(self):
        status = incentives.itc_status(
            quote_date=date(2026, 8, 11),
            expected_placed_in_service=date(2027, 6, 30),
        )
        assert status.available
        assert status.value_fraction == 0.30

    def test_itc_lost_if_energised_after_2027(self):
        status = incentives.itc_status(
            quote_date=date(2026, 8, 11),
            expected_placed_in_service=date(2028, 3, 1),
        )
        assert not status.available

    def test_safe_harbored_project_keeps_the_credit_into_2030(self):
        status = incentives.itc_status(
            quote_date=date(2026, 8, 11),
            began_construction_on=date(2026, 5, 1),
            expected_placed_in_service=date(2029, 9, 1),
        )
        assert status.available

    def test_reap_grant_is_not_quotable_today(self):
        status = incentives.reap_status(date(2026, 8, 11))
        assert not status.available
        assert status.value_fraction == 0.0

    def test_stack_never_silently_includes_a_halted_program(self):
        statuses = incentives.stack(quote_date=date(2026, 8, 11))
        assert incentives.total_incentive_fraction(statuses) == 0.0
        assert all(s.verify_before_quoting for s in statuses)
