# solarbid

Prospecting and preliminary solar sizing for poultry farms in the Peco Foods
Pocahontas draw area, northeast Arkansas.

Given public aerial imagery, find the chicken houses, estimate what each farm
spends on electricity, and produce a preliminary roof-and-ground system concept
with an honest uncertainty band attached.

## Status

Running against real data. First pass over the Peco Pocahontas draw area
(50 mi radius), full 50% ITC stack at $2.10/W:

| | |
|---|---|
| Houses detected | 945 |
| Farms | 277 (median 3 houses) |
| Estimated load | 61.2 GWh/yr |
| Recommended capacity | 36.7 MW DC |
| Farms with ≥4 houses | 120 — **76% of the pipeline MW** |

Largest single prospect is a 12-house farm at ~515 kW. Targeting the 120 farms
of four houses or more captures three quarters of the opportunity.

**Read the count as a floor.** Arkansas coverage in the source dataset is 2017
NAIP; Peco opened Pocahontas in 2016 and expanded through 2021, so much of the
grower buildout is simply not in this imagery. That 945 lands close to Peco's
~1,000-house regional figure is encouraging but may be coincidental — the
imagery predates the network the figure describes.

```bash
pip install -r requirements.txt
python -m pytest tests/          # 63 passing
python scripts/clip_to_aoi.py    # one-time: build the committable AOI extract
python scripts/run_spike.py      # count farms, size systems, price them
```

## Getting the barn data in

The pipeline needs the Microsoft `poultry-cafos` national predictions (128 MB
GeoPackage, 360,857 polygons). That host is refused by some managed egress
policies with a `403 to CONNECT` — a policy denial, not a network fault.

**The durable fix is to commit a clipped extract**, so the download happens once
and never again. On any machine with normal internet:

```bash
git clone https://github.com/FiftyClint/solarbid.git && cd solarbid
python -m pip install -r requirements.txt
python scripts/clip_to_aoi.py          # downloads, clips to the Peco AOI
git add data/peco_aoi_barns.gpkg
git commit -m "Add Peco AOI barn extract" && git push
```

<details>
<summary>Windows PowerShell</summary>

Windows PowerShell 5.1 does not accept `&&` as a statement separator, and `pip`
is often not on PATH even when Python is. Run one line at a time:

```powershell
cd $HOME
git clone https://github.com/FiftyClint/solarbid.git
cd solarbid
git checkout claude/chicken-house-solar-tool-k8eu3s
python -m pip install -r requirements.txt
python scripts\clip_to_aoi.py
git add data/peco_aoi_barns.gpkg
git commit -m "Add Peco AOI barn extract"
git push
```

If the dependency install fails to build wheels, the Python version is likely
newer than the geospatial stack supports. Install Python 3.12 and use
`py -3.12 -m pip install -r requirements.txt`, then `py -3.12 scripts\clip_to_aoi.py`.

</details>

`resolve_barn_source()` prefers that extract whenever it exists, so every later
run — anywhere, including restricted environments — needs no network at all.

Two alternatives: drop the national `.gpkg` in `./data/` by hand, or allowlist
`researchlabwuopendata.blob.core.windows.net` in the environment's network
policy.

## How it works

| Stage | Module | What it does |
|---|---|---|
| Fetch | `data.py` | Cache the national barn polygon set, carry its provenance |
| Find | `sites.py` | Clip to the plant catchment, screen on shape, cluster houses into farms |
| Load | `load.py` | Floor area → birds → live weight → annual kWh **band** |
| Size | `siting.py` | Roof and ground capacity, then Act 278-aware sizing |
| Gate | `incentives.py` | Dated ITC rate resolution (base + adders), REAP status |
| Finance | `finance.py` | Net cost after credit, bonus depreciation and grant |
| Quote | `quote.py` | Stage-one budgetary estimate, ranged and clearly not a bid |

