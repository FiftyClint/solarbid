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
HOUSE_WID_M = 54 * FT    # 16.5 m -- modern commercial width; the screen
                         # deliberately rejects narrower legacy houses

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
    geoms = [_house(i * 30.0, 0.0) for i in range(4)]
    geoms += [_house(2000.0 + i * 30.0, 0.0) for i in range(2)]
    return gpd.GeoDataFrame(geometry=geoms, crs=WORKING_CRS)


@pytest.fixture
def four_house_farm() -> float:
    """Total floor area of a representative four-house Peco farm, sq ft."""
    return 4 * 500 * 54


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
        band = estimate_load(500 * 54)
        assert 15_000 < band.low_kwh < 30_000
        assert 30_000 < band.mid_kwh < 55_000
        assert 60_000 < band.high_kwh < 110_000

    def test_band_is_wide_enough_to_require_metered_validation(self):
        band = estimate_load(500 * 54)
        assert band.spread_ratio == pytest.approx(83 / 20, rel=1e-9)
        assert requires_metered_validation(band), (
            "geometry alone must never be treated as quote-grade"
        )

    def test_load_scales_linearly_with_floor_area(self):
        one = estimate_load(500 * 54)
        four = estimate_load(4 * 500 * 54)
        assert four.mid_kwh == pytest.approx(4 * one.mid_kwh, rel=1e-9)

    def test_big_bird_program_raises_load(self):
        standard = estimate_load(500 * 54, LoadModel())
        big_bird = estimate_load(500 * 54, LoadModel(avg_market_weight_lb=9.2))
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


class TestBudgetaryQuote:
    """Stage-one output: cheap, ranged, and clearly not a bid."""

    def _quote(self, tax_rate=0.30, **kw):
        from solarbid.quote import budgetary_quote
        from solarbid.siting import roof_capacity_kw as roof_cap

        floor = 4 * 500 * 54
        itc = incentives.itc_rate(
            system_kw_ac=150,
            quote_date=TODAY,
            expected_placed_in_service=TARGET_PIS,
            domestic_content=True,
            energy_community=incentives.energy_community_by_county("Randolph"),
        )
        return budgetary_quote(
            farm_id="farm_00001",
            county="Randolph",
            house_count=4,
            floor_area_ft2=floor,
            load=estimate_load(floor),
            roof_capacity_kw=roof_cap(floor),
            ground_capacity_kw=300.0,
            itc=itc,
            tax_rate=tax_rate,
            quote_date=TODAY,
            **kw,
        )

    def test_randolph_farm_quotes_the_full_fifty_percent(self):
        q = self._quote()
        assert q.itc.total_rate == pytest.approx(0.50)
        assert q.itc.is_fully_resolved

    def test_system_size_is_a_range_driven_by_the_load_band(self):
        """Load uncertainty, not irradiance, is what makes this a range."""
        q = self._quote()
        assert q.system_kw_low < q.system_kw_mid < q.system_kw_high

    def test_both_mount_options_are_priced(self):
        q = self._quote()
        assert q.roof.recommended_kw > 0
        assert q.ground.recommended_kw > 0

    def test_each_mount_carries_its_own_verification_blocker(self):
        q = self._quote()
        assert any("structural review" in b for b in q.roof.blockers)
        assert any("ownership" in b for b in q.ground.blockers)

    def test_preferred_option_is_the_faster_payback(self):
        q = self._quote()
        assert q.preferred.payback_years == min(
            q.roof.payback_years, q.ground.payback_years
        )

    def test_rendered_quote_says_it_is_not_a_bid(self):
        text = self._quote().render()
        assert "not a bid" in text.lower()
        assert "BEFORE THIS BECOMES A BID" in text

    def test_rendered_quote_surfaces_the_2027_deadline(self):
        assert "2027-12-31" in self._quote().render()

    def test_rendered_quote_asks_for_the_utility_bills(self):
        """The cheapest way to collapse the load band is to ask."""
        assert "utility bills" in self._quote().render().lower()

    def test_no_tax_appetite_still_produces_a_usable_quote(self):
        q = self._quote(tax_rate=0.0)
        assert q.preferred.viable
        assert q.preferred.payback_years > self._quote().preferred.payback_years

    def test_roof_beats_ground_on_economics_where_structure_allows(self):
        """The 10c gap is what makes the mount comparison meaningful."""
        q = self._quote()
        assert q.roof.payback_years < q.ground.payback_years
        assert q.preferred.mount == "roof"

    def test_roof_advantage_is_conditional_on_the_structural_review(self):
        """Cheaper on paper is not cheaper if the trusses cannot carry it."""
        q = self._quote()
        assert q.preferred.mount == "roof"
        assert any("structural review" in b for b in q.preferred.blockers)


