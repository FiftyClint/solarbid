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
python -m pytest tests/          # 23 passing, synthetic geometry
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
| Gate | `incentives.py` | Dated ITC and REAP eligibility rules |

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
  recommended      :  50 kW DC       ← economic, at 30% ITC
```

Surface is never the constraint. Self-consumption is.

**3. Roof and ground are quoted side by side, not as fallback.** Roof structural
capacity on light-gauge metal over wood trusses is a per-site engineering call
this tool cannot make, so `roof_requires_structural_review` is always true.
Ground siting is worse than it looks: `open_ground_area_ft2()` finds land that is
merely *not built on* and knows nothing about cropping, land cover, floodplain or
ownership. Both need verification before a quote goes out.

## Incentives are dated gates, not constants

Both incentives that move a poultry solar deal are mid-transition, so
`incentives.py` takes a date and returns a status with its basis attached.

- **Federal ITC (Sec. 48E).** OBBBA set a begin-construction deadline of
  2026-07-04 — **already passed**. A project starting now needs a
  placed-in-service date on or before **2027-12-31**, or documented
  safe-harboured equipment. Real, closing, and it belongs in the sales
  conversation.
- **USDA REAP.** Grant awards **halted 2026-03-31** pending new regulations
  under EO 14315. Processing stopped; prior applicants must reapply. Guaranteed
  loans continue. Any proposal showing a REAP grant line today quotes a program
  not accepting grant applications.

Run both gates today and the stack returns **0%** — at which point
`recommend_size_kw()` correctly returns no system, because at $2.35/W and 12¢
retail, unsubsidised simple payback is ~13.5 years even at perfect
self-consumption. That is the finding, not a bug:

| Incentive stack | Recommended | % of load |
|---|---|---|
| None (today) | 0 kW | — |
| 30% ITC | 50 kW | 48% |
| ITC + REAP restored | 85 kW | 82% |

The commercial question this raises is whether the near-term play is
safe-harboured equipment and a 2027 energisation, rather than a 2028 pipeline.

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
- **Incentive stacking is naive.** `total_incentive_fraction()` sums fractions;
  real stacking has ordering and basis-reduction rules (REAP grant proceeds
  reduce ITC basis).

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
- [NSAC — USDA halts rural energy investments](https://sustainableagriculture.net/blog/release-usda-halts-rural-energy-efficiency-investments/)