**Finding houses is the easy part.** Microsoft already published a U-Net trained
on 1m USDA NAIP imagery *and* the resulting national polygon set, so stage one
is a spatial filter, not a training job. Poultry houses are then trivially
separable on shape: 300–600 ft long, 30–70 ft wide, 8–15:1 aspect.

**A farm, not a house, is the unit of sale.** One owner, one service, one quote.
Houses within 200 m are clustered into a farm.

## Two stages

**Stage one is screening.** Everything derives from aerial imagery and public
data, costs nothing per farm, and exists to get a grower to raise their hand.
Precision is not the goal and chasing it is wasted money — a farm that never
responds does not deserve an 8760 simulation. `quote.py` produces this.

**Stage two starts when they respond**: twelve months of interval data, a
structural review for roof, parcel and land cover for ground, site-specific
irradiance modelling, and a firm bid.

This is why production uses a flat 1,450 kWh/kW planning figure. At stage one
the load band already spans 4×, so a precise irradiance model would be false
precision bolted onto a rough number. Stage-one system size is quoted as a
**range driven by the load band** — 85 to 355 kW on a representative four-house
farm — because that is where the real uncertainty lives.

## Three things that decide whether a quote is any good

**1. Load estimation is the weak link.** University of Arkansas audits of real
Arkansas broiler houses found usage spanning **20 to 83 kWh per 1,000 lb of
broiler sold, mean 44** — a 4× spread reflecting genuine farm-to-farm variation
in house age, fan efficiency and management. That is why `estimate_load()`
returns a band and `requires_metered_validation()` exists. Geometry alone
cannot size a system tightly enough to bid. Twelve months of interval data, or a
University of Arkansas farm energy audit, is the cheapest way to collapse it.

The one favourable structural fact: **~88% of poultry house electricity is
ventilation fans**, so load peaks on summer afternoons, coincident with peak
generation. Solar self-consumption on poultry is unusually good.

**2. Arkansas Act 278 inverts the sizing logic.** Systems energised after
2024-09-30 no longer get 1:1 net metering. On-site consumption avoids retail
(~12¢); exports are credited at avoided cost (~2.5¢). Sizing to "offset the
annual bill" — correct under the old rules — produces economics that are wrong
by a wide margin today. `recommend_size_kw()` instead walks the array up in 5 kW
steps and stops when the marginal kW stops earning out.

The gap this opens is the central design insight:

```
4-house farm, 86,000 sq ft under roof
  load             : 150,309 kWh/yr  (range 68,322 – 283,537)
  roof capacity    : 426 kW DC       ← physical
  recommended      : 185 kW DC       ← economic, at the full 50% stack
```

Surface is never the constraint. Self-consumption is.

**3. Roof and ground are quoted side by side, not as fallback.** At $2.00/W
roof against $2.10/W ground, roof wins on economics — but by ~$2,300 and 0.19
years on a four-house farm, which is thin enough that the decision belongs to
the site walk. Roof structural capacity on light-gauge metal over wood trusses
is a per-site engineering call this tool cannot make, so
`roof_requires_structural_review` is always true.
Ground siting is worse than it looks: `open_ground_area_ft2()` finds land that is
merely *not built on* and knows nothing about cropping, land cover, floodplain or
ownership. Both need verification before a quote goes out.

## Incentives are dated gates, not constants

Every incentive that moves a poultry solar deal is mid-transition, so
`incentives.py` takes a date and returns a status with its basis attached.
Anything unresolvable from public data is reported as **unresolved** rather
than silently assumed favourable.

**Target: placed in service by 2027-12-31.** OBBBA's begin-construction deadline
(2026-07-04) has passed, so that date is the surviving path to Sec. 48E — and it
sets the schedule for everything else.

- **Base ITC — 30%.** Systems under **1 MW AC** are deemed to satisfy prevailing
  wage and apprenticeship, taking the full 30% *and* full 10-point adders with
  no compliance burden. Farm systems run 50–150 kW, an order of magnitude
  inside. This is the most favourable structural fact in the model.
