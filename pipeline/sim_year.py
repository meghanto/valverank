"""A simulated year of Houston main breaks, minute by minute, into Tiger Data.

Breaks: a seeded Poisson process per isolation segment at the planner's break rate (11,119/yr spread by pipe
length x a per-diameter rate from 311 calls; pipeline/repair.py), at uniform random times in 2027. Each break
replays its segment's engine timeline at default assumptions (gush 60 min, +90 min if a first-ring valve is
dead, then 6 h shut off) in three scenarios:
  paper  every valve works
  real   the City's valve records
  fixed  after the planner's top 100 repairs (segments whose dead ring valves are all repaired revert to
         paper; partly repaired segments are kept at 'real', which under-credits the repairs)

Tiger Data:
  sim_breaks(start, scenario, piece, diameter, phase, minutes, customers)    hypertable, one row per break phase
  sim_customers_out(t, scenario, customers)                                 hypertable, one row per minute, compressed
  sim_daily   continuous aggregate: time_bucket('1 day'), scenario -> customer-hours, peak customers out

  uv run --project pipeline python pipeline/sim_year.py [seed]
"""
import datetime as dt
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
YEAR0 = dt.datetime(2027, 1, 1, tzinfo=dt.UTC)
MIN = 365 * 24 * 60
T_FIRST, T_DEAD, T_REPAIR = 60, 90, 360


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    rng = np.random.default_rng(seed)
    N = pickle.load(open(ROOT / "data/build/network.pkl", "rb"))
    rows = list({r["seg"]: r for r in map(json.loads, open(ROOT / "data/build/batch_b.jsonl")) if "error" not in r}.values())
    fixed_ids = set(json.loads((ROOT / "data/build/fixed/ids.json").read_text()))

    # per-segment break rate: same blending as pipeline/repair.py
    br = json.loads((ROOT / "data/build/break_rates.json").read_text())
    rel = np.asarray(br["relative_rate"])
    dia = np.array([float(N["mains"][p[0]].get("DIAMETER") or 8) for p in N["pieces"]])
    L = np.array([p[4] for p in N["pieces"]])
    roots, inv = np.unique(N["seg"]["paper"], return_inverse=True)
    segw = np.bincount(inv, weights=L * rel[np.digitize(dia, br["edges_in"])])
    rix = {int(s): i for i, s in enumerate(roots)}
    w = np.array([segw[rix[r["seg"]]] for r in rows])
    rate = 11_119 * w / w.sum()                       # breaks per year per segment
    n = rng.poisson(rate)
    print(f"seed {seed}: {n.sum()} breaks in the year (expected 11,119)")

    def phases(r, scen):
        iso_p = round((r["paper_ch"] - r["gush"]) / (T_REPAIR / 60))
        iso_r = round((r["real_ch"] - r["gush"] - r["gush_dead"] * T_DEAD / 60) / (T_REPAIR / 60))
        if scen == "paper" or (scen == "fixed" and r["dead"] and set(r["dead"]) <= fixed_ids):
            return [("gush", T_FIRST, r["gush"]), ("isolated", T_REPAIR, iso_p)]
        if r["dead"]:
            return [("gush", T_FIRST, r["gush"]), ("gush_dead", T_DEAD, r["gush_dead"]), ("isolated", T_REPAIR, iso_r)]
        return [("gush", T_FIRST, r["gush"]), ("isolated", T_REPAIR, iso_r)]

    scens = ("paper", "real", "fixed")
    diff = {s: np.zeros(MIN + 1, np.int64) for s in scens}
    events = []
    for i in np.nonzero(n)[0]:
        r = rows[i]
        d = float(N["mains"][N["pieces"][r["piece"]][0]].get("DIAMETER") or 0)
        for start in rng.integers(0, MIN, n[i]):
            for s in scens:
                t = int(start)
                for ph, m, c in phases(r, s):
                    a, b = t, min(t + m, MIN)
                    if c and a < MIN:
                        diff[s][a] += c; diff[s][b] -= c
                    events.append((YEAR0 + dt.timedelta(minutes=t), s, r["piece"], d, ph, m, int(c)))
                    t += m
    series = {s: np.cumsum(diff[s])[:MIN] for s in scens}
    for s in scens:
        print(f"  {s:5}: customer-hours {series[s].sum() / 60:14,.0f}   peak customers out {series[s].max():9,}")

    import psycopg
    url = os.environ.get("TIGER_DATABASE_URL") or next(
        l.split("=", 1)[1] for l in (ROOT / ".env").read_text().splitlines() if l.startswith("TIGER_DATABASE_URL="))
    with psycopg.connect(url, autocommit=True) as c:
        c.execute("DROP MATERIALIZED VIEW IF EXISTS sim_daily CASCADE")
        c.execute("DROP TABLE IF EXISTS sim_customers_out")
        c.execute("DROP TABLE IF EXISTS sim_breaks")
        c.execute("""CREATE TABLE sim_breaks (start timestamptz NOT NULL, scenario text, piece int, diameter real,
                     phase text, minutes int, customers int)""")
        c.execute("SELECT create_hypertable('sim_breaks', 'start', chunk_time_interval => interval '30 days')")
        c.execute("CREATE TABLE sim_customers_out (t timestamptz NOT NULL, scenario text NOT NULL, customers int NOT NULL)")
        c.execute("SELECT create_hypertable('sim_customers_out', 't', chunk_time_interval => interval '7 days')")
        with c.cursor() as cur, cur.copy("COPY sim_breaks FROM STDIN") as cp:
            for e in events:
                cp.write_row(e)
        times = [YEAR0 + dt.timedelta(minutes=m) for m in range(MIN)]
        with c.cursor() as cur, cur.copy("COPY sim_customers_out FROM STDIN") as cp:
            for s in scens:
                for t, v in zip(times, series[s].tolist()):
                    cp.write_row((t, s, v))
        c.execute("""ALTER TABLE sim_customers_out SET (timescaledb.compress, timescaledb.compress_segmentby = 'scenario',
                     timescaledb.compress_orderby = 't')""")
        c.execute("SELECT count(compress_chunk(ch)) FROM show_chunks('sim_customers_out') ch")
        c.execute("""CREATE MATERIALIZED VIEW sim_daily WITH (timescaledb.continuous) AS
                     SELECT time_bucket('1 day', t) AS day, scenario, sum(customers) / 60.0 AS customer_hours,
                            max(customers) AS peak_customers
                     FROM sim_customers_out GROUP BY 1, 2 WITH NO DATA""")
        c.execute("CALL refresh_continuous_aggregate('sim_daily', NULL, NULL)")
        rows_n = c.execute("SELECT count(*) FROM sim_customers_out").fetchone()[0]
        size = c.execute("SELECT pg_size_pretty(hypertable_size('sim_customers_out'))").fetchone()[0]
        print(f"Tiger: sim_breaks {len(events):,} rows; sim_customers_out {rows_n:,} rows ({size} compressed); sim_daily refreshed")


if __name__ == "__main__":
    main()