class TestCLI:
    """Guards on scripts/run_spike.py argument handling."""

    def _tristate(self):
        import importlib.util
        from pathlib import Path

        path = Path(__file__).resolve().parent.parent / "scripts" / "run_spike.py"
        spec = importlib.util.spec_from_file_location("run_spike", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module._tristate

    def test_tristate_parses_the_three_words(self):
        """argparse applies `type` before `choices`, so validation lives here.

        With choices=["yes","no","unknown"] alongside type=_tristate, "yes"
        converts to True and then fails the membership test -- every flag was
        rejected.
        """
        tristate = self._tristate()
        assert tristate("yes") is True
        assert tristate("no") is False
        assert tristate("unknown") is None

    def test_tristate_is_case_and_whitespace_tolerant(self):
        tristate = self._tristate()
        assert tristate(" YES ") is True

    def test_tristate_rejects_anything_else(self):
        import argparse

        tristate = self._tristate()
        with pytest.raises(argparse.ArgumentTypeError):
            tristate("maybe")


class TestDetectionCalibration:
    """Guards on the screen calibrated against the real Peco AOI extract."""

    def _poly(self, length_ft, width_ft):
        return gpd.GeoDataFrame(
            geometry=[
                box(
                    ORIGIN_E,
                    ORIGIN_N,
                    ORIGIN_E + width_ft * FT,
                    ORIGIN_N + length_ft * FT,
                )
            ],
            crs=WORKING_CRS,
        )

    def test_modern_commercial_house_passes(self):
        assert len(sites.screen_barns(self._poly(555, 68))) == 1

    def test_the_smaller_outbuilding_population_is_thinned(self):
        """Loosening the screen pulled in a distinct second population.

        Those detections median 412ft x 48ft and are overwhelmingly isolated
        singles -- hay barns, machine sheds and older small houses rather than
        contract poultry. The screen thins that population rather than
        eliminating it: 412 x 48 is a median, so roughly half of it sits above
        the 400ft/45ft thresholds and still survives. Anything meaningfully
        below either threshold is cut.
        """
        assert len(sites.screen_barns(self._poly(350, 48))) == 0   # too short
        assert len(sites.screen_barns(self._poly(412, 40))) == 0   # too narrow
        assert len(sites.screen_barns(self._poly(412, 48))) == 1   # survives

    def test_narrow_legacy_house_is_rejected(self):
        """43ft wide is below modern commercial; excluded deliberately."""
        assert len(sites.screen_barns(self._poly(500, 43))) == 0

    def test_probability_gate_reads_the_p_column(self):
        """The released dataset names it `p`; missing it skips the gate silently."""
        low = self._poly(555, 68).assign(p=0.05)
        high = self._poly(555, 68).assign(p=0.80)
        assert len(sites.screen_barns(low)) == 0
        assert len(sites.screen_barns(high)) == 1

    def test_probability_floor_is_permissive_by_design(self):
        """Shape carries the discrimination; p only floors out noise.

        In the AOI, p 0.00-0.25 detections median 511ft x 67ft at 7.8:1 aspect,
        indistinguishable from the p 0.70+ band. A 0.50 threshold discarded
        ~800 polygons that look exactly like poultry houses.
        """
        from solarbid.config import DetectionFilter

        assert DetectionFilter().min_probability <= 0.30
        mid = self._poly(555, 68).assign(p=0.35)
        assert len(sites.screen_barns(mid)) == 1


class TestOversizingBound:
    """Sizing must not run away on farms with lots of open ground."""

    def test_self_consumption_decays_toward_zero(self):
        """The tabulated curve alone floors at 0.44 and never stops paying."""
        assert self_consumed_fraction(4.0) < 0.20
        assert self_consumed_fraction(20.0) < 0.05
        assert self_consumed_fraction(50.0) < self_consumed_fraction(20.0)

    def test_self_consumed_energy_never_exceeds_load(self):
        """The hard physical bound behind the asymptote."""
        for ratio in (0.5, 1.0, 2.0, 5.0, 25.0, 100.0):
            assert self_consumed_fraction(ratio) * ratio <= 1.0

    def test_single_house_farm_with_vast_open_ground_stays_sane(self):
        """The bug: 5 MW recommended against a 35,000 kWh/yr load."""
        load = estimate_load(500 * 54)          # one house
        huge_ground_kw = 9_000.0                # 150m buffer around one house
        fin = project_finance(50, Pricing().ground_cost_per_watt, 0.50, tax_rate=0.30)

        kw = recommend_size_kw(
            load.mid_kwh, huge_ground_kw, net_cost_per_watt=fin.net_cost_per_watt
        )
        assert kw < 100, f"one house should not warrant {kw:,.0f} kW"
        assert kw * 1450 < 3 * load.mid_kwh

    def test_recommendation_never_reaches_the_act_278_cap_on_a_farm(self):
        load = estimate_load(4 * 500 * 54)
        fin = project_finance(50, Pricing().ground_cost_per_watt, 0.50, tax_rate=0.30)
        kw = recommend_size_kw(
            load.mid_kwh, 20_000.0, net_cost_per_watt=fin.net_cost_per_watt
        )
        assert kw < ArkansasTariff().max_project_kw



class TestQuoteHtml:
    """The grower-facing one-pager."""

    def _quote(self):
        from solarbid.quote import budgetary_quote
        from solarbid.siting import roof_capacity_kw as roof_cap

        floor = 10 * 560 * 56
        itc = incentives.itc_rate(
            system_kw_ac=325,
            quote_date=TODAY,
            expected_placed_in_service=TARGET_PIS,
            domestic_content=True,
            energy_community=incentives.energy_community_by_county("Randolph"),
        )
        return budgetary_quote(
            farm_id="farm_00167",
            county="Randolph",
            house_count=10,
            floor_area_ft2=floor,
            load=estimate_load(floor),
            roof_capacity_kw=roof_cap(floor),
            ground_capacity_kw=2000.0,
            itc=itc,
            quote_date=TODAY,
        )

    def test_html_leads_with_the_midpoint_not_the_range(self):
        q = self._quote()
        html = q.render_html()
        assert f"{q.load_mid_kwh:,.0f}" in html
        assert f"{q.load_low_kwh:,.0f} to" not in html.split("Before this becomes")[0]

    def test_html_still_states_the_range_in_the_footnotes(self):
        q = self._quote()
        html = q.render_html()
        assert f"{q.load_low_kwh:,.0f}" in html
        assert f"{q.system_kw_high:,.0f} kW" in html

    def test_html_is_self_contained(self):
        """Must survive being emailed as an attachment."""
        html = self._quote().render_html()
        for external in ("http://", "https://", "<script", "src="):
            assert external not in html

    def test_html_is_marked_as_not_a_bid(self):
        assert "not a bid" in self._quote().render_html().lower()
