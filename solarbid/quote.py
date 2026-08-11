"""Budgetary quotes: the stage-one artifact.

This pipeline has two stages with very different economics.

Stage one is screening. Everything is derived from aerial imagery and public
data, costs nothing per farm, and exists to get a grower to raise their hand.
Precision is not the goal here and chasing it is wasted money -- a farm that
never responds does not deserve an 8760 simulation.

Stage two starts when they respond: twelve months of interval data, a
structural review for roof mounts, parcel and land cover for ground, real
irradiance modeling, and a firm bid.

This module produces stage one. Its numbers carry a range rather than a point,
because the honest uncertainty at this stage is wide and pretending otherwise
is how a screening figure gets mistaken for a bid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .config import ArkansasTariff, Pricing, SitingModel
from .finance import project_finance
from .incentives import ITCResult
from .load import LoadBand
from .siting import blended_value_per_kwh, recommend_size_kw

# Flat planning yield for northeast Arkansas, kWh per kW DC per year. Coarse on
# purpose: at stage one the load band spans 4x, so a precise irradiance model
# would be false precision bolted onto a rough number. PVWatts belongs in
# stage two.
PLANNING_YIELD_KWH_PER_KW = 1450.0


@dataclass(frozen=True)
class MountOption:
    """One mounting approach for a farm."""

    mount: str
    capacity_kw: float
    recommended_kw: float
    gross_cost: float
    net_cost: float
    annual_savings: float
    payback_years: float
    blockers: list[str] = field(default_factory=list)

    @property
    def viable(self) -> bool:
        return self.recommended_kw > 0


@dataclass(frozen=True)
class BudgetaryQuote:
    """A stage-one quote for one farm, with its range and its caveats."""

    farm_id: str
    county: str
    house_count: int
    floor_area_ft2: float

    load_low_kwh: float
    load_mid_kwh: float
    load_high_kwh: float

    system_kw_low: float
    system_kw_mid: float
    system_kw_high: float

    roof: MountOption
    ground: MountOption

    itc: ITCResult
    quote_date: date
    caveats: list[str] = field(default_factory=list)

    @property
    def preferred(self) -> MountOption:
        """Cheaper payback wins, but only among options that are actually viable."""
        options = [o for o in (self.ground, self.roof) if o.viable]
        if not options:
            return self.ground
        return min(options, key=lambda o: o.payback_years)

    @property
    def range_note(self) -> str:
        """The uncertainty, stated once, for the footnotes.

        The grower sees a single number up front; this is where the honesty
        about how wide it really is lives.
        """
        return (
            f"Consumption is estimated from house dimensions and University of "
            f"Arkansas audit data, not from your meter. The plausible range is "
            f"{self.load_low_kwh:,.0f} to {self.load_high_kwh:,.0f} kWh/yr, which "
            f"corresponds to a system of {self.system_kw_low:,.0f} to "
            f"{self.system_kw_high:,.0f} kW. Twelve months of your utility bills "
            f"would replace this estimate with your actual usage."
        )

    def render(self) -> str:
        """Plain-text budgetary summary, suitable for a one-pager."""
        lines = [
            f"BUDGETARY SOLAR ESTIMATE -- {self.farm_id}",
            f"{self.county} County, Arkansas | {self.house_count} houses | "
            f"{self.floor_area_ft2:,.0f} sq ft under roof",
            f"Prepared {self.quote_date}. Budgetary only -- not a bid.",
            "",
            "ESTIMATED ELECTRICITY USE",
            f"  {self.load_mid_kwh:,.0f} kWh/yr",
            "",
            "INDICATIVE SYSTEM SIZE",
            f"  {self.system_kw_mid:,.0f} kW DC",
            "",
            f"SECTION 48E: {self.itc.summary()}",
        ]

        for option in (self.ground, self.roof):
            lines.append("")
            lines.append(f"{option.mount.upper()} MOUNT")
            if not option.viable:
                lines.append("  Not recommended at this site.")
            else:
                lines.append(f"  System            {option.recommended_kw:,.0f} kW DC")
                lines.append(f"  Installed cost    ${option.gross_cost:,.0f}")
                lines.append(f"  Net after credit  ${option.net_cost:,.0f}")
                lines.append(f"  Annual savings    ${option.annual_savings:,.0f}")
                lines.append(f"  Simple payback    {option.payback_years:.1f} years")
            for blocker in option.blockers:
                lines.append(f"  NOTE: {blocker}")

        if self.itc.unresolved:
            lines.append("")
            lines.append("OPEN ITEMS AFFECTING THE CREDIT")
            for item in self.itc.unresolved:
                lines.append(f"  - {item}")

        lines.append("")
        lines.append("BEFORE THIS BECOMES A BID")
        lines.append(f"  - {self.range_note}")
        for caveat in self.caveats:
            lines.append(f"  - {caveat}")

        return "\n".join(lines)

    def render_html(self, prepared_by: str = "") -> str:
        """Self-contained, printable one-pager.

        No external assets, so it survives being emailed as an attachment, and
        prints to a single page.
        """

        def money(x: float) -> str:
            return f"${x:,.0f}"

        def mount_card(option: MountOption) -> str:
            if not option.viable:
                return (
                    f'<div class="card"><h3>{option.mount.title()} mount</h3>'
                    "<p class='na'>Not recommended at this site.</p></div>"
                )
            rows = [
                ("System", f"{option.recommended_kw:,.0f} kW DC"),
                ("Installed cost", money(option.gross_cost)),
                ("Net after credit &amp; depreciation", money(option.net_cost)),
                ("Estimated annual savings", f"{money(option.annual_savings)}/yr"),
                ("Simple payback", f"{option.payback_years:.1f} years"),
            ]
            body = "".join(
                f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows
            )
            notes = "".join(f"<p class='note'>{b}</p>" for b in option.blockers)
            return (
                f'<div class="card"><h3>{option.mount.title()} mount</h3>'
                f"<table>{body}</table>{notes}</div>"
            )

        caveats = "".join(f"<li>{c}</li>" for c in self.caveats)
        open_items = ""
        if self.itc.unresolved:
            items = "".join(f"<li>{u}</li>" for u in self.itc.unresolved)
            open_items = (
                "<h2>Open items affecting the credit</h2>"
                f"<ul class='open'>{items}</ul>"
            )
        byline = f"<p class='by'>Prepared by {prepared_by}</p>" if prepared_by else ""

        return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Budgetary Solar Estimate — {self.farm_id}</title>
<style>
  :root {{ --ink:#1a1a1a; --mute:#666; --rule:#d8d8d8; --accent:#1c5f3f; --bg:#fff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:2.5rem 2rem; background:var(--bg); color:var(--ink);
         font:16px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         max-width:52rem; margin-inline:auto; }}
  header {{ border-bottom:3px solid var(--accent); padding-bottom:1rem; margin-bottom:1.5rem; }}
  h1 {{ font-size:1.5rem; margin:0 0 .35rem; letter-spacing:-.01em; }}
  .sub {{ color:var(--mute); font-size:.95rem; margin:0; }}
  .flag {{ display:inline-block; margin-top:.6rem; padding:.2rem .55rem; border-radius:3px;
           background:#fdf3d7; color:#6b4e00; font-size:.8rem; font-weight:600;
           text-transform:uppercase; letter-spacing:.04em; }}
  .headline {{ display:flex; gap:2.5rem; flex-wrap:wrap; margin:1.5rem 0 2rem; }}
  .metric {{ flex:1 1 12rem; }}
  .metric .label {{ font-size:.78rem; text-transform:uppercase; letter-spacing:.06em;
                    color:var(--mute); margin-bottom:.15rem; }}
  .metric .value {{ font-size:1.9rem; font-weight:650; line-height:1.15;
                    color:var(--accent); letter-spacing:-.02em; }}
  .metric .unit {{ font-size:.95rem; font-weight:400; color:var(--mute); }}
  .credit {{ background:#f1f6f3; border-left:3px solid var(--accent);
             padding:.85rem 1rem; margin-bottom:1.75rem; font-size:.95rem; }}
  h2 {{ font-size:1.05rem; margin:1.75rem 0 .75rem; }}
  .cards {{ display:flex; gap:1.25rem; flex-wrap:wrap; }}
  .card {{ flex:1 1 18rem; border:1px solid var(--rule); border-radius:5px; padding:1rem 1.15rem; }}
  .card h3 {{ margin:0 0 .6rem; font-size:1rem; }}
  table {{ width:100%; border-collapse:collapse; font-size:.92rem; }}
  th {{ text-align:left; font-weight:400; color:var(--mute); padding:.3rem 0; }}
  td {{ text-align:right; font-variant-numeric:tabular-nums; font-weight:600; padding:.3rem 0; }}
  .note {{ font-size:.8rem; color:var(--mute); margin:.75rem 0 0; padding-top:.6rem;
           border-top:1px solid var(--rule); }}
  .na {{ color:var(--mute); font-style:italic; }}
  ul {{ padding-left:1.1rem; }}
  li {{ margin:.4rem 0; font-size:.9rem; }}
  ul.open li {{ color:#7a4a00; }}
  footer {{ margin-top:2rem; padding-top:1rem; border-top:1px solid var(--rule);
            font-size:.8rem; color:var(--mute); }}
  .by {{ margin:.2rem 0 0; }}
  @media print {{ body {{ padding:0; }} .card {{ break-inside:avoid; }} }}
</style></head><body>
<header>
  <h1>Budgetary Solar Estimate</h1>
  <p class="sub">{self.county} County, Arkansas &middot; {self.house_count} poultry houses
     &middot; {self.floor_area_ft2:,.0f} sq ft under roof &middot; ref {self.farm_id}</p>
  <span class="flag">Budgetary estimate — not a bid</span>
</header>

<div class="headline">
  <div class="metric">
    <div class="label">Estimated electricity use</div>
    <div class="value">{self.load_mid_kwh:,.0f}<span class="unit"> kWh/yr</span></div>
  </div>
  <div class="metric">
    <div class="label">Indicative system size</div>
    <div class="value">{self.system_kw_mid:,.0f}<span class="unit"> kW DC</span></div>
  </div>
</div>

<div class="credit"><strong>Federal tax credit:</strong> {self.itc.summary()}</div>

<h2>Mounting options</h2>
<div class="cards">{mount_card(self.roof)}{mount_card(self.ground)}</div>

{open_items}

<h2>Before this becomes a bid</h2>
<ul><li>{self.range_note}</li>{caveats}</ul>

<footer>
  Prepared {self.quote_date}. Figures are preliminary planning estimates based on
  aerial imagery and public data, and are subject to site verification.
  {byline}
</footer>
</body></html>"""


