# ValveRank

**Find the right valves to fix in Houston's water network.**

**When a Houston water main breaks, how many homes really lose water?**

Crews isolate a break by closing the nearest valves. The City of Houston's own GIS records mark **17,413 valves on water mains as inoperable** (seized, buried, or "cannot locate"). When a valve won't close, crews have to go to the next ring of valves, and the outage spreads.

ValveRank runs this on Houston's real water network (290,959 pipe segments, 166,362 valves, 62,540 hydrants, 544,011 customer accounts). Click any main to break it. You see the outage if every valve worked, then the outage given the City's recorded valve status.

| Citywide result (model) | Every valve works | City-recorded valve status |
|---|---|---|
| Customers out, average break (length-weighted) | 16.3 | **38.6** |
| … of which cut off downstream (no remaining path to a plant, pump station or tank) | 3.2 | 7.9 |
| Fire hydrants out, average break | 1.6 | **3.5** |
| Largest single outage | 1,683 customers | **2,496 customers** |

**Customer-hours without water per year** (one simulated break per isolation segment, all 72,171 segments, on the full pressure model; 11,119 breaks/yr spread by pipe length × a break rate per pipe size estimated from 3,495 real 311 calls):

| | Every valve works | City-recorded valve status |
|---|---|---|
| Shut-off time, neighborhood mains (< 24″) | 1.07 M | **2.57 M (×2.4)** |
| Citywide dead-valve cost | — | **4.26 M** = 1.55 M longer shut-offs (City records + connectivity) + 2.71 M longer gushing (pressure model) |
| Repair the planner's top 10 / 100 / 500 dead valves | | recovers 17% / 41% / 72% of that cost |

Gushing time that no valve repair changes (customers losing ≥ 15 psi while a break flows) is reported separately: it comes from the uncalibrated pressure model and the assumed break size and response time. Break rate by pipe size: small mains break ~1.65× more often per km than average, 42″+ mains ~0.55× (311 data blended with length, `pipeline/break_rates.py`).

78% of valves on mains were last inspected five or more years ago (industry guidance: exercise every valve within five years).

## How it works

1. **Ingest** (`pipeline/ingest.py`) downloads public City of Houston ArcGIS layers: water mains (UtilityAnalysis_gx layer 51), system valves (39), hydrants (46), and customer accounts (Customer_Operation_gx layer 1).
2. **Network** (`pipeline/network.py`)
   - Pipe endpoints form junction nodes.
   - Valves within 1 m of a main (3 m if the City labels them in-line) become cut points. Hydrant and service valves are excluded: they isolate a lead, not the main.
   - Abandoned, proposed and non-potable mains are dropped. Unnoded tees (a dead end within 1 m of another pipe) are joined.
   - Pipes are split at interior valves.
   - Union-find builds **isolation segments** (Walski): the smallest areas that can be shut off by closing valves.
   - This runs twice:
     - **paper**: every valve closes.
     - **real**: valves with `CONDITION = 'INOP'` can't close, so the segments on either side merge.
   - Customers and hydrants are snapped to the nearest main.
3. **Supply loss** (`pipeline/supply.py`): closing a segment can also cut off segments whose only path to a water source runs through it. Sources are the City's 218 in-service plants, pump stations and storage tanks (layer 44). One articulation-point pass over the segment graph gives every segment's downstream loss; `pipeline/test_supply.py` checks it against brute force.
4. **Pressure** (`pipeline/hydraulic.py`): an EPANET 2.2 model of the whole network (3 surface-water plants as fixed heads, 218 capped secondary sources, pressure-driven demand, elevation from hydrant records). The break is an emitter sized from the pipe bore. See `validation/data_audit.md` §10.
5. **Timeline** (`server/engine.py`): gushing → still gushing because a first-ring valve is dead → isolated until repair. Each phase counts customers (pressure drops ≥ 15 psi below baseline while gushing; segment + downstream when isolated) and sums customer-hours. Small mains solve a 4 km window pinned to baseline heads (~200 ms, median error 0.5 psi vs the full solve, `pipeline/window.py`); mains ≥ 24″ solve the full city.
6. **Repaired scenario** (`pipeline/fixed.py`): the City's records after repairing the planner's top 100 dead valves, re-segmented and re-run for supply loss. Every break shows it as a third timeline; the overview links to breaks where it matters (`web/public/data/showcase.json`).
7. **Batch + repair planner** (`pipeline/batch.py`, `pipeline/repair.py`): one break per isolation segment citywide, then a greedy pick of the dead valves whose repair recovers the most customer-hours.
8. **Export** (`pipeline/export.py`): citywide vector tiles (PMTiles), segment tables and statistics.
9. **Web** (`web/`, React + MapLibre) and **API** (`server/app.py`, FastAPI): click any pipe to break it, see paper vs real outage, the timeline with assumption sliders, and the repair planner.

```bash
uv run --project pipeline python pipeline/ingest.py    # ~2 min, ~220 MB to data/raw
uv run --project pipeline python pipeline/network.py   # ~90 s
uv run --project pipeline python pipeline/export.py    # writes web/public/data
cd web && npm install && npm run dev
```

## Machine-checked guarantees (Bend 2)

`proofs/` states 13 laws about the model's specification and proves them in [Bend 2](https://bend-lang.com). The checker and its Lean-backed `--verdict` mode both accept them, with no assumed axioms:
- **A dead valve can never shrink an outage.** For any network, valves and customer weights, the paper segment is contained in the real one, so real customers ≥ paper customers (`customers_mono`).
- **Supply loss is sound.** Removing a segment never creates a path to a water source (`supply_mono`).

What is *not* proved: the Python implementation itself, union-find ≡ closure, Tarjan's algorithm, and geometry/snapping. Those are covered by tests (`pipeline/test_supply.py`, brute force) instead. See `proofs/README.md`.

```bash
cd proofs && bend PROOF.bend --verdict   # ALL PROOFS CHECK
```

## Limitations (read before quoting numbers)

- **Data snapshot.** The City's public water GIS was last edited 2023-06-05, and valve condition records end in March 2023. Pipe networks change slowly (about 0.3% of lines replaced per year). Inoperable flags are a floor: dead valves don't fix themselves.
- **Pressure model is uncalibrated.** Plant pressures, demand, break size and response times are assumptions (sliders in the app). It reproduces the 2020 Clinton Dr citywide pressure loss but not neighborhood-scale reports.
- **Customers are utility accounts, not people.** An apartment complex can be a single account.
- **Few real outages to validate against.** Only 2 news-reported breaks give comparable customer counts (`validation/model_vs_news.md`); the model is low on both.
- **Break frequency** is spread by pipe length. Real break rates vary with diameter, material and age; the 11,119/yr HPW figure likely includes leak repairs.
- **569 segments** (0.8%) sit on fragments outside the pressure model; they get shutoff and downstream counts but no pressure phase.
- **Data audit:** provenance, cross-checks against Houston Public Works published totals, and known defects are in `validation/data_audit.md`.

## AI tools used

Disclosed per CodeRED rules:

- **Claude Code (Anthropic Claude Opus 5.5):** research, data pipeline, and frontend code.
- **ChatGPT:** early ideation, before the hacking window.
