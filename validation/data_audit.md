# Data audit

Run: Sat 2026-10-10, 22:30–23:45 CDT. How to reproduce:
- `pipeline/server_stats.py`: City server's own counts per field
- `pipeline/ingest_attrs.py`: extra columns used for the audit
- `data/MANIFEST.json`: byte size, sha256, download time per raw file

Verdict scale:
- **OK**: fit for the claim
- **CAVEAT**: usable if the caveat is stated
- **DEFECT**: our use of the data is wrong; fix it before quoting numbers
- **MISSING**: planned but not downloaded

---

## 1. Inventory: what the plan used vs. what we have

| # | Source (planned in `proposals/03-shutoff.txt` §7) | Purpose | Local? | Status |
|---|---|---|---|---|
| 1 | Water mains, `UtilityAnalysis_gx/51` | Network | `mains.json` + `mains_attrs.json` | Have |
| 2 | System valves, `/39` | Cut points, INOP flags | `valves.json` + `valves_attrs.json` | Have |
| 3 | Hydrants, `/46` | Fire-impact count | `hydrants.json` | Have |
| 4 | Customer accounts, `CAS/Customer_Operation_gx/1` | Who loses water | `customers.json` | Have |
| 5 | Pressure-reducing stations, `/48` | Supply / zone boundaries | `prs_attrs.json` (93) | Have since tonight, **not used in model** |
| 6 | Control valves, `/38` | (not in plan) Check whether any are isolation valves | `control_valves_attrs.json` (4,840) | Have since tonight. Types: blow-off 2,681, air release 1,684. Not isolation valves, correctly excluded. |
| 7 | Critical facilities, `HPC/CriticalFacilities` | Care homes / schools hit | `facilities_*.json` | **UNUSABLE for public use**: licensed Data Axle data ("not to be distributed outside H-GAC"); no hospitals, schools or fire stations. City open-data replacements are stale (2020–21): CAVEAT. See `data_audit_extra.md`. |
| 8 | 311 water requests, Winter Storm Uri (11,041; 3,429 "Water Main Valve") | The plan's **only** independent check of the INOP flags | `uri311.json` | Have. Data: CAVEAT (no date field; dates inferred as Feb 13–25 2021). **Test: null.** Valve requests are no closer to INOP valves than other water requests (−0.2 pp, 95% CI [−1.8, +1.5]). See `data_audit_extra.md`. |
| 9 | 311 counts by ZIP | Context | — | **MISSING** |
| 10 | News-reported breaks | Outage-size validation | `validation/news_breaks.csv`: 12 events, every row has a source URL; **only 3 have a count** | Have, thin |
| 11 | HPW financial reports FY23–25 (independent totals) | Cross-check our counts | Figures in §3 below | Have (figures, not files) |
| 12 | Water plants / supply points, `UtilityAnalysis_gx/44` "Network Structure" (402: wells 181, pump stations 92, ground tanks 92, elevated tanks 25, "surface water treatment plant" 12) | Supply-loss model | `structures_attrs.json` | Have. CAVEAT: labels are inconsistent (several "surface water treatment plant" points are named groundwater plants). We use subtypes 14–17 that are in service (218); all snap to a main ≤300 m (median 0 m, 90th percentile 42 m). |

## 2. Provenance

| Dataset | Publisher / service | Layer name on server | Parent group | Server count now | Local count | Last edit in data |
|---|---|---|---|---|---|---|
| Mains | City of Houston, `geogimsms.houstontx.gov` HPC/UtilityAnalysis_gx | "Pump Pressure Main (By Type)" | Drinking Water Distribution System → Mains (siblings: Lateral Service /50, Casing /52) | 290,959 | 290,959 | DATEMODIFIED max **2023-05-30** |
| Valves | same | "System Valve" | Drinking Water Distribution System | 166,362 | 166,362 | **2023-06-05** |
| Hydrants | same | "Hydrant" | same | 62,540 | 62,540 | **2023-06-05** |
| Customers | City of Houston, CAS/Customer_Operation_gx (Customer Account Services) | "Customer Accounts" | — (siblings: Drainage Charges, Payment Locations, Parcels) | 544,011 | 544,011 | No date field. **Snapshot date unknown.** |

