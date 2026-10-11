# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

Pre-code. Hackathon entry for CodeRED: Orion. Nothing built yet; idea not chosen. Three candidate proposals are in `proposals/` (GreaseTrace, CrossingClear, Shutoff); each lists verified data endpoints, a demo script and a build plan. `background.md` holds earlier ChatGPT research.

When code is added, replace this section with real build/lint/test commands. Do not assume a stack until one is chosen.

## Event facts (verified 2026-10-10 from Devpost, orion.uhcode.red, MLH)

- Hacking: **Sat 2026-10-10 1:00 PM CDT → Sun 2026-10-11 1:00 PM CDT** (Devpost deadline). Judging 1:30–3:30 PM Sun, in person, Houston Room, Student Center South. Closing 5:00 PM.
- Teams ≤ 4. College students only. 61 Devpost registrants at hour 1 (site expects 400+).
- **Submit: hosted website + public repo.** Hardware is shown via live demo.
- **Judging criteria (Orion Devpost):** Originality, Relevance to Track, Impact, Demo (smooth in-person demo, team shows deep understanding), Technical Implementation (well-tested, complete, bug-free).
- Cash/house prizes:

| Prize | Award | Track text emphasis |
|---|---|---|
| Best Overall | $1,000 | Any track. "Most ambition… huge impact and reach", most concrete, complete, stable implementation |
| Best Pitch/Demo | $500 | Business case: target market/users, improvement over existing alternatives, path beyond the hackathon |
| Best Environment Hack | $500 | Climate, conservation, pollution, resource use, biodiversity, local ecosystems/communities |
| Best Hardware | 43" 4K TVs | — |
| Most Immersive | 27" 1440p monitors | — |

- MLH sponsor prizes (swag): ElevenLabs, Gemini API, Tiger Data, Solana (Ledger wallets), Backboard, Vultr, GoDaddy domain, DEV Writing Challenge ($100).
- Sponsors: Reynolds and Reynolds, Chevron, RSM, Red Bull, Pure Buttons, daily.dev, Lovable, Katz Coffee, MLH. Judges come from sponsor companies. Do not frame projects as attacks on oil and gas.
- Rules file (github.com/UHCodeRED/rules) is the 2025 Astra version; Devpost criteria above supersede its criteria. Still assumed in force: all work inside the window, list every AI tool used, repo stays public, bug fixes only after the deadline.
- Calibration from 2025 Astra: 53 projects; most winners were LLM-wrapper apps. A complete, polished, technically real project clears the bar.

## Verified Houston data sources (2026-10-10)

