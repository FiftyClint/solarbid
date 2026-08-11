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
from solarbid.config import WORKING_CRS, ArkansasTariff, LoadModel, Pricing, SitingModel
from solarbid.finance import project_finance, transfer_value
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

ORIGIN_E, ORIGIN_N = 320_000.0, 4_015_000.0   # Randolph County, UTM 15N

TARGET_PIS = date(2027, 12, 1)   # the end-of-2027 energisation target
TODAY = date(2026, 8, 11)


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


@pytest.fixture
def four_house_farm() -> float:
    """Total floor area of a representative four-house Peco farm, sq ft."""
    return 4 * 500 * 43


class TestGeometry:
    def test_screen_recovers_house_dimensions(self, synthetic_barns):
        screened = sites.screen_barns(synthetic_barns)
        assert len(screened) == 6
        assert screened["length_m"].iloc[0] == pytest.approx(HOUSE_LEN_M, rel=1e-6)
        assert screened["width_m"].iloc[0] == pytest.approx(HOUSE_WID_M, rel=1e-6)
        assert screened["azimuth_deg"].iloc[0] % 180 == pytest.approx(0.0, abs=1e-6)

    def test_screen_rejects_a_square_machine_shed(self):
        shed = gpd.GeoDataFrame(
            geometry=[box(ORIGIN_E, ORIGIN_N, ORIGIN_E + 40, ORIGIN_N + 40)],
            crs=WORKING_CRS,
        )
        assert len(sites.screen_barns(shed)) == 0

    def test_screen_rejects_an_overlong_narrow_sliver(self):
        """A fence line or field edge: long and thin, but far too thin."""
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
        band = estimate_load(500 * 43)
        assert 15_000 < band.low_kwh < 30_000
        assert 30_000 < band.mid_kwh < 55_000
        assert 60_000 < band.high_kwh < 110_000

    def test_band_is_wide_enough_to_require_metered_validation(self):
        band = estimate_load(500 * 43)
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


