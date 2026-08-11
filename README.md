# solarbid

Prospecting and preliminary solar sizing for poultry farms in the Peco Foods
Pocahontas draw area, northeast Arkansas.

Given public aerial imagery, find the chicken houses, estimate what each farm
spends on electricity, and produce a preliminary roof-and-ground system concept
with an honest uncertainty band attached.

## Status

The site-finding, load and sizing logic is implemented and tested. The barn
polygon dataset has **not** been ingested yet — see [Blocked](#blocked).

```bash
pip install -r requirements.txt
python -m pytest tests/          # 35 passing, synthetic geometry
python scripts/run_spike.py      # needs the dataset (see below)
```

## Blocked

`scripts/run_spike.py` needs the Microsoft `poultry-cafos` national predictions
(128 MB GeoPackage, 360,857 barn polygons):

```
https://researchlabwuopendata.blob.core.windows.net/poultry-cafo/full-usa-3-13-2021_filtered_deduplicated.gpkg
```

That host is currently refused by the egress proxy at the policy layer
(`403 to CONNECT`, not a network fault). Either allowlist
`researchlabwuopendata.blob.core.windows.net`, or download the file
out-of-band and drop it in `./data/`. Everything downstream then runs.

## How it works

| Stage | Module | What it does |
|---|---|---|
| Fetch | `data.py` | Cache the national barn polygon set, carry its provenance |
| Find | `sites.py` | Clip to the plant catchment, screen on shape, cluster houses into farms |
| Load | `load.py` | Floor area → birds → live weight → annual kWh **band** |
| Size | `siting.py` | Roof and ground capacity, then Act 278-aware sizing |
| Gate | `incentives.py` | Dated ITC rate resolution (base + adders), REAP status |
| Finance | `finance.py` | Net cost after credit, bonus depreciation and grant |

**Finding houses is the easy part.** Microsoft already published a U-Net trained
on 1m USDA NAIP imagery *and* the resulting national polygon set, so stage one
is a spatial filter, not a training job. Poultry houses are then trivially
separable on shape: 300–600 ft long, 30–70 ft wide, 8–15:1 aspect.

**A farm, not a house, is the unit of sale.** One owner, one service, one quote.
Houses within 200 m are clustered into a farm.

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
  recommended      : 150 kW DC       ← economic, at the full 50% stack
```

Surface is never the constraint. Self-consumption is.

**3. Roof and ground are quoted side by side, not as fallback.** Roof structural
capacity on light-gauge metal over wood trusses is a per-site engineering call
this tool cannot make, so `roof_requires_structural_review` is always true.
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
- **Energy community — +10%.** Per **census tract**, from IRS Notice 2026-39
  (2026-06-10). **Cannot be inferred from the county** — it must be looked up per
  site at [energycommunities.gov](https://energycommunities.gov/energy-community-tax-credit-bonus/).
  Randolph County status is currently unresolved in this repo.
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

Gross $2.35/W, load 150,309 kWh/yr, roof capacity 426 kW DC:

| Scenario | ITC | Grower tax rate | Net $/W | Size | Payback |
|---|---|---|---|---|---|
| Gross cost, no tax benefit | 0% | 0% | $2.35 | 0 kW | — |
| Depreciation only, no ITC | 0% | 30% | $1.65 | 50 kW | 10.4 yr |
| Base ITC + depreciation | 30% | 30% | $1.05 | 95 kW | 7.6 yr |
| + Domestic content | 40% | 30% | $0.85 | 130 kW | 6.9 yr |
| **Full stack (DC + EC)** | **50%** | **30%** | **$0.65** | **150 kW** | **5.7 yr** |
| Full stack, low tax appetite | 50% | 10% | $1.00 | 100 kW | 7.4 yr |
| Full stack, no tax appetite | 50% | 0% | $1.18 | 85 kW | 8.2 yr |

Two things fall out of this. The adders don't just cut the price — they change
the **system**, tripling the economically sensible array from 50 kW to 150 kW,
because cheaper capacity stays worth building further up the declining
self-consumption curve.

And **the grower's tax rate moves the answer nearly as much as the adders do**.
Net cost is a property of the buyer, not the project. Many contract growers
cannot absorb a 50% credit plus full first-year expensing, and a Sec. 6418
transfer on a single 50 kW system realises ~$54k of a $58.7k credit before
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
- **No PVWatts yet.** Specific yield is a flat 1,450 kWh/kW. NREL PVWatts v8 keyed
  off each farm's centroid and ridge azimuth is the next integration.
- **Pricing is unanchored.** $/W figures are placeholders until real bids land.
- **Co-op tariffs are unmodelled.** Craighead, Clay County, Farmers and Woodruff
  each set their own rates and demand charges, with no clean API. Hand-entry per
  utility, verified per quote.
- **Energy community status is unresolved.** Worth 10 points — a third of the
  credit — and it is a per-tract lookup against Notice 2026-39 that has not been
  run for the Peco footprint. Do this before quoting; the two most likely
  qualifying routes here are coal-closure tract adjacency and the statistical
  area criterion.
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