- **No license or description.** None of these services publishes a copyright notice, terms, or a layer description. The data is public and needs no login, but there is no documentation.
- **Native coordinates:** EPSG:2278 (Texas South Central, US feet). We request WGS84 (`outSR=4326`); the server does the conversion.
- **Live service matches our copy.** Counts are identical tonight. The service is a frozen 2023 export.
- **Wastewater layers in the same service** (layers 15 and 16, also called "System Valve"/"Control Valve") are a different system. We use 39, which sits under the drinking-water group. Confirmed.

## 3. Cross-check against independent figures (HPW Combined Utility System financial reports)

| Quantity | Ours (June 2023 snapshot) | Published | Match | Verdict |
|---|---|---|---|---|
| Miles of main | 7,218 mi | FY23: 7,660 mi **total**, which includes hydrant leads 4.35% and fire/meter lines 2.18% (2023 council deck). Without those: **≈7,160 mi** | **101%** | OK. Layer 51 = distribution + transmission + well collection. Leads are in /50, which we don't use. |
| Transmission share | 438.7 + 5.8 mi ≈ **6.2%** | 5.70% | ✓ | OK |
| Well collection | 59 mi (0.8%) | 0.70% | ✓ | OK |
| System valves | 166,362 | "170K system valves" (2023 deck) | 98% | OK |
| Hydrants | 62,540 | 62,509 (FY23) | 100% | OK |
| Customer accounts | 544,011 | **496,945 active water accounts (FY23)**; 509,561 (FY25) | **107–109%** | **CAVEAT.** CAS accounts include something besides active water accounts (inactive, drainage-only, or sewer-only accounts?). Our counts are ~8% high, unevenly in space. |
| Material, PVC / AC / CI (share of known length) | 54% / 21% / 13% | 49.6% / 18.3% / 13.9% | Close | OK |
| Material, ductile iron | **4.2%** | **11.6%** | ✗ | CAVEAT. 14.8% of our length has no material. Doesn't affect segments; matters only if we use material. |

**Conclusion:** the four layers are the City's real drinking-water system, complete as of mid-2023. They are the right data for valve-isolation segments. The customer count needs a caveat.

## 4. Quality of each field we depend on

### Mains
| Check | Result | Verdict |
|---|---|---|
| Geometry | 0 null, 0 multipart | OK |
| Lifecycle | In use 290,879; rehab 53; abandoned 18; proposed 1; null 8 | OK. **We don't filter on it**: the 19 abandoned/proposed pipes are modeled as live. Negligible, but filter anyway. |
| Water type | Potable 290,225; non-potable well collector 521; non-potable 8; null 205 | CAVEAT. Non-potable well collectors (~36 mi) shouldn't carry customers. Filter. |
| Owner | City 289,365; private 1,588 | OK. Private mains are still connected to the system. |
| Diameter | 1,163 null/0 (0.4%) | OK |
| In-service date | 15,210 null (5%) | OK (only used for display) |