def _mount_option(
    mount: str,
    capacity_kw: float,
    annual_load_kwh: float,
    itc_rate: float,
    tax_rate: float,
    pricing: Pricing,
    tariff: ArkansasTariff,
    siting: SitingModel,
) -> MountOption:
    cost_per_watt = (
        pricing.ground_cost_per_watt if mount == "ground" else pricing.roof_cost_per_watt
    )
    fin_unit = project_finance(1.0, cost_per_watt, itc_rate, tax_rate=tax_rate)

    kw = recommend_size_kw(
        annual_load_kwh=annual_load_kwh,
        max_kw_dc=capacity_kw,
        tariff=tariff,
        pricing=pricing,
        mount=mount,
        net_cost_per_watt=fin_unit.net_cost_per_watt,
    )

    blockers: list[str] = []
    if mount == "roof" and siting.roof_requires_structural_review:
        blockers.append(
            "Roof mount is subject to a structural review. Light-gauge metal over "
            "wood trusses often cannot carry the added load."
        )
    if mount == "ground":
        blockers.append(
            "Ground area estimated from imagery only. Not checked for cropping, "
            "land cover, floodplain or ownership."
        )

    if kw <= 0:
        return MountOption(mount, capacity_kw, 0.0, 0.0, 0.0, 0.0, float("inf"), blockers)

    fin = project_finance(kw, cost_per_watt, itc_rate, tax_rate=tax_rate)
    production = kw * PLANNING_YIELD_KWH_PER_KW
    savings = production * blended_value_per_kwh(production / annual_load_kwh, tariff)

    return MountOption(
        mount=mount,
        capacity_kw=capacity_kw,
        recommended_kw=kw,
        gross_cost=fin.gross_cost,
        net_cost=fin.net_cost,
        annual_savings=savings,
        payback_years=fin.simple_payback_years(savings),
        blockers=blockers,
    )


