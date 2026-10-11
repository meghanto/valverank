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
