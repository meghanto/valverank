# Data audit: 311 Uri requests and critical facilities

Run: Sat 2026-10-10, 22:40–23:10 CDT. Covers the two items marked **MISSING** in `data_audit.md` §1 (#7, #8). How to reproduce:
- `pipeline/ingest_extra.py`: downloads both datasets to `data/raw/`, layer metadata to `data/raw/meta/`, appends `data/MANIFEST.json`
- `pipeline/audit_extra.py`: every number below (seed 7, ~20 s). The date calibration queries a live City layer; everything else reads `data/raw`.

Verdict scale (same as `data_audit.md`, plus one):
- **OK**: fit for the claim
- **CAVEAT**: usable if the caveat is stated
- **DEFECT**: our use of the data is wrong; fix it before quoting numbers
- **UNUSABLE**: can't be used for the intended purpose

---

## 1. Summary

| Dataset | Local file | Records (server = local) | Verdict | One line |
|---|---|---|---|---|
| Winter Storm Uri 311 water requests | `uri311.json` | 11,041 | **CAVEAT** as data. **Null result** as a check of the INOP flags | Real Uri data (Feb 13–25 2021, inferred). "Water Main Valve" requests sit no closer to INOP valves than other water requests do |
| `HPC/CriticalFacilities` (5 layers) | `facilities_adult_care.json`, `facilities_correctional.json` | 447, 15 | **UNUSABLE for the public site** (license). CAVEAT for internal use | Licensed Data Axle data: "not to be distributed outside H-GAC". No hospitals, schools, dialysis or fire stations in it |
| City open-data alternatives | `facilities_{hospitals,trauma,schools,fire_stations,nursing,assisted_living,icf}.json` | 108, 56, 1,541, 94, 71, 191, 30 | CAVEAT (stale; many outside City water service) | Best available. Dialysis: no Houston layer exists in the City org |

---

## 2. Winter Storm Uri 311 water requests

### 2.1 Provenance

| Item | Value |
|---|---|
| URL | `services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/311_water2019/FeatureServer/0` |
| Layer name | `311_water_final_2` |
| AGOL item | title **"311_water2021"**, snippet "311_water2021 freeze event", tag "311 data 2021". Owner `HCDInspectionAdmin` (Housing & Community Development, not Public Works). Created 2021-03-02, modified 2022-05-25 |
| Description / license | None |
| Last edit (`editingInfo`) | 2022-05-25 |
| Native SR | EPSG:2278. Downloaded with `outSR=4326` |
| Count on server / local | 11,041 / 11,041 |
| Duplicate copy | `311_water_final_1` in the same org: same 11,041 records, last edit 2021-03-05 |
| **Date field** | **None.** The layer has no request date, so the date range is inferred (§2.2) |

- **The "2019" in the service name is wrong.** The item title, snippet and tag all say 2021, and the case numbers (§2.2) put every dated record in Feb 2021. The `yr` field ("2020", 10,444 rows) is the appraisal year of the joined HCAD parcel record, not the request year.
- **What we downloaded.** The publisher joined each request to its HCAD parcel, so the layer also carries owner names, owner mailing addresses and appraisal values. **We don't download those.** `uri311.json` keeps only the case number, category, geocode status, council district, neighbourhood, ZIP, parcel class, low/moderate-income flags and the point. The service-request address field (`SERVICE_RE`) is also dropped.

### 2.2 Date range (inferred)

`CASE_NUMBE` = `<8-digit HPW service-request id>-<12-digit 311 case number>`. The HPW id is the same sequence as `REQUEST_ID` in the City's odor-complaint layer (`geohwp …/SSO_Stoppages_Odor/FeatureServer/8`), which has dates. Calibration: 195 odor requests from 2021-01-15 to 2021-03-20, interpolated (monotone).

| | Value |
|---|---|
| Records with an 8-digit HPW id | 10,876. The other 165 (158 of them "Water Meter") have a 6-digit id from a different sequence; no date for those |
| HPW id range | 20110177 – 20122258 |
| Estimated first / median / last request | **2021-02-13 21:07 CST / 2021-02-19 / 2021-02-25 22:55 CST** (1st–99th percentile: Feb 14 – Feb 25) |
| Peak | Thu Feb 18: 2,390 requests (Feb 17: 1,336; Feb 19: 1,267). Little before Feb 15 |
| 311 case-number span | 28,917 numbers. This layer holds 11,041, so it is a subset (water categories) of all 311 cases in the window |

**Verdict: OK.** The data covers Winter Storm Uri and its aftermath (Feb 14–25 2021), as CLAUDE.md says. The dates are estimated to within hours, not read from a field. Don't claim per-request timestamps.

### 2.3 Field completeness and categories

| Field | Complete | Notes |
|---|---|---|
| `Issue` (category) | 11,041 / 11,041 | 6 values, below |
| Geometry | 10,798 (97.8%) | 243 have no point (`Status`=U, unmatched) |
| Geocode status | M 10,541 / T 257 / U 243 | All matched points: `Addr_type`=PointAddress, `Score`=100 |
| `city` (from parcel join) | 10,441 | 600 blank: the 243 unmatched plus 357 matched points with no parcel |
| Date | **0** | See §2.2 |

| Issue | Records | Of which no point |
|---|---|---|
| Water Leak | 3,594 | 130 |
| **Water Main Valve** | **3,429** | 9 |
| Water Service | 3,160 | 66 |
| Water Quality | 483 | 5 |
| Fire Hydrant | 217 | 29 |
| Water Meter | 158 | 4 |

Counts match CLAUDE.md exactly.

### 2.4 Space, duplicates, geocode precision

| Check | Result | Verdict |
|---|---|---|
| Extent | lon −95.731…−95.044, lat 29.539…30.086 | OK |
| Inside Houston bbox (lon −95.9..−95.0, lat 29.5..30.2) | **100%** of points | OK |
| Cities (parcel join) | Houston 10,103; Humble 179; Kingwood 84; Webster 25; Stafford 19; … | OK. Same service area as `customers.json` |
| Duplicate case numbers | 0 | OK |
| Shared coordinates | 9,517 distinct points. 971 points carry >1 request (2,252 requests). Max 13 at one point | CAVEAT. Repeat callers and apartment complexes. The test (§2.5) uses one point per location |
| Same point + same category | 743 extra records | CAVEAT. Probably repeat calls about one problem. Counts of "requests" overstate counts of distinct problems by up to ~7% |
| Placeholder geocodes | 0 within 50 m of City Hall. No ZIP/street centroids: every point is an address point | OK |
| Tied geocodes (`Status`=T) | 257 | CAVEAT. The geocoder had equal candidates. Points may be at the wrong address |
| **What the point means** | The address of the request. For "Water Main Valve" that is the caller's address, **not the valve's location** | CAVEAT. Key limitation for §2.5 |

### 2.5 First-pass test: do "Water Main Valve" requests cluster near INOP valves?

**Question.** If the City's INOP flags are real, crews responding to Uri shutoff requests should have hit inoperable valves more often near "Water Main Valve" (WMV) requests. So WMV requests should sit closer to INOP valves than comparable points do.

**Method** (`audit_extra.py`, section "311 'Water Main Valve' vs INOP valves"):
- Requests deduplicated to one per location: WMV 3,191 (of 3,420 with a point); all other 311 categories 6,630.
- Valves from `valves.json` (166,362). Two sets: **all**; **main** = the 99,403 left after removing hydrant-gate valves (subtype 33) and lead/service uses (data_audit D1).
- Labels: INOP 21,574 (15,927 dated before 2021-02-14, 5,647 after). Known working (GOOD/FAIR/POOR) 48,055. Unknown 96,732.
- Per point: distance to the nearest INOP valve, to the nearest non-INOP valve, and to any valve. Whether the **nearest valve is INOP**. **INOP share among valves within 150 m** (controls for valve density).
- Baselines: (a) **other 311 water requests** (same people, same week, same geocoder: the main control); (b) 20,000 random customer accounts (where people live); (c) 20,000 random valves, each displaced by a random WMV→nearest-valve offset (the spatial distribution of valves).
- Bootstrap 95% CIs (2,000 resamples). Plus a within-cell comparison: WMV vs other requests inside the same 1 km grid cell (826 cells), which controls for neighbourhood-level inspection coverage.

**Results, main valves (the fair test).** Base rate: 18.0% of main valves are INOP.

| Point set | n | Median m to nearest INOP | Median m to nearest non-INOP | Nearest valve is INOP | INOP share within 150 m |
|---|---|---|---|---|---|
| **WMV requests** | 3,191 | 117 | 57 | **18.5%** | **18.6%** |
| Other 311 water requests | 6,630 | 121 | 58 | 18.6% | 18.5% |
| — Water Leak | 3,242 | 116 | 56 | 19.2% | 18.7% |
| — Water Service | 2,831 | 123 | 61 | 18.8% | 18.4% |
| Random customers | 20,000 | 129 | 62 | 17.6% | 18.6% |
| Valve-distribution baseline | 20,000 | 107 | 38 | 18.6% | 18.3% |

| Difference (WMV minus baseline) | Nearest valve is INOP | INOP share within 150 m |
|---|---|---|
| vs other 311 | −0.2 pp [−1.8, +1.5] | +0.2 pp [−0.7, +1.1] |
| vs customers | +0.8 pp [−0.6, +2.3] | +0.1 pp [−0.7, +0.8] |
| vs valve baseline | −0.2 pp [−1.6, +1.4] | +0.4 pp [−0.4, +1.1] |
| vs other 311, within 1 km cells | +0.3 pp [−1.3, +2.1] | — |

**Same test, other cuts:**

| Valves / flag | WMV nearest-is-flag | Other 311 | WMV − other 311 | Within-cell |
|---|---|---|---|---|
| All valves, INOP | 10.2% | 10.9% | −0.8 pp [−2.1, +0.5] | −0.8 pp [−2.2, +0.7] |
| Main, **INOP recorded before Uri** (the only flags that could *predict* requests) | 10.5% | 11.6% | −1.1 pp [−2.4, +0.2] | −0.4 pp [−1.7, +1.0] |
| Main, INOP recorded after Uri | 8.0% | 7.0% | +1.0 pp [−0.1, +2.1] | +0.7 pp [−0.4, +1.9] |

Share of points with a main valve flagged INOP between 2021-02-14 and 2021-12-31 within 100 m: WMV 10.1%, other 311 8.6%, customers 7.8%, valve baseline 8.3%.

**Reading.**
- **Null result for the claim we wanted.** INOP flags recorded before the storm don't predict where "Water Main Valve" requests came from. The point estimate is slightly *negative*, and every CI includes zero. On this test the 311 data does **not** support "INOP flags reflect reality". It doesn't refute it either. The test is weak (see confounders).
- **Weak signal the other way round.** Valves flagged INOP *after* the storm are a little more common near WMV requests (+1.0 pp vs other requests, CI touching zero; +1.4 pp [+0.5, +2.4] vs customers). That fits crews logging valves as INOP while doing Uri shutoffs. If real, it means 311 requests helped **produce** flags, which makes them useless as an *independent* check of those flags.
- The distance profile of WMV requests is the same as Water Leak and Water Service (median 53 m vs 52–57 m to any main valve). Nothing marks WMV points as being "at a valve".
- The displaced-valve baseline lands closer to valves than any real set (median 36 m vs 53 m), so its distances aren't comparable. Its INOP-share columns are still valid.

**Confounders (why a null here is not strong evidence either way):**
1. **The point is the caller's address, not the valve.** A shutoff for a block can use a valve hundreds of metres away. The median distance to any main valve is 53 m, but the isolating valve for a request is not necessarily the nearest one.
2. **"Water Main Valve" may often mean "shut my water off".** During Uri many residents had burst house pipes and needed their supply shut off. The category may record the *action requested*, not a broken valve. WMV looking like Leak and Service fits this. Unverified: there is no request text in the layer, and we have not found the City's category definitions.
3. **Uri is not normal operations.** Frozen pipes, mass shutoffs, crews stretched. A valve that failed then might work in June, and the reverse.
4. **Valve density and inspection coverage.** INOP flags exist only where crews inspected (58% of valves have no condition). Requests come from dense residential areas. The 150 m share and the within-cell comparison control for this partly, not fully.
5. **Timing.** The flags are a June 2023 snapshot with dates 2015–2023. Flags set before Feb 2021 may have been fixed by then. Flags set after may be *caused* by the response (above).
6. **Repeat calls.** Deduplicating by location helps. 257 tied geocodes add position noise.

**Verdict for this use: CAVEAT (data) / NULL RESULT (test).** The dataset is genuine and well geocoded. It does not provide the independent validation of INOP flags that the plan relied on. A stronger test would need the request text, crew work orders, or the actual valves operated (none are public; see CLAUDE.md "Not public").

---

## 3. Critical facilities

### 3.1 `HPC/CriticalFacilities` exists, but it isn't what the plan assumed

`geogimsms.houstontx.gov/arcgis/rest/services/HPC/CriticalFacilities/MapServer`: 5 point layers, no service description, keywords "HPC,HPW". **Every layer** has the same description and copyright:

> "Data Axle data showing confirmed businesses in the H-GAC region. This dataset is a licensed dataset and is not to be distributed outside H-GAC without the written consent of Data Axle." (copyright: Data Axle)

| Layer | Name | Count | Geometry | Fields | Primary SIC values | Downloaded? |
|---|---|---|---|---|---|---|
| 0 | Adult Care Facilities | 447 | Point | 166 (Data Axle business schema) | Residential care homes 267; retirement communities 99; adult day care 51; skilled nursing 13; other 17 | Yes, 19 fields |
| 1 | Correctional Institutions | 15 | Point | 166 | State 7; private 5; county 2; city 1 | Yes, 19 fields |
| 2 | Oil Refineries and Drilling Entities | 186 | Point | 166 | Drilling/boring contractors 138; refiners 25; drilling 23 | No: not water-dependent populations (and sponsor framing) |
| 3 | News Services | 46 | Point | 166 | TV stations 37; news service 9 | No |
| 4 | Power Grid Providers | 14 | Point | 166 | Energy-management firms 8; oil & gas producers 5; gas co. 1. **Not substations** | No |

- **No hospitals, schools, dialysis centres or fire stations** in this service. The plan assumed it held them.
- **The Data Axle schema includes personal fields** (contact first/last name, gender, ethnicity, phone). We download only: id, company, SIC/NAICS, city, ZIP, lat/lon, geocode level, employee size, year established, Data Axle production date, HQ/branch, call status.
- Data Axle production date: **2022-04-05** for all 447.

**Adult care (layer 0)**

| Check | Result | Verdict |
|---|---|---|
| Inside Houston bbox | 406 / 447 | OK (H-GAC region) |
| Geocode level (`MatchLC`) | Parcel centroid 402; site-level 21; **ZIP / ZIP+4 / ZIP+2 centroid 24 (5.4%)** | CAVEAT. 24 points are only ZIP-accurate. Drop them for segment assignment |
| Shared coordinates | 69 records (max 3 per point) | CAVEAT. Multiple businesses at one site |
| Duplicate names | 28 | Chains and branches. Not checked further |
| Main vertex within 120 m | 43%. 239 are >500 m from any City main | Most lie outside City of Houston water service (MUDs, other cities) |
| Overlap with HHSC lists (§3.2) | Only 20% of nursing and 34% of assisted-living facilities have a Data Axle point within 100 m | The two sources describe different populations |

**Verdict: UNUSABLE for anything shipped** (public repo, hosted site, demo screenshots). The City serves it publicly, but the license text forbids distribution outside H-GAC. CAVEAT for local, internal analysis only. **If anyone commits `data/raw/`, these two files must be excluded** (`facilities_adult_care.json`, `facilities_correctional.json`).

### 3.2 Alternatives in the City's ArcGIS Online org

Searched all 2,294 services in `services.arcgis.com/NummVBqZSIJKUeVR`. Best candidate per type:

| Type | Service / layer | Publisher (AGOL owner) | Count | In bbox | Data as of | Main within 120 m | Downloaded | Verdict |
|---|---|---|---|---|---|---|---|---|
| Hospitals | `COH_Hospitals_view/10` | `cohgis_ago`, "City of Houston Open Data". © HITS-GIS | 108 | 104 | View created 2025-06-02, **but the 106 names match the 2021 copy (`COH_HOSPITALS`, 2021-02-19) exactly** | 54% | ✓ | CAVEAT: data ≥ 2021. No bed counts |
| Trauma centres | `COH_Trauma_Centers_view/9` | `cohgis_ago` | 56 | 35 | 2025-06-02 | 39% | ✓ | CAVEAT: regional (lon −96.8…−94.4). 25 blank trauma level |
| Schools | `COH_Schools_view/0` | `cohgis_ago` (TEA data) | 1,541 | 1,397 | Enrollment Oct 2022. `Update_Date` 2023-04-20 for all | 33% (917 >500 m) | ✓ (no principal/superintendent names) | CAVEAT: regional. 144 records share a point (max 10): campuses and programmes geocoded to one site. 32 under construction |
| Fire stations | `COH_Houston_Fire_Stations_view/10` | `cohgis_ago`. © HFD, HITS-GIS | 94 | 94 | `LastUpdate` 2020-04-30 for all | 96% | ✓ | OK. Same 94 as `HFD_94_FIRE_STATIONS` (2015 item) named in CLAUDE.md |
| Nursing facilities | `Nursing_Facilities/0` | `mslentz` (city user) | 71 | 71 | **2020-04-24** | 68% | ✓ | CAVEAT: 6 years old. `COH_Servic` FULL 51 / LIMITED 20 (undocumented; looks like City water service) |
| Assisted living | `Assisted_Living_Facilities/0` | `mslentz` | 191 | 191 | 2020-04-25 | 83% | ✓ | CAVEAT: same. FULL 163 / LIMITED 28 |
| Intermediate care (ICF/IID) | `Intermediate_Care_Facilities/0` | `mslentz` | 30 | 30 | 2020-04-25 | 100% | ✓ | CAVEAT: same |
| Dialysis | `DialysisCenter_SZ/0` | `e132794_MyCity` | 379 | **0** | 2022-01-24 | — | ✗ | **UNUSABLE.** Every record is in **Georgia** (Atlanta 33, Decatur 16, …). The snippet says so. **No Houston dialysis layer exists in the City org** |
| Warming centres | `HHD_operated_warming_centers/7` | `HHDGIS` | 5 | — | Jan 2025 | — | ✗ | Too small |
| Daycares | `Daycares_in_Houston/0` | `HCDInspectionAdmin` | 897 | — | 2021-04-04 | — | ✗ | Not fetched. Exists if needed |

Also present, not fetched: `HFD_Hospital`, `HOSPITALS_new` (108, 2024; same list), `Hospital_Based_Nursing_Facilities` (2), `HCPH_Health_Clinics`, `HHD_Health_Centers`, `COHGIS_SCHOOLS_JAN_2021` (1,473), `Evacuation_Shelters`, `Urgent_Care_Facilities`.

- **No layer has a capacity number** we could use to weight impact (beds, residents), except school enrollment (Oct 2022).
- **"Main within 120 m"** uses main vertices, not segments, so it slightly overstates distance. The pattern is clear anyway: the regional layers (schools, trauma, Data Axle) are mostly outside City water service. The HHSC lists and fire stations sit inside it. **Filter every facility layer to points that snap to a City main before counting "facilities affected".**
- Identical-coordinate checks: no layer except schools and adult care has more than 6 records on shared coordinates. Only the Data Axle layer reports its geocode level; the City layers don't, so centroid geocodes in them can't be ruled out.

---

## 4. What this changes in `data_audit.md`

| `data_audit.md` item | Was | Now |
|---|---|---|
| #7 Critical facilities | MISSING | **Have, CAVEAT.** `HPC/CriticalFacilities` is licensed Data Axle data: internal only, never shipped. Use the City open-data views plus the 2020 HHSC lists. No dialysis source |
| #8 311 Uri requests | MISSING | **Have.** Real Uri data, Feb 13–25 2021 (dates inferred from case numbers). **The INOP check comes out null** |
| §6 "INOP flags reflect reality" | Unsupported (data missing) | **Still unsupported.** Tested and not confirmed. Don't claim 311 validates INOP flags |

## 5. Contradictions with CLAUDE.md

- `311_water2019`: CLAUDE.md is right that it is Feb 2021 Uri data. But the layer **has no date field**; the range is inferred. The publisher is Housing & Community Development, not HPW.
- `HPC/CriticalFacilities` is listed in the plan as the care-home/school source. It holds **no schools, hospitals or fire stations**, and it is **licensed, no redistribution**.
- Valve `CONDITION` has more values than INOP/GOOD/null: FAIR 496, POOR 108, CNL 1. The test treats them as "known working".
- `HFD_94_FIRE_STATIONS` (2015) is superseded by `COH_Houston_Fire_Stations_view` (same 94 stations, last updated 2020-04-30).