def budgetary_quote(
    farm_id: str,
    county: str,
    house_count: int,
    floor_area_ft2: float,
    load: LoadBand,
    roof_capacity_kw: float,
    ground_capacity_kw: float,
    itc: ITCResult,
    tax_rate: float = 0.30,
    quote_date: date | None = None,
    pricing: Pricing | None = None,
    tariff: ArkansasTariff | None = None,
    siting: SitingModel | None = None,
) -> BudgetaryQuote:
    """Build a stage-one quote for one farm.

    System size is quoted as a range driven by the load band, not by anything
    to do with irradiance. A farm consuming at the low end of the audit range
    warrants a materially smaller array than one at the high end, and that
    spread dwarfs any error in the yield assumption.
    """
    pricing = pricing or Pricing()
    tariff = tariff or ArkansasTariff()
    siting = siting or SitingModel()
    quote_date = quote_date or date.today()

    best_capacity = max(roof_capacity_kw, ground_capacity_kw)
    unit = project_finance(1.0, pricing.ground_cost_per_watt, itc.total_rate, tax_rate)
    sizes = [
        recommend_size_kw(
            annual_load_kwh=kwh,
            max_kw_dc=best_capacity,
            tariff=tariff,
            pricing=pricing,
            net_cost_per_watt=unit.net_cost_per_watt,
        )
        for kwh in (load.low_kwh, load.mid_kwh, load.high_kwh)
    ]

    ground = _mount_option(
        "ground", ground_capacity_kw, load.mid_kwh, itc.total_rate, tax_rate,
        pricing, tariff, siting,
    )
    roof = _mount_option(
        "roof", roof_capacity_kw, load.mid_kwh, itc.total_rate, tax_rate,
        pricing, tariff, siting,
    )

    caveats = [
        "Twelve months of interval data to confirm consumption and load shape.",
        "Structural review if roof mounted; parcel and land cover if ground mounted.",
        "Utility tariff and interconnection terms confirmed for this meter.",
        "Tax capacity confirmed with your CPA -- the credit and first-year "
        "depreciation only help if there is liability to offset.",
        f"Production modeled at a flat {PLANNING_YIELD_KWH_PER_KW:,.0f} kWh per kW "
        "planning figure; site-specific modeling comes with the firm proposal.",
    ]
    if itc.eligible:
        caveats.append(
            "System energized by 2027-12-31. The credit is not available after that."
        )

    return BudgetaryQuote(
        farm_id=farm_id,
        county=county,
        house_count=house_count,
        floor_area_ft2=floor_area_ft2,
        load_low_kwh=load.low_kwh,
        load_mid_kwh=load.mid_kwh,
        load_high_kwh=load.high_kwh,
        system_kw_low=sizes[0],
        system_kw_mid=sizes[1],
        system_kw_high=sizes[2],
        roof=roof,
        ground=ground,
        itc=itc,
        quote_date=quote_date,
        caveats=caveats,
    )