class TestITC:
    """Section 48E, targeting an end-of-2027 placed-in-service date."""

    def test_end_of_2027_energisation_qualifies(self):
        result = incentives.itc_rate(
            system_kw_ac=50, quote_date=TODAY, expected_placed_in_service=TARGET_PIS
        )
        assert result.eligible
        assert result.base_rate == 0.30

    def test_slipping_past_2027_loses_everything(self):
        result = incentives.itc_rate(
            system_kw_ac=50,
            quote_date=TODAY,
            expected_placed_in_service=date(2028, 3, 1),
        )
        assert not result.eligible
        assert result.total_rate == 0.0

    def test_farm_scale_systems_are_exempt_from_prevailing_wage(self):
        """The most favourable structural fact in the model."""
        result = incentives.itc_rate(
            system_kw_ac=85, quote_date=TODAY, expected_placed_in_service=TARGET_PIS
        )
        assert result.pwa_exempt
        assert result.base_rate == 0.30

    def test_above_one_megawatt_loses_the_exemption(self):
        result = incentives.itc_rate(
            system_kw_ac=1500, quote_date=TODAY, expected_placed_in_service=TARGET_PIS
        )
        assert not result.pwa_exempt

    def test_both_adders_stack_to_fifty_percent(self):
        result = incentives.itc_rate(
            system_kw_ac=50,
            quote_date=TODAY,
            expected_placed_in_service=TARGET_PIS,
            domestic_content=True,
            energy_community=True,
        )
        assert result.total_rate == pytest.approx(0.50)
        assert result.is_fully_resolved

    def test_unknown_adders_are_never_assumed_favourable(self):
        """Undetermined must not quietly inflate the credit."""
        result = incentives.itc_rate(
            system_kw_ac=50, quote_date=TODAY, expected_placed_in_service=TARGET_PIS
        )
        assert result.total_rate == pytest.approx(0.30)
        assert len(result.unresolved) == 2
        assert not result.is_fully_resolved

    def test_energy_community_is_flagged_when_undetermined(self):
        result = incentives.itc_rate(
            system_kw_ac=50, quote_date=TODAY, expected_placed_in_service=TARGET_PIS
        )
        assert any("Energy community" in u for u in result.unresolved)

    def test_peco_footprint_counties_qualify(self):
        """Pocahontas sits in Randolph, so the plant's home county qualifies."""
        for county in ("Randolph", "Clay", "Lawrence", "Greene", "Independence",
                       "Izard", "Sharp", "Fulton", "Jackson", "Mississippi"):
            assert incentives.energy_community_by_county(county) is True, county

    def test_county_lookup_is_case_insensitive(self):
        assert incentives.energy_community_by_county("randolph") is True

    def test_counties_off_the_list_do_not_qualify(self):
        assert incentives.energy_community_by_county("Craighead") is False

    def test_outside_arkansas_is_unknown_not_false(self):
        """No list carried for other states; unknown must not read as ineligible."""
        assert incentives.energy_community_by_county("Randolph", state="MO") is None

    def test_energy_community_claim_cites_the_boc_safe_harbor(self):
        """Annual redetermination is survivable only by starting construction."""
        result = incentives.itc_rate(
            system_kw_ac=50,
            quote_date=TODAY,
            expected_placed_in_service=TARGET_PIS,
            energy_community=True,
        )
        assert any("construction start" in c for c in result.conditions)

    def test_domestic_content_threshold_rises_with_construction_year(self):
        y26 = incentives.itc_rate(
            system_kw_ac=50,
            quote_date=date(2026, 8, 11),
            expected_placed_in_service=TARGET_PIS,
            domestic_content=True,
        )
        y27 = incentives.itc_rate(
            system_kw_ac=50,
            quote_date=date(2027, 2, 1),
            began_construction_on=date(2027, 2, 1),
            expected_placed_in_service=TARGET_PIS,
            domestic_content=True,
        )
        assert any("50%" in c for c in y26.conditions)
        assert any("55%" in c for c in y27.conditions)

    def test_feoc_is_raised_for_every_current_project(self):
        """Failing the material assistance ratio denies the credit outright."""
        result = incentives.itc_rate(
            system_kw_ac=50, quote_date=TODAY, expected_placed_in_service=TARGET_PIS
        )
        assert any("material assistance" in c for c in result.conditions)

    def test_reap_grant_is_not_quotable_today(self):
        status = incentives.reap_status(TODAY)
        assert not status.available
        assert status.value_fraction == 0.0


class TestFinance:
    def test_bonus_depreciation_roughly_halves_net_cost_at_30_percent(self):
        fin = project_finance(50, 2.10, itc_rate=0.30, tax_rate=0.30)
        assert 0.85 < fin.net_cost_per_watt < 1.05
        assert fin.total_benefit_fraction > 0.50

    def test_full_stack_drives_net_cost_under_a_dollar(self):
        fin = project_finance(50, 2.10, itc_rate=0.50, tax_rate=0.30)
        assert fin.net_cost_per_watt < 0.75
        assert fin.total_benefit_fraction > 0.70

    def test_itc_reduces_depreciable_basis_by_half_the_credit(self):
        fin = project_finance(50, 2.10, itc_rate=0.50, tax_rate=0.30)
        assert fin.depreciable_basis == pytest.approx(
            fin.gross_cost - 0.5 * fin.itc_amount
        )

    def test_low_tax_appetite_materially_worsens_the_deal(self):
        """Net cost is a property of the grower, not just the project."""
        high = project_finance(50, 2.10, itc_rate=0.50, tax_rate=0.35)
        low = project_finance(50, 2.10, itc_rate=0.50, tax_rate=0.10)
        assert low.net_cost > high.net_cost
        assert any("tax capacity" in c for c in low.caveats)

    def test_every_financed_quote_carries_monetisation_caveats(self):
        fin = project_finance(50, 2.10, itc_rate=0.50, tax_rate=0.30)
        assert fin.caveats
        assert any("passive activity" in c.lower() for c in fin.caveats)

    def test_credit_transfer_clears_below_par(self):
        fin = project_finance(50, 2.10, itc_rate=0.50, tax_rate=0.30)
        assert transfer_value(fin.itc_amount) < fin.itc_amount

    def test_zero_incentives_leaves_gross_cost_intact(self):
        fin = project_finance(50, 2.10, itc_rate=0.0, tax_rate=0.0)
        assert fin.net_cost == pytest.approx(fin.gross_cost)


