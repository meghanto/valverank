"""Run cache + outage time series. Tiger Data (Timescale) when TIGER_DATABASE_URL is set, else memory.

Tables
  runs(key PK, piece, created, result jsonb)
  outage_series(run_key, scenario, t, phase, customers)   -- hypertable on t when timescaledb is available:
      one row per minute-step boundary, so SQL can sum customer-hours or plot the outage curve.
"""
import datetime as dt
import json
import os

_mem: dict = {}
_conn = None


def kind():
    return "tiger" if _conn else "memory"


def init():
    global _conn
    url = os.environ.get("TIGER_DATABASE_URL")
    if not url:
        return
    import psycopg
    _conn = psycopg.connect(url, autocommit=True)
    with _conn.cursor() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS runs(
                       key text PRIMARY KEY, piece int, created timestamptz DEFAULT now(), result jsonb)""")
        c.execute("""CREATE TABLE IF NOT EXISTS outage_series(
                       run_key text, scenario text, t timestamptz NOT NULL, phase text, customers int)""")
        try:
            c.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
            c.execute("SELECT create_hypertable('outage_series', 't', if_not_exists => TRUE)")
        except Exception as e:  # plain Postgres still works
            print("timescaledb unavailable:", str(e)[:120])


def get(key):
    if _conn:
        with _conn.cursor() as c:
            c.execute("SELECT result FROM runs WHERE key = %s", (key,))
            row = c.fetchone()
            return row[0] if row else None
    return _mem.get(key)


def put(key, result):
    if not _conn:
        _mem[key] = result
        return
    t0 = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)  # breaks are simulated from a common epoch
    rows = []
    for scen in ("paper", "real"):
        t = t0
        for ph in result[scen]["phases"]:
            rows.append((key, scen, t, ph["phase"], ph["customers"]))
            t += dt.timedelta(minutes=ph["minutes"])
        rows.append((key, scen, t, "restored", 0))
    with _conn.cursor() as c:
        c.execute("INSERT INTO runs(key, piece, result) VALUES (%s, %s, %s) ON CONFLICT (key) DO NOTHING",
                  (key, result["piece"], json.dumps(result)))
        c.executemany("INSERT INTO outage_series VALUES (%s, %s, %s, %s, %s)", rows)