### Topology (pipes joined at shared endpoints, valves ignored)
| Check | Result | Verdict |
|---|---|---|
| Connected components | 181. Largest = **93.7%** of length (6,762 mi). 2nd: **300 mi, Kingwood** (lon −95.26…−95.13, lat 30.02…30.10, 20,761 customers). 3rd: 31 mi (Lake Houston / Atascocita area). 93 tiny fragments under 100 m. | OK. Kingwood is plausibly a separate system with its own groundwater plants. **Unconfirmed.** |
| Dead ends | 16,552 (6.1% of nodes) | Expected: cul-de-sacs |
| Unnoded tees (a dead end within 1.5 m of another pipe's interior, not its endpoint) | **970** (104 within 0.5 m) | **DEFECT (minor).** These branches look disconnected from the pipe they tee into. Each forms its own segment, which makes paper segments too small. Fix: snap and split at ≤1 m. |
| Near-miss endpoints (dead end within 2 m of another node) | 2,455 | CAVEAT. Some are real gaps, some digitizing error. |

### Valves: the main finding
| Subtype (City's code) | On main, at a junction | On main, mid-pipe | Off main (>1 m) | INOP on main |
|---|---|---|---|---|
| Gate (21) | 79,013 | 98 | 3,084 | 14,578 |
| Tapping sleeve (20) | 11,270 | 585 | 8,207 | 2,469 |
| **Hydrant gate valve (33)** | **752** | **8,427** | 52,614 | 135 |
| Butterfly / in manhole (19, 22, 25) | 2,161 | 1 | 10 | 318 |
| Check / unknown / other | 15 | 1 | 124 | 1 |

- **DEFECT (major): 9,179 hydrant gate valves are treated as main shutoffs.** A hydrant gate valve isolates the hydrant lead, not the main. Our 1 m snap catches them because the lead tees off the main. 8,427 of them **split mains mid-pipe**, creating cut points that don't exist. Effect: both paper and real segments are too small. Since these are rarely INOP (135), the paper scenario is hit hardest. **The headline numbers (11.9 → 25.1 customers per break) are biased and must be recomputed** before anyone quotes them.
  - Same issue, smaller: `VALVE_USE` = HYD LEAD 2,576 on main, SERVICE 563, FIRE SERVICE 122.
  - Fix: exclude subtype 33 and VALVE_USE ∈ {HYD LEAD, HL, SERVICE, SERV, FIRE SERVICE} from cut points.
- **CAVEAT: in-line valves missed.** In-line valves more than 1 m from a main: INL 185, IN LINE 920, IN LINE - SLF 334 (1.8% of in-line valves). Fix: allow ≤3 m for in-line valves.
- **CAVEAT: condition is unknown for 58% of valves** (null 96,732). The real scenario treats unknown as working, so INOP is a **floor**.
- Condition dates: 2015–2022, peak 2020 (32,862). Only 735 in 2023. The 78% "inspected 5+ years ago" figure is relative to today (2026), not to the snapshot.
- `INSPECTIONDATE` is essentially empty (394 non-null). Don't use it.
- Normally-closed valves: only 25 of 166,362. Pressure-zone boundaries are barely encoded. Hence the need for the PRS layer.

### Hydrants
| Check | Result | Verdict |
|---|---|---|
| Condition | 100% null | Don't claim anything about hydrant condition |
| Inspected date | 1,331 non-null, of which 1,314 are "1899" (a placeholder) | Unusable |
| Snap to main ≤40 m | 99.4% | OK |

### Customers
| Check | Result | Verdict |
|---|---|---|
| Geometry | 0 null; 539,419 distinct points; 24 points carry ≥10 accounts (max 104) | OK. Apartments are mostly separate points or one account each. |
| City field | Houston 510k; Kingwood 17k; Humble 6k; Missouri City 3k; … | OK. HPW serves some areas outside city limits. |
| Snap to main ≤120 m | 28,899 unassigned (5.3%) | CAVEAT |
| What an "account" is | Not documented; 8% above active water accounts | CAVEAT, see §3 |

## 5. Defects that change our numbers (ordered by impact)

| # | Defect | Effect on headline | Fix cost |
|---|---|---|---|
| D1 | Hydrant / service valves used as main shutoffs | Paper and real segments both too small; the size of the gap is unknown until recomputed | 10 min + 90 s rerun |
| D2 | 970 unnoded tees | Some segments too small | 30 min |
| D3 | 1,439 in-line valves just over the 1 m snap | Some segments too large | 10 min |
| D4 | Abandoned/proposed and non-potable pipes not filtered | Negligible | 5 min |
| D5 | No supply model (plants, PRS, Kingwood) | Big feeder breaks underestimated (Tidwell) | 1–2 h, needs supply-point data |

## 6. What we still can't support

- **"The model matches real outages."** 3 news events with counts. That's an anecdote, not validation.
- **"INOP flags reflect reality."** The Winter Storm Uri 311 check (#8) found no association. The flags stay the City's own records, independently uncorroborated. Frame every number as "what the City's records imply".
- **Anything about 2026.** Every water layer stops in June 2023.
- **Exact customer counts.** Accounts ≠ active water accounts (+8%).

## 7. Fix log

Commit after `99d0d83`. D1, D3, D4 fixed; D2 partly fixed (844 of 970 tees joined at ≤1 m; the other 126 are 1–1.5 m away). D5 open.

| Quantity | Before | After |
|---|---|---|
| Mains modeled | 290,959 | 290,411 (dropped abandoned, proposed, non-potable) |
| Valves used as cut points | 102,323 | 92,763 (66,959 hydrant/service valves excluded) |
| Valves splitting a pipe mid-line | 9,112 | 829 |
| Unnoded tees joined | 0 | 844 |
| Segments, paper / real | 82,085 / 64,803 | 72,253 / 55,076 |
| Customers per break (length-weighted), paper / real | 11.9 / 25.1 | **13.1 / 30.7** |
| Hydrants per break, paper / real | 1.40 / 2.78 | 1.57 / 3.49 |
| Largest segment (customers), paper / real | 329 / 1,896 | 335 / 2,038 |
| INOP valves on mains | 17,501 | 17,413 |

The real/paper ratio went from 2.1× to 2.3×. The direction of the finding held, and the size of the gap grew.

News check after the fix (`validation/model_vs_news.md`; only 4 events report a count):

| Event | Reported | Model, closest pipe (paper → real) | Read |
|---|---|---|---|
| Beltway 8 & Bellfort, 12″ | 74–80 homes and businesses | 8 → 28 | Real scenario is closer; still 3× low |
| Memorial Dr, 24″ | 1 (an apartment complex) | 7 → 7 | Not comparable (one account = many units) |
| Tidwell & Antoine, 16″ | 2,000 | 5 → 5 | Miss: no supply model (D5) |
| Keller St | 9 HISD schools (KPRC: 3); no customer count | 57 → 57 | Not comparable: the unit is schools |

**These checks don't validate the model.** Only 2 events report a customer-like count (Beltway 8, Tidwell), and the model is low on both.

## 8. Supply loss (D5)

`pipeline/supply.py`, verified against brute force (`pipeline/test_supply.py`: 62/62 sampled segments match exactly).

| Quantity | Paper | Real |
|---|---|---|
| Customers per break, isolation only | 13.1 | 30.7 |
| Customers per break, with downstream loss | **16.3** | **38.6** |
| Share of pipe length whose closure cuts off downstream customers | 13.6% | 20.3% |
| Largest single outage | 1,683 | 2,496 |
| Segments with no path to any source | 641 (2,538 customers) | 605 (2,538 customers) |

News check: Beltway 8 & Bellfort is now 22 → 38 (reported 74–80). Tidwell & Antoine is unchanged at 5 (reported 2,000; another report says 100+). The 16″ main there sits in a looped grid, so isolating it cuts nothing off by connectivity. The reported outage was probably pressure loss, which needs a hydraulic model. **D5 is partly fixed: connectivity supply loss is modeled; pressure is not.**

## 9. Search for more outage counts (closed)

About 900 Houston water-break articles, 2010–2026: sitemaps of ABC13, Houston Chronicle, chron.com, FOX 26, Community Impact, Houston Public Media and Houston Press; KHOU and KPRC via the Wayback Machine; the City newsroom and HPW pages. Details in `news_breaks_search_log.md`.

- **No new event reports a count comparable to customer accounts.** NB02 and NB07 remain the only two.
- Added NB13–NB16, all without counts:
  - **NB13** (2014): a leaky valve on a transmission line "threatened roughly 40,000 residents" with low pressure. That's a hydraulic effect, consistent with the Tidwell reading.
  - **NB16** (2024): a planned shutoff with published street boundaries. Usable for an area check, not a count check.
- Counts appear only when an HPW spokesperson quotes one to a reporter. Planned-shutoff notices go out by door hanger, Nextdoor and 311, and aren't archived.
- **Conclusion:** public sources can't validate outage size. The realistic route is a public-records request to HPW for work orders with valve closures and customers out of service. That's the "next step" for the pitch.

## 10. Pressure model (EPANET 2.2, uncalibrated)

`pipeline/hydraulic.py` builds `data/build/houston.inp`: 269k junctions, 290k pipes. One steady-state solve takes 2–5 s.

**Data defect D6, found while building it:** the transmission backbone has gaps. 122 of the 135 dead ends on ≥36″ mains are 1–10 m from another large main (vaults and fittings not noded). `network.py` now joins ≥24″ dead ends to a ≥24″ main within 10 m (256 joins). Segments changed slightly (paper 72,253 → 72,171).

**Assumptions** (constants at the top of `hydraulic.py`):

| Input | Value | Basis |
|---|---|---|
| Surface-water plants (3) | Fixed head, ground + 75 psi | Located from the network itself (dead ends of ≥84″ mains); East matches the geocoded plant address |
| Other sources (218: groundwater plants, pump stations, tanks) | Ground + 65 psi, capped together at `GW_SHARE` of demand (FCV + check valve) | Assumed. Swept 0.1 / 0.25 / 0.5 |
| Demand | 0.27 gpm per account (≈390 gal/day) | Assumed |
| Elevation | Nearest hydrant's `DEMELEV2018` (m) | City data |
| Roughness | Hazen-Williams C by material | Textbook values |
| Pressure-reducing stations, pump curves, tank levels | Not modeled | Not public |

**Baseline at GW_SHARE 0.25:**
- Median pressure 55 psi; 93% of junctions are within 40–80 psi.
- 3.7% are below 20 psi with no break at all. These sit at the network fringes and are excluded from break counts, which count only junctions newly below 20.

**Known-answer test: Clinton Dr 96″, Feb 2020.** Reported: "Homes, businesses and the Texas Medical Center had low water pressure or no water at all", followed by a citywide boil notice.

| Model state | GW 0.1 | GW 0.25 | GW 0.5 |
|---|---|---|---|
| Isolated (segment closed) | — | 0 customers below 20 psi; 340k drop more than 1 psi | — |
| Gushing, 25% of bore | 284k customers below 20 psi | 254k | 188k |
| Gushing, full bore | 435k | 431k | 423k |

**Verdict:** the model reproduces a citywide pressure collapse from the uncontrolled break, and the result holds across the swept assumptions. It does **not** reproduce that collapse once the break is isolated. So the damage happens while the break gushes, which is the window that broken valves extend.

**Tidwell & Antoine 16″** (reported 2,000; another report says 100+), full-bore rupture: 8–10 customers below 20 psi, ~1,230 drop more than 10 psi. **Not a match** for "without water". Beltway 8 12″ (reported 80), full bore: 0 below 20 psi, 2,052 drop more than 10 psi.

**What can be claimed:** an uncalibrated pressure model that reproduces the 2020 citywide event under every tested assumption. **What can't:** neighborhood-scale pressure predictions.

## 11. Citywide batch (2026-10-11 03:20)

`pipeline/batch.py`: one break per paper segment (its largest-diameter, then longest piece), default assumptions (25% bore, 60 min to first valves, +90 min per dead ring, 6 h repair). 72,171 / 72,171 segments; 1,882 used the full-city solve (≥ 24″).

| Class | Breaks/yr (length share) | Paper c-h/yr | Real c-h/yr | Gushing share of paper |
|---|---|---|---|---|
| Distribution (< 24″) | 10,335 | 1,031,000 | 2,494,514 | 1% |
| Transmission (≥ 24″) | 784 | 12,364,922 | 12,717,278 | 99% |

- Dead-valve cost citywide: 1,815,870 c-h/yr (distribution 1,463,514; transmission 352,356). 25,622 segments have at least one dead first-ring valve; 16,773 distinct dead valves sit in some ring with positive value.
- Repair planner (greedy, `pipeline/repair.py`): top 10 / 100 / 500 / 1,000 / 3,000 recover 12% / 32% / 54% / 64% / 83%.
- Transmission totals are driven by the gushing phase (mean 9,438 customers below 20 psi per break, median 0). They depend on the break-size and response-time assumptions and are not a headline number.
- 569 segments first failed with EPANET errors 203/223: their break node lies on a fragment outside the hydraulic model. Fixed (`4b9b629`): they skip the pressure phase and keep shutoff + downstream counts.
- Superseded: the "top 50 recover 72%" figure from the 2% partial run.
- **Timing bug fixed (04:20, found in the browser check).** The engine shortened the real isolated phase to `t_repair − t_dead`, so a dead valve *saved* repair time: 2,784 rows (3.9%) had real < paper customer-hours. Repair starts only once the break is isolated, so the isolated phase now lasts `t_repair` in both scenarios. Batch rows written before the fix are corrected exactly in `repair.py:fix_timing` (customer counts are integers, so the isolated count is recoverable from the totals); 40/40 sampled rows match a fresh engine run, and 0 rows now have real < paper. Numbers above are post-fix; pre-fix values were distribution real 2,022,717, dead-valve cost 1,318,533.

## 12. Are valve repairs after March 2023 published anywhere? (2026-10-11 04:00)

Swept every service on both City GIS servers (`geogimsms`, `geohwp`): 186 services, 1,394 layers, filtered by name for valve/water/hydrant/main/work/repair/asset/CIP/SAM/model.

| Source | What it holds | Newer than the valve snapshot? | Valve repairs? |
|---|---|---|---|
| `HPC/UtilityAnalysis_gx/39` (used) | 166,362 valves, 21,574 INOP | No: DATEMODIFIED max 2023-06-05, CONDITIONDATE max 2023-03-02 | — |
| `HW/OutsideWater_gx/25` | Identical copy: same count, same INOP count, same max dates | No | No |
| `EMC/WaterBreak_Dashboard` layers 0–6 | 311 cases: 3,495 water-break calls (2021-09 → 2024-06-20), 2,402 leaks, 293 hydrant, **117 "Water Main Valve"** (2023-04 → 2024-06), status incl. "Service Completed" | Yes, to 2024-06-20, then frozen | Complaints/service requests, not condition updates. Upper bound: 117 cases vs 17,413 INOP on mains (0.7%) |
| `04_BaseData_Operations/CIP/0` | 1,996 capital projects, MOD_DATE to 2026-05-31; 277 mention valves, almost all large-diameter (16–84″) | Yes | Capital replacements of big valves. 108 INOP main valves lie within 50 m of a CIP valve project (219 within 100 m); 34 of the 963 INOP valves ≥ 16″ within 50 m. Many of these projects predate 2023 |
| Sewer layers (`Sewer_Network/0,6`, `OutsideWastewater_gx/15,16`) | Wastewater valves | — | Not water |

**Not public / not searched:** work orders (`311_ARCHIVED_CASES` stopped), HPW valve-exercising program records, City Council agenda items for valve contracts, Texas Public Information Act request (days, not hours).

**Conclusion:** no public source records valve condition after March 2023. Bounds from what is public: ≤ 117 311 valve cases (0.7%) and ~108 INOP valves near capital valve projects (0.6%) could have been repaired. The 17,413 figure stands as "City records, June 2023 snapshot". Unknown-condition valves (96,732, treated as working) push the other way.

**New validation lead:** `WaterBreak_Dashboard/0` has 3,495 geolocated water-break 311 calls (2021-09 → 2024-06) with created/closed dates. It could test the length-weighted break distribution by main class. Do not export the `INCIDENT_ADDRESS`/`TITLE` fields (street addresses).

## 13. Gushing metric changed: pressure drop, not "newly below 20 psi" (2026-10-11 05:00)

Found in the browser: a 54″ break (piece 10256, −95.429, 29.811) lit up low pressure only 11–23 km west of the break. Diagnosis (full solve, 25% bore): pressure near the break fell 51 → 33 psi (never below 20), while a west-Houston zone whose *baseline* is only 33–38 psi crossed 20 psi after a ~18 psi citywide drop. The "newly below 20 psi" metric therefore marked the weakest-baseline zone, not the break's footprint. Baseline: 4.1% of junctions are below the TCEQ 35 psi normal minimum, probably because booster pumps are not modelled (fix in progress as option B).

Change: `server/engine.py` counts a junction as affected while gushing when its pressure falls ≥ `DROP_PSI` = 15 psi below its own baseline. Result, real scenario, gushing phase:

| Break | Customers affected | Distance from break p10 / p50 / p90 (km) |
|---|---|---|
| 54″ piece 10256 | 268,079 | 4.1 / 11.5 / 21.0 (was 11.3 / 12.7 / 23.3, none within 10 km) |
| 60″ piece 2353 | 100,872 | 3.1 / 8.1 / 19.2 |
| 84″ piece 81556 | 446,406 | 4.7 / 11.9 / 21.2 |
| 8″ piece 85470 | 0 | — |

Open issue: transmission footprints are very large (a 25% bore 54″ break drains ~107 MGD, about half of modelled demand). The 15 psi threshold is an assumption, not a standard.

## 14. Hydraulic model B: baseline fixed (2026-10-11 05:40, now the live model)

Cause of the weak baseline: mostly **Kingwood**, not west Houston. Kingwood connects to the rest of the network through ~10 pipes (largest 20″), has ~6,600 gpm of demand, and its 31 sources were each capped at the uniform 159 gpm, so it was starved (10k of the 11k junctions below 35 psi; all of those below 20). West elevations are sane (median 23 m vs 12 m east), so source heads were left alone.

Change (`pipeline/hydraulic.py`, new flags; defaults byte-identical):
- `--alloc=N`: the secondary-source total stays at GW_SHARE × demand (0.25), but is re-dispatched each round from sources running under their cap to capped sources, in proportion to the demand-weighted shortfall below 35 psi in each source's service area (network-nearest source). Converged in 5 rounds.
- `--headroom=1.5`: each source can deliver 1.5× its dispatched flow during a break (TCEQ: pumps must meet peak hour with the largest pump out). Baseline draw from these sources is 32.6% of demand.
- Build: `uv run --project pipeline python pipeline/hydraulic.py --gw=0.25 --alloc=10 --headroom=1.5 --out=data/build/hydraulic_b`, then copied into `data/build/` (model A kept in `data/build/hydraulic_a/`).

| Check | Model A | Model B (live) |
|---|---|---|
| Baseline p5/25/50/75 (psi) | 37.7/47.5/55.2/61.5 | 44.3/51.4/58.4/63.7 |
| Junctions < 20 / 35 / 40 psi | 3.7% / 4.1% / 6.9% | 0% / 0.04% / 0.86% |
| Clinton Dr 96″ gushing, newly < 20 psi, 25% / full bore | 253,918 / 431,098 | 202,118 / 424,755 |
| Clinton Dr isolated: < 20 psi / drop > 1 psi | 0 / 340k | 0 / 10.5k |
| 54″ piece 10256, 25% bore: customers losing ≥ 15 psi | 267,786 | 174,792 (p10/50/90 distance 3.4/10.0/20.0 km) |
| Window vs full, median / worst (psi) | 0.5 / 3.9 (29 breaks) | 0.42 / 40.9 (49 breaks; worst all in Kingwood) |

- Remaining < 35 psi junctions (~120) sit on the highest ground in NW Houston (−95.57, 29.88; 31–35 m).
- Kingwood window failure: a 25% bore 12″ leak (~4,700 gpm) exceeds the area's spare capped supply (~3,300 gpm); a window pinned at baseline head implies unlimited supply. **Fix: breaks inside (−95.30, 29.98)–(−95.10, 30.15) always use the full solve** (`EXACT_BOXES` in `server/engine.py`, ~9 s per click).
- Clinton Dr still reproduces a citywide loss while gushing; the isolated state is now far less stiff (10.5k vs 340k customers dropping > 1 psi).
- Assumptions added: 35 psi dispatch target, 16 gpm minimum per source, 1.5 headroom, caps fixed during a break.

**Batch provenance after B.** Transmission mains (≥ 24″, 1,882 segments) are re-run on model B with the 15 psi metric (`data/build/batch_b_trans.jsonl`; `repair.py` merges it). Distribution rows keep the earlier run (model A, old metric, timing-corrected). Sensitivity, from 33,500 distribution segments re-run on model A with the new metric (`batch_a.jsonl`): paper customer-hours +4.7%, real +4.1%, real/paper ratio 2.855 → 2.839. The headline ratio is insensitive to the pressure metric; absolute distribution customer-hours may be ~4–5% low.