class TestSiting:
    def test_roof_capacity_far_exceeds_house_load(self, four_house_farm):
        """Roof area is not the constraint -- this is the core design insight."""
        roof_kw = roof_capacity_kw(four_house_farm)
        load = estimate_load(four_house_farm)
        assert roof_kw * 1450 > 3 * load.mid_kwh

    def test_self_consumption_declines_with_array_size(self):
        assert self_consumed_fraction(0.25) > self_consumed_fraction(1.0)
        assert self_consumed_fraction(1.0) > self_consumed_fraction(2.0)
        assert self_consumed_fraction(0.0) == 1.0

    def test_export_is_worth_far_less_than_self_consumption(self):
        tariff = ArkansasTariff()
        assert tariff.export_credit_per_kwh < tariff.retail_rate_per_kwh / 4
        assert blended_value_per_kwh(0.2, tariff) > blended_value_per_kwh(2.0, tariff)

    def test_nothing_pencils_at_gross_cost(self, four_house_farm):
        """At $2.10/W and 12c retail, unsubsidised payback is ~13.5 years."""
        load = estimate_load(four_house_farm)
        roof_kw = roof_capacity_kw(four_house_farm)
        assert recommend_size_kw(load.mid_kwh, roof_kw) == 0.0

    def test_act_278_sizing_stays_well_under_physical_capacity(self, four_house_farm):
        """The binding constraint is self-consumption, not available surface."""
        load = estimate_load(four_house_farm)
        roof_kw = roof_capacity_kw(four_house_farm)
        fin = project_finance(50, Pricing().ground_cost_per_watt, 0.30, tax_rate=0.30)

        recommended = recommend_size_kw(
            load.mid_kwh, roof_kw, net_cost_per_watt=fin.net_cost_per_watt
        )
        assert 0 < recommended < roof_kw, (
            "sizing to the roof rather than to the load is the Arkansas trap"
        )

    def test_bonus_adders_justify_a_larger_array(self, four_house_farm):
        """Domestic content and energy community change the system, not just the price."""
        load = estimate_load(four_house_farm)
        roof_kw = roof_capacity_kw(four_house_farm)
        cpw = Pricing().ground_cost_per_watt

        base = project_finance(50, cpw, 0.30, tax_rate=0.30)
        stacked = project_finance(50, cpw, 0.50, tax_rate=0.30)

        base_kw = recommend_size_kw(
            load.mid_kwh, roof_kw, net_cost_per_watt=base.net_cost_per_watt
        )
        stacked_kw = recommend_size_kw(
            load.mid_kwh, roof_kw, net_cost_per_watt=stacked.net_cost_per_watt
        )
        assert stacked_kw > base_kw

    def test_one_to_one_net_metering_would_justify_a_bigger_array(self, four_house_farm):
        """Sanity check that the tariff, not the geometry, drives the answer."""
        load = estimate_load(four_house_farm)
        roof_kw = roof_capacity_kw(four_house_farm)
        fin = project_finance(50, Pricing().ground_cost_per_watt, 0.30, tax_rate=0.30)

        act278 = recommend_size_kw(
            load.mid_kwh,
            roof_kw,
            tariff=ArkansasTariff(),
            net_cost_per_watt=fin.net_cost_per_watt,
        )
        grandfathered = recommend_size_kw(
            load.mid_kwh,
            roof_kw,
            tariff=ArkansasTariff(export_credit_per_kwh=0.12),
            net_cost_per_watt=fin.net_cost_per_watt,
        )
        assert grandfathered > act278

    def test_zero_load_yields_no_system(self):
        assert recommend_size_kw(0.0, 500.0) == 0.0

    def test_ground_mount_is_quoted_alongside_not_instead(self):
        siting = SitingModel()
        assert siting.roof_requires_structural_review
        assert siting.ground_watts_per_ft2 < siting.roof_watts_per_ft2