- **Domestic content — +10%.** Adjusted percentage threshold is **50%** for a
  2026 construction start, 55% for 2027. Evidenced via the Notice 2025-08
  elective safe harbor tables.
- **Energy community — +10% of project cost.** The Peco footprint qualifies
  under the **Statistical Area** category, which resolves to whole counties.
  Confirmed eligible: **Randolph, Clay, Lawrence, Greene, Independence, Izard,
  Sharp, Fulton, Jackson, Mississippi** — Pocahontas sits in Randolph, so the
  plant's home county is in. Craighead (Jonesboro) is not.
  `energy_community_by_county()` carries the list.

  Statistical Area status is **redetermined annually** on the unemployment
  test, so the list has a shelf life. What defuses that is the Notice 2023-29
  **beginning-of-construction safe harbor**: a project in an energy community
  on its BOC date is treated as being in one at placed-in-service, for the full
  credit. Starting construction while these counties are on the current list
  locks the 10 points — the calendar risk is on the start date, not the
  finish date.
- **Bonus depreciation — 100%, permanent** for property acquired after
  2025-01-19. Depreciable basis is reduced by half the ITC, so a 50% credit
  leaves 75% of cost depreciable. Note OBBBA also repealed 5-year MACRS for
  solar where construction began after 2024-12-31 — moot under full bonus, but it
  bites hard if the grower elects out.
- **FEOC / material assistance — applies to every project here.** Facilities
  beginning construction after 2025-12-31 must clear a material assistance cost
  ratio. Failing it **denies the credit entirely**, not just the adders. Safe
  harbor tables in Notice 2026-15 (2026-02-12); supplier attestations needed
  before ordering.
- **USDA REAP — halted 2026-03-31** pending new regulations under EO 14315.
  Guaranteed loans continue. No grant line until it reopens.

### What the stack does to a four-house farm

At our $2.10/W, load 150,309 kWh/yr, roof capacity 426 kW DC, in Randolph County:

| Scenario | ITC | Grower tax rate | Net $/W | Size | Payback |
|---|---|---|---|---|---|
| Base ITC + depreciation | 30% | 30% | $0.93 | 120 kW | 7.4 yr |
| + Energy community | 40% | 30% | $0.76 | 140 kW | 6.4 yr |
| **+ Domestic content** | **50%** | **30%** | **$0.58** | **185 kW** | **5.6 yr** |
| Full stack, low tax appetite | 50% | 10% | $0.89 | 125 kW | 7.2 yr |

Two things fall out of this. The adders don't just cut the price — they change
the **system**, taking the economically sensible array from 120 kW to 185 kW,
because cheaper capacity stays worth building further up the declining
self-consumption curve.

And **the grower's tax rate moves the answer nearly as much as the adders do**.
Net cost is a property of the buyer, not the project. Many contract growers
cannot absorb a 50% credit plus full first-year expensing, and a Sec. 6418
transfer on a single 50 kW system realises ~$48k of a $52.5k credit before
diligence cost — which only works aggregated across farms. Confirm tax capacity
with the grower's CPA before any of these numbers become a price.

## Known limitations

- **Dataset vintage.** Predictions generated 2021-03-13 from NAIP flown ~2019–20.
  Peco expanded the Pocahontas complex through 2020–21, so newer houses are
  absent. Counts are a **floor, not a census**; re-running the released U-Net on
  current NAIP is the fix.
- **Self-consumption curve is a placeholder.** The anchors in
  `_SELF_CONSUMPTION_CURVE` are engineering judgement, not measurement, and must
  be replaced with an 8760 simulation against real interval data before any
  binding proposal.
- **No PVWatts, deliberately.** Flat 1,450 kWh/kW is a stage-one planning
  figure. Site-specific modelling belongs in stage two, after a grower responds.
