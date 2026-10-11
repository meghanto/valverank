"""Real break history: City 311 water-break calls (Sept 2021 - June 2024) into Tiger Data.

Source: geogimsms EMC/WaterBreak_Dashboard/FeatureServer layers 1-6 (one per call type; layer 0 is
their union). Only geometry, dates and status are requested: the TITLE / INCIDENT_ADDRESS fields hold
street addresses and are never downloaded. Each call is snapped to the nearest water main (<= 150 m)
for pipe diameter and material, then the point itself is dropped.

Tiger Data (TIGER_DATABASE_URL):
  break_calls(opened, closed, type, status, piece, diameter, material, snap_m)  hypertable on opened
  break_calls_weekly  continuous aggregate: time_bucket('7 days'), type, size class -> calls, mean hours to close

  uv run --project pipeline python pipeline/break_calls.py
"""
import datetime as dt
import json
import os
import pickle
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
URL = "https://geogimsms.houstontx.gov/arcgis/rest/services/EMC/WaterBreak_Dashboard/FeatureServer"
TYPES = {1: "Fire Hydrant", 2: "Water Leak", 3: "Water Main Valve", 4: "Water Meter", 5: "Water Quality", 6: "Water Service"}
RAW = ROOT / "data" / "raw" / "break_calls.json"
SNAP_M = 150.0


def fetch(layer):
    """This service rejects resultOffset paging and caps at 2000: fetch object ids, then query by id batches."""
    get = lambda q: json.load(urllib.request.urlopen(urllib.request.Request(
        f"{URL}/{layer}/query", data=urllib.parse.urlencode(q | {"f": "json"}).encode()), timeout=120))
    ids = get({"where": "1=1", "returnIdsOnly": "true"}).get("objectIds") or []
    out = []
    for i in range(0, len(ids), 500):
        out += get({"objectIds": ",".join(map(str, ids[i:i + 500])), "outFields": "STATUS,CREATED_DATE,CLOSED_DATE",
                    "returnGeometry": "true", "outSR": 4326})["features"]
    return out


def size_class(d):
    return "transmission (24 in+)" if d >= 24 else "distribution (< 24 in)"


def main():
    if not RAW.exists():
        rows = []
        for layer, typ in TYPES.items():
            for f in fetch(layer):
                a, g = f["attributes"], f.get("geometry")
                if g and a.get("CREATED_DATE"):
                    rows.append([typ, a.get("STATUS"), a["CREATED_DATE"], a.get("CLOSED_DATE"), g["x"], g["y"]])
        RAW.write_text(json.dumps(rows))
    rows = json.loads(RAW.read_text())
    print(f"{len(rows)} calls")

    N = pickle.load(open(ROOT / "data/build/network.pkl", "rb"))
    kx, ky = 111_320 * np.cos(np.radians(29.76)), 110_574
    xy = lambda lon, lat: np.column_stack([(np.asarray(lon) + 95.4) * kx, (np.asarray(lat) - 29.76) * ky])
    samp, owner = [], []
    for k, p in enumerate(N["pieces"]):
        m = xy(*np.asarray(p[3]).T)
        for s in range(len(m) - 1):
            n = max(1, int(np.hypot(*(m[s + 1] - m[s])) // 10.0))
            for t in np.linspace(0, 1, n + 1):
                samp.append(m[s] + t * (m[s + 1] - m[s])); owner.append(k)
    d, j = cKDTree(np.asarray(samp)).query(xy([r[4] for r in rows], [r[5] for r in rows]))
    owner = np.asarray(owner)

    ts = lambda ms: dt.datetime.fromtimestamp(ms / 1000, dt.UTC) if ms else None
    recs = []
    for r, dist, jj in zip(rows, d, j):
        k = int(owner[jj]) if dist <= SNAP_M else None
        main = N["mains"][N["pieces"][k][0]] if k is not None else {}
        diam = float(main.get("DIAMETER") or 0) if k is not None else None
        recs.append((ts(r[2]), ts(r[3]), r[0], r[1], k, diam, main.get("MATERIAL"), round(float(dist), 1)))
    print(f"snapped within {SNAP_M:.0f} m: {sum(r[4] is not None for r in recs)}")

    import psycopg
    url = os.environ.get("TIGER_DATABASE_URL") or next(
        l.split("=", 1)[1] for l in (ROOT / ".env").read_text().splitlines() if l.startswith("TIGER_DATABASE_URL="))
    with psycopg.connect(url, autocommit=True) as c:
        c.execute("DROP MATERIALIZED VIEW IF EXISTS break_calls_weekly CASCADE")
        c.execute("DROP TABLE IF EXISTS break_calls")
        c.execute("""CREATE TABLE break_calls (opened timestamptz NOT NULL, closed timestamptz, type text, status text,
                     piece int, diameter real, material text, snap_m real)""")
        c.execute("SELECT create_hypertable('break_calls', 'opened', chunk_time_interval => interval '90 days')")
        with c.cursor() as cur, cur.copy("COPY break_calls FROM STDIN") as cp:
            for rec in recs:
                cp.write_row(rec)
        c.execute("""CREATE MATERIALIZED VIEW break_calls_weekly WITH (timescaledb.continuous) AS
                     SELECT time_bucket('7 days', opened) AS week, type,
                            CASE WHEN diameter >= 24 THEN 'transmission' WHEN diameter > 0 THEN 'distribution' ELSE 'unsnapped' END AS size,
                            count(*) AS calls, count(closed) AS closed_calls,
                            avg(EXTRACT(EPOCH FROM (closed - opened)) / 3600) AS mean_hours_to_close
                     FROM break_calls GROUP BY 1, 2, 3 WITH NO DATA""")
        c.execute("CALL refresh_continuous_aggregate('break_calls_weekly', NULL, NULL)")
        c.execute("""SELECT add_continuous_aggregate_policy('break_calls_weekly', start_offset => NULL,
                     end_offset => interval '1 day', schedule_interval => interval '1 day')""")
        n = c.execute("SELECT count(*), min(opened), max(opened) FROM break_calls").fetchone()
        w = c.execute("SELECT count(*), sum(calls) FROM break_calls_weekly").fetchone()
        print(f"break_calls: {n[0]} rows {n[1]:%Y-%m-%d} .. {n[2]:%Y-%m-%d}; weekly aggregate {w[0]} buckets, {w[1]} calls")


if __name__ == "__main__":
    main()