- Water mains, public ArcGIS REST, no auth: `https://geogimsms.houstontx.gov/arcgis/rest/services/HPC/UtilityAnalysis_gx/MapServer/51` (290,959 polylines; MATERIAL, DIAMETER, INSERVICEDATE, CONDITION, REHAB*, REPLACEMENTYR). 2000 records/page, pagination supported. Same service: valves (38, 39), hydrants (46), pressure reducing stations (48), abandoned pipe (36); wastewater layers 0–26.
- **The whole `UtilityAnalysis_gx` service (water mains, valves, hydrants) is a June 2023 snapshot.** Last edit 2023-06-05; no valve condition records after 2023-03. Sewer SSO data is current to 2026-04-30.
- Valve modelling gotcha: `TURNSTOOPEN` is populated only when crews operate a valve, so it leaks the INOP label (inflates AUC to 0.79; leak-free is ~0.58). In-line valves (VALVE_USE INL / IN LINE / IN LINE - SLF): 79,247, of which 28% of inspected are INOP.
- System valves (layer 39): 166,362 records. CONDITION: INOP 21,574, GOOD 47,451, null 96,732. REASON_INOPERABLE: CANNOT_LOCATE 15,781, plus covered over, misaligned, spins free, etc. Also VALVE_USE, NORMALPOSITION, TURNSTOOPEN, DIAMETER. Sample test (Rice Village bbox): pipe endpoints share exact coordinates (network is noded); 57% of valves lie exactly on a pipe and 60% within 2 m (the sample was capped at 2,000 pipes, so these figures are understated).
- Houston Train Watch (live, no key): `services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Train_Watch_Layer/FeatureServer/0/query`. 56 crossings; crossingStatus, timeToClear, predictedStart, sensorStatus.
- NOAA AIS ship positions: `coast.noaa.gov/htdata/CMSP/AISDataHandler/2024/AIS_2024_MM_DD.zip` (~345 MB/day, nationwide, HTTP 200).
- Sewer overflows: `geohwp.houstontx.gov/arcgis/rest/services/04_BaseData_Operations/SSO_Stoppages_Odor/FeatureServer/5`, 66,385 records 2000–2026. Fields: CAUSE, TOT_VOL_L, GPM, DURATION, WATERSHED, US_GMUFID/DS_GMUFID (pipe IDs upstream and downstream; snap to graph), census block GEOIDs, PARCEL_ID. Layer 1: stoppages (235k). Layer 6: repeat SSOs.
- Sewer mains: `01_BaseData_Infrastructure/Sewer_Network/FeatureServer/11` (143k; upstream/downstream manholes, slope, diameter, material). `Consent_Decree/GravityMains_PACPScoring/FeatureServer/0` (146k condition scores). geohwp layers are in EPSG:2278; request `outSR=4326`.
- Customer accounts (count affected customers): `geogimsms.../CAS/Customer_Operation_gx/MapServer/1`, 544k points.
- HFD fire stations: `HFD_94_FIRE_STATIONS` in the services.arcgis.com/NummVBqZSIJKUeVR org.
- FRA blocked-crossing reports (open JSON, no key): `https://www.fra.dot.gov/blockedcrossings/api/incidents?state=TX&city=Houston&pageSize=500&page=N`, 24,457 Houston reports. FRA crossing inventory: Socrata `data.transportation.gov/resource/m2f8-22s6.json`.
- Restaurants: OSM Overpass at `overpass-api.de` works (709 in the central Houston bbox). The kumi and private.coffee mirrors failed.
- 311 data that IS public (city org `services.arcgis.com/NummVBqZSIJKUeVR`): `SanitarySewer_ServiceRequest_2009_2019` (244k sewer requests), `311_water2019` (11k water requests from Winter Storm Uri, Feb 2021), `SWM_311_90_Days_view_layer` (38.7k solid-waste cases, last 90 days, live), `SWM_FY26_311Cases`. On geohwp: `SSO_Stoppages_Odor/8` (33k odor complaints to 2026) and `/1` (235k stoppage work orders to 2026).
- Not public: current water-leak 311 cases (`311_ARCHIVED_CASES` service is stopped; the last-90-days layer covers meter cases only), work orders, water pressure/SCADA.
- TWDB statewide water-loss audit Excel (updated 2026-02-28): twdb.texas.gov/conservation/data/water-loss-dashboard.asp.

## `background.md`

ChatGPT conversation export. The user says its project ideas are **suggestions only, not decisions**.

- Lines ~750–1376 duplicate lines ~100–750. Skip them.
- Ignore the export markup (`<box>`, `<Cite>`, `{#each}`).
- Useful parts: the list of crowded categories (food rescue, generic disaster maps, AI accessibility assistants, AI sustainability dashboards, chatbots, portfolio risk dashboards) and the build principles below.

## Build principles

- Every displayed number comes from one deterministic computation path. No LLM-generated results.
- Seeded data generators for reproducible demos. Cache external data locally so the demo works offline.
- Judge-operable demo: the judge triggers the problem, applies the fix, and sees the measured result.
- Add sponsor integrations only after the core works, and only where they serve the product.
- Feature freeze around Sun 9:00 AM. Deploy early. The hosted URL is a submission requirement.