- **Mount economics are nearly a wash.** $2.00/W roof against $2.10/W ground
  separates a four-house farm by ~$2,300 net and 0.19 years of payback. Roof
  wins on paper, but the margin is thin enough that structural feasibility and
  land availability should decide it, not the spreadsheet.
- **Co-op tariffs are unmodelled.** Craighead, Clay County, Farmers and Woodruff
  each set their own rates and demand charges, with no clean API. Hand-entry per
  utility, verified per quote.
- **Energy community list needs an annual refresh.** Statistical Area status is
  redetermined each year. The county list here reflects the current notice;
  re-check it annually, and lean on the BOC safe harbor to lock status on
  projects already started.
- **Domestic content is asserted, not evidenced.** The model takes a boolean.
  Actually claiming it needs a bill of materials clearing 50% adjusted
  percentage, run through the Notice 2025-08 safe harbor tables.
- **FEOC compliance is flagged, not computed.** Failing the material assistance
  cost ratio denies the credit outright, so this needs a real supplier
  attestation workflow before equipment is ordered.
- **Tax capacity is an input, not a check.** `project_finance()` takes the
  grower's marginal rate on faith. It moves net cost nearly as much as the
  adders do, and contract growers frequently cannot absorb the full stack.

## What this does not produce

A bindable number. It produces a ranked prospect list and a preliminary system
concept. Every quote still needs interval data, a structural review for roof,
parcel and land cover for ground, and a live check of the incentive stack.

## Sources

- [microsoft/poultry-cafos](https://github.com/microsoft/poultry-cafos) — MIT code, Open Use of Data Agreement v1.0 data
- [Mapping Industrial Poultry Operations at Scale with Deep Learning and Aerial Imagery](https://arxiv.org/abs/2112.10988)
- [UADA — chicken house electricity audit and peak demand](https://www.uaex.uada.edu/media-resources/news/2024/september2024/09-16-2024-ark-broiler-house-electricity-usage.aspx)
- [UADA — Poultry Farm Energy Use Evaluation Program](https://www.uaex.uada.edu/environment-nature/energy/conservation.aspx)
- [UADA — Arkansas net metering policy](https://www.uaex.uada.edu/environment-nature/energy/solar/net-metering.aspx)
- [Navigating safe-harbor rules for Sec. 48E facilities](https://www.thetaxadviser.com/issues/2026/feb/navigating-safe-harbor-rules-for-solar-and-wind-sec-48e-facilities/) · [IRS Notice 2025-42](https://www.irs.gov/pub/irs-drop/n-25-42.pdf)
- [IRS — prevailing wage and apprenticeship FAQ](https://www.irs.gov/credits-deductions/frequently-asked-questions-about-the-prevailing-wage-and-apprenticeship-under-the-inflation-reduction-act) (one-megawatt exception)
- [IRS — domestic content bonus credit](https://www.irs.gov/credits-deductions/domestic-content-bonus-credit) · [Notice 2025-08 elective safe harbor](https://www.irs.gov/pub/irs-drop/n-25-08.pdf)
- [DOE — Energy Community Tax Credit Bonus mapper](https://energycommunities.gov/energy-community-tax-credit-bonus/) · [Holland & Knight on Notice 2026-39](https://www.hklaw.com/en/insights/publications/2026/07/irs-releases-2026-energy-community-bonus-credit-updates)
- [Morgan Lewis — Notice 2026-15 material assistance cost ratio](https://www.morganlewis.com/pubs/2026/02/meeting-the-macr-irss-interim-guidance-addresses-obbbas-material-assistance-feoc-limitation) · [Bracewell on FEOC guidance](https://www.bracewell.com/resources/treasury-and-irs-issue-guidance-on-foreign-entity-of-concern-rules-for-clean-energy-tax-credits/)
- [SEIA — MACRS depreciation of solar energy property](https://seia.org/depreciation-solar-energy-property-macrs/)
- [NSAC — USDA halts rural energy investments](https://sustainableagriculture.net/blog/release-usda-halts-rural-energy-efficiency-investments/)
