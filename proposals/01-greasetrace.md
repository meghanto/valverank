# GreaseTrace: find out what's flooding Houston's bayous with sewage

> **One line:** Houston's sewer system overflows thousands of times a year. GreaseTrace traces each overflow upstream through the city's real sewer network to the pipes and businesses most likely causing it. It then tells crews where to clean and inspect first, and shows on held-out real data how many overflows that plan would have caught.

**Targets:** Best Overall ($1,000), Best Environment Hack ($500), Best Pitch/Demo ($500)

---

## 1. The problem

| Fact | Number | Source |
|---|---|---|
| Sanitary sewer overflows (SSOs) recorded by the City since 2021 | **20,457** | City SSO layer, queried 2026-10-10 |
| SSOs in 2025 | **3,898** | Same |
| 2025 SSOs the City itself classes as **"Preventable"** | **2,609 (67%)** | Same, `CAUSECLASS` field |
| SSOs since 2021 caused by grease | **5,936** | Same, `CAUSE LIKE '%Grease%'` |
| SSOs since 2021 caused by rags/wipes | **8,206** | Same |
| Watershed with the most 2025 SSOs | **Brays Bayou (1,025)**, then Sims (911), Buffalo (583), White Oak (531) | Same, `WATERSHED` field |
| Federal consent decree requiring Houston to fix this | Signed 2021. First estimate ~$2B; city materials now cite ~$9B *[re-verify before pitch]* | [Houston Public Works](https://houstonpublicworks.org/wastewater-cd), [Council briefing Aug 2024](https://311.houstontx.gov/council/committees/servicedelivery/2024_08_28/consent_decree.pdf), [NACWA](https://www.nacwa.org/news-publications/water-sector-news/2021/04/02/mayor-turner-announces-consent-decree-work-begins-to-upgrade-houston's-wastewater-system) |

Spill volumes are in `TOT_VOL_L`, **in gallons**: the Goodyear Dr spill reported in the press as ">100,000 gallons" is 172,340 in the data. 2025 total: 1.87M gallons.

**Primary source to cite first:** the City's [FY2025 Consent Decree Annual Report](https://www.houstonpublicworks.org/media/5746/download). Public SSOs: FY22 1,266, FY23 1,235, FY24 1,377, FY25 1,813 (102 from Hurricane Beryl). Grease + wipes share fell 73% → 60%; grease alone is 38%. The FOG program ran 30,032 inspections in FY25, yet grease SSOs rose 550 → 686. There are 112 repeat-SSO locations. Full breakdown in `news.md` §1.

**What makes this hard:** an overflow appears at a manhole, but the grease that caused it came from somewhere upstream. Any of hundreds of pipes and dozens of restaurants could be the source. Today the City largely re-cleans locations that have overflowed before, which is reactive.

---

## 2. What we build

1. **The sewer network as a directed graph.** 143k public gravity mains plus 136k manholes. Flow direction comes from the upstream/downstream manhole fields and pipe invert elevations.
2. **Snapping each overflow onto the graph.** Every SSO record already carries the IDs of the pipes upstream and downstream of it (`US_GMUFID`, `DS_GMUFID`), so no guessing is needed.
3. **Upstream trace.** For any overflow, a reverse breadth-first search finds every pipe, manhole, parcel and restaurant that drains into it.
4. **Risk model.** Score each pipe segment's chance of a grease or wipes blockage in the next period. Inputs:
   - its overflow and stoppage history (235k stoppage records)
   - restaurant density upstream
   - slope, diameter, material, age
   - the City's own condition score for that pipe (PACP)
5. **Crew planner.** Given *K* crew-days per month, choose which segments to clean and which restaurants to inspect so that predicted overflows (or spill volume) avoided is as high as possible. This is a budgeted-coverage problem; greedy selection carries a (1 − 1/e) guarantee.
6. **Backtest.** Train on overflows before 2025. Predict 2025's 3,898. Report what share of 2025 overflows fall in our top-K segments, against the City's implicit baseline of "re-clean last year's overflow sites".

---

## 3. 90-second demo

| Time | Judge sees | Narration |
|---|---|---|
| 0–15 s | Map of Houston's bayous with 2025 overflow dots, Brays Bayou glowing red | "Last year Houston's sewers overflowed 3,898 times. The City calls two-thirds of them preventable." |
| 15–35 s | **Judge clicks** an overflow dot on Brays. The network upstream lights up and flows animate back toward their sources. | "This overflow happened here. The cause is somewhere up here." |
| 35–55 s | A ranked side panel: suspect pipe segments and upstream restaurants, each with a reason (repeat stoppages, flat slope, 14 restaurants upstream) | "GreaseTrace ranks the likely culprits from the City's own pipe and overflow records." |
| 55–75 s | **Judge drags** a "crew-days per month" slider from 5 to 20. Selected segments update, and the counter shows predicted overflows avoided. | "Give us a crew budget and we tell you where to send it." |
| 75–90 s | Backtest card: "Trained on 2021–2024. On 2025, our top-K plan covers X% of overflows. Re-cleaning repeat sites covers Y%." | "We checked it against what actually happened." |

---

## 4. Fit with Orion's judging criteria

| Criterion | How GreaseTrace scores |
|---|---|
| **Originality** | No hackathon project found that traces overflows upstream to grease sources. Closest on Devpost: one random-forest overflow predictor, not Houston and no network trace. Commercial tools such as Autodesk InfoAsset are licensed desktop products. |
| **Relevance to track (Environment)** | Raw sewage in bayous is pollution that hits local communities. It falls squarely under the track's "pollution" and "protection of local ecosystems and communities". |
| **Impact** | Every Houston bayou. A federal consent decree with EPA-enforced deadlines. The method applies to every US city under a sewer consent decree. |
| **Demo** | The judge clicks a real overflow and watches the trace. The judge moves the crew budget and sees a measured result. |
| **Technical implementation** | Directed-graph construction over 143k pipes, upstream traversal, a learned risk model, budgeted optimization, and a time-split backtest on real outcomes. |

---

## 5. Business case (for Best Pitch/Demo)

- **Primary buyer:** Houston Public Works, Wastewater Operations. It is under a consent decree that mandates grease and debris cleaning programs. The tool turns those mandates into a ranked weekly work list.
- **Secondary buyers:** other utilities under EPA sewer consent decrees, and grease-trap service companies (lead generation).
- **Existing alternatives:**

  | Alternative | Gap |
  |---|---|
  | Re-clean past overflow sites (status quo) | Reactive; misses first-time overflows |
  | Fixed-interval cleaning schedules | Ignores where grease actually comes from |
  | Licensed hydraulic/asset tools (InfoAsset and similar) | Expensive, need consultants, no restaurant-source attribution |

- **Differentiation:** built on the city's public data, attributes overflows to upstream sources, and proves its value with a backtest.
- **Beyond the hackathon:** pilot with one wastewater service area. The same pipeline runs on any city's GIS exports.
- **Sponsor fit:** RSM judges see a compliance-risk product (consent-decree exposure). Chevron judges see asset-integrity analytics.

---

## 6. Technical design

```
City ArcGIS REST ──► ingest (Python) ──► GeoParquet
                                          │
                     build graph (networkx/igraph): manholes = nodes, mains = directed edges
                                          │
       ┌───────────────┬──────────────────┼──────────────────┐
  upstream index   features per edge   SSO ↔ edge join    restaurants (OSM) ↔ parcels ↔ edge
       └───────────────┴──────────────────┼──────────────────┘
                     risk model (LightGBM / Poisson GLM), time-split backtest
                                          │
                     crew planner (greedy budgeted coverage)
                                          │
                     export static JSON / PMTiles ──► React + MapLibre/deck.gl (static site)
```

- **Precompute everything** in Python and ship static files. The hosted site has no backend that can fail during judging.
- **Upstream trace in the browser:** ship an adjacency list for the demo area, or precomputed upstream sets for each overflow node.
- **Projection:** geohwp layers are in EPSG:2278. Request `outSR=4326`.
- **Stack:** Python 3 (geopandas, networkx, lightgbm, shapely), Vite + React + MapLibre GL + deck.gl. Deploy on Vercel or Cloudflare Pages.

## 7. Data (each endpoint queried by us on 2026-10-10)

| Data | Endpoint | Size |
|---|---|---|
| All SSOs | `geohwp.houstontx.gov/arcgis/rest/services/04_BaseData_Operations/SSO_Stoppages_Odor/FeatureServer/5` | 66,385 (2000–2026) |
| Stoppages, repeat SSOs | same service, layers 1 and 6 | 235k / 3.8k |
| Gravity mains | `01_BaseData_Infrastructure/Sewer_Network/FeatureServer/11` | 143k |
| Manholes | `Sewer_Network/FeatureServer/1` | 136k |
| Pipe condition scores (PACP) | `Consent_Decree/GravityMains_PACPScoring/FeatureServer/0` | 146k |
| **311 odor complaints** | `SSO_Stoppages_Odor/FeatureServer/8` (REQUEST_ID, PROBLEM_CD, address, meter basin) | **33,425** (2005 → Apr 2026) |
| **Stoppage work orders** | `SSO_Stoppages_Odor/FeatureServer/1` (asset UFID/COMPKEY) | **235,365** (2009 → May 2026) |
| **311 sewer service requests** | `services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/SanitarySewer_ServiceRequest_2009_2019/FeatureServer/0` | **244,070** (2009 → Aug 2019). "Sewage in residence" 66.6k, "SSO" 44.9k, "Blockage" 33.7k, "Odor" 12.1k, "cave-in" 12.7k |
| Restaurants | OpenStreetMap Overpass (`overpass-api.de`) | 709 in central Houston alone |

**How 311 is used:** resident complaints are a *leading indicator*. Odor calls and sewage-backup calls upstream of a manhole should come before an overflow there. They enter the risk model as time-windowed features: complaints in the upstream area over the prior 30, 90 and 365 days. The backtest then shows whether 311 adds predictive lift ("residents' 311 calls predicted X% of overflows Y days ahead"). 2009–2019 service requests serve as training history. Odor complaints and stoppages run to 2026, so they work for the 2025 holdout.

All City layers are public, need no key, return 2,000 records per page and support pagination.

## 8. Claims we will and won't make

- **Will:** "On 2025 data the model was never trained on, our plan covers X% of overflows against Y% for the baseline." Fill in the measured numbers.
- **Won't:** name specific restaurants as polluters on stage. Show them as "upstream food-service sites", ranked by drainage, not by blame. The ranking is a list of places to inspect, not an accusation.
- **Won't:** claim volumes until the `TOT_VOL_L` unit is confirmed.

## 9. Build plan (hacking ends Sun 1:00 PM)

| Window | Work |
|---|---|
| Sat 3:30–6 PM | Pull all layers to GeoParquet, build the graph, check edge directions, snap SSOs to edges. Deploy a skeleton map. |
| Sat 6–10 PM | Upstream trace, feature table, restaurants joined to parcels and pipes. First risk model and backtest number. |
| Sat 10 PM–2 AM | Crew planner, UI (bayou view, click-to-trace, ranked panel, slider), static data export |
| Sun 2–6 AM | Improve the backtest (features, baseline comparison), fix data-quality problems, animate the trace |
| Sun 6–9 AM | Polish, performance, README with method and AI-tool disclosure. **Feature freeze 9 AM.** |
| Sun 9 AM–12:30 PM | Devpost write-up, slides, demo rehearsal, fallback recording |

## 10. Risks

| Risk | Mitigation |
|---|---|
| Graph breaks: missing upstream/downstream manholes, wrong flow direction | Fall back to invert elevations, then geometry endpoints. Report how much of the network is connected. |
| Backtest shows only a small gain over the baseline | Report it honestly. Compare against several baselines (random, repeat sites, condition score). |
| Demo is less dramatic than a live-impact demo | Animate the upstream flow, start from bayou impact, and let the judge drive the controls. |
| Restaurant data is incomplete in OSM | The model still runs on pipe and history features. Restaurants are a bonus feature. |
| Sponsor sensitivity | None identified. This is municipal infrastructure. |
