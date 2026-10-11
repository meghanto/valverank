# Shutoff

**When a Houston water main breaks, how many homes really lose water?**

Crews isolate a break by closing the nearest valves. The City of Houston's own GIS records mark **17,501 valves on water mains as inoperable** (seized, buried, or "cannot locate"). When a valve won't close, crews have to go to the next ring of valves, and the outage spreads.

Shutoff runs this on Houston's real water network (290,959 pipe segments, 166,362 valves, 62,540 hydrants, 544,011 customer accounts). Click any main to break it. You see the outage if every valve worked, then the outage given the City's recorded valve status.

| Citywide result (model) | Every valve works | City-recorded valve status |
|---|---|---|
| Customers out, average break (length-weighted) | 11.9 | **25.1** |
| Fire hydrants out, average break | 1.4 | **2.8** |
| Largest single isolation segment | 329 customers | **1,896 customers** |

78% of valves on mains were last inspected five or more years ago (industry guidance: exercise every valve within five years).

## How it works

1. **Ingest** (`pipeline/ingest.py`) downloads public City of Houston ArcGIS layers: water mains (UtilityAnalysis_gx layer 51), system valves (39), hydrants (46), and customer accounts (Customer_Operation_gx layer 1).
2. **Network** (`pipeline/network.py`)
   - Pipe endpoints form junction nodes.
   - Valves within 1 m of a main become cut points; valves farther away are on laterals or hydrant leads and are ignored.
   - Pipes are split at interior valves.
   - Union-find builds **isolation segments** (Walski): the smallest areas that can be shut off by closing valves.
   - This runs twice:
     - **paper**: every valve closes.
     - **real**: valves with `CONDITION = 'INOP'` can't close, so the segments on either side merge.
   - Customers and hydrants are snapped to the nearest main.
3. **Export** (`pipeline/export.py`) writes the demo area (NW and central Houston) as GeoJSON, plus citywide statistics.
4. **Web** (`web/`): React + MapLibre. Clicking a pipe looks up its paper and real segments and animates the difference.

```bash
uv run --project pipeline python pipeline/ingest.py    # ~2 min, ~220 MB to data/raw
uv run --project pipeline python pipeline/network.py   # ~90 s
uv run --project pipeline python pipeline/export.py    # writes web/public/data
cd web && npm install && npm run dev
```

## Limitations (read before quoting numbers)

- **Data snapshot.** The City's public water GIS was last edited 2023-06-05, and valve condition records end in March 2023. Pipe networks change slowly (about 0.3% of lines replaced per year). Inoperable flags are a floor: dead valves don't fix themselves.
- **Connectivity-only model.** There's no hydraulics. An isolation segment is where water *can* be shut off, not a pressure simulation.
- **Customers are utility accounts, not people.** An apartment complex can be a single account.
- **Not validated against real outages yet.** A comparison against news-reported Houston main breaks is in progress (`validation/`).

## AI tools used

Disclosed per CodeRED rules:

- **Claude Code (Anthropic Claude Opus 5.5):** research, data pipeline, and frontend code.
- **ChatGPT:** early ideation, before the hacking window.
