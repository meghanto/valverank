"""H2Out API: break timelines on the full Houston network.

  GET  /health
  GET  /break/{piece}?opening=&t_first=&t_dead=&t_repair=&exact=   timeline (fast window, or exact full city)
  GET  /nearest?lon=&lat=                                           nearest main piece to a point
  POST /ask      {"q": "..."}        Gemini turns a question into a break + params (needs GEMINI_API_KEY)
  POST /brief    {"run": {...}}       Gemini words a crew brief from a run's numbers (needs GEMINI_API_KEY)

Runs are cached in Tiger Data (Postgres/Timescale) when TIGER_DATABASE_URL is set, else in memory.
Every number comes from engine.Engine; Gemini only parses questions and words results.

  uv run --project pipeline uvicorn server.app:app --port 8787
"""
import gzip
import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.engine import Engine
from server import store
from server.codec import encode

ROOT = Path(__file__).resolve().parent.parent
for line in (ROOT / ".env").read_text().splitlines() if (ROOT / ".env").exists() else []:
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

app = FastAPI(title="H2Out")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
ENGINE: Engine | None = None


@app.on_event("startup")
def _start():
    global ENGINE
    ENGINE = Engine()
    store.init()


@app.get("/health")
def health():
    return {"ok": ENGINE is not None, "store": store.kind(), "gemini": bool(os.environ.get("GEMINI_API_KEY"))}


@app.get("/break/{piece}")
def brk(piece: int, opening: float = 0.25, t_first: int = 60, t_dead: int = 90, t_repair: int = 360, exact: bool = False,
        stage: str = "full"):
    if not 0 <= piece < len(ENGINE.pieces):
        raise HTTPException(404, "no such pipe piece")
    if not (0.01 <= opening <= 1.0 and 0 <= t_first <= 1440 and 0 <= t_dead <= 1440 and 0 <= t_repair <= 4320):
        raise HTTPException(422, "parameter out of range")
    key = run_key(ENGINE.version, piece, opening, t_first, t_dead, t_repair, exact)
    hit = disk_get(key) or store.get(key)
    if stage == "outage" and not hit:  # shut-off part only: connectivity, milliseconds, not cached
        return encode(ENGINE.run(piece, opening, t_first, t_dead, t_repair, exact, pressure=False), len(ENGINE.pieces)) | {"cached": False}
    if hit:
        return hit | {"cached": True}
    r = encode(ENGINE.run(piece, opening, t_first, t_dead, t_repair, exact), len(ENGINE.pieces))
    store.put(key, r)
    return r | {"cached": False}


def run_key(version, piece, opening=0.25, t_first=60, t_dead=90, t_repair=360, exact=False):
    """Cache key; pipeline/presolve.py uses the same function so presolved files are found."""
    return f"{version}:{piece}:{opening:.2f}:{t_first}:{t_dead}:{t_repair}:{int(exact)}"


CACHE = Path(os.environ.get("H2O_CACHE_DIR", ROOT / "data" / "build" / "cache"))


def disk_path(key):
    return CACHE / key.split(":", 1)[0] / (key.replace(":", "_") + ".json.gz")


def disk_get(key):
    f = disk_path(key)
    return json.loads(gzip.decompress(f.read_bytes())) if f.exists() else None


@app.get("/nearest")
def nearest(lon: float, lat: float):
    lat0 = 29.76
    kx, ky = 111_320 * np.cos(np.radians(lat0)), 110_574
    p = np.array([(lon + 95.4) * kx, (lat - lat0) * ky])
    # "the main at X and Y": the largest pipe with a node within 60 m, else the nearest node's largest pipe
    near = ENGINE.tree.query_ball_point(p, 60.0)
    d, i = ENGINE.tree.query(p)
    nodes = [int(ENGINE.tree_ids[j]) for j in near] or [int(ENGINE.tree_ids[i])]
    ks = np.where(np.isin(ENGINE.pa, nodes) | np.isin(ENGINE.pb, nodes))[0]
    k = int(ks[np.argmax(ENGINE.diam[ks])]) if len(ks) else None
    return {"piece": k, "distance_m": round(float(d), 1)}


@app.get("/history")
def history():
    """Real 311 water-break calls from Tiger Data (pipeline/break_calls.py): monthly open/closed counts from the
    weekly continuous aggregate, observed open->close hours, and break share by main size vs pipe-length share."""
    global _HISTORY
    if _HISTORY is None:
        conn = store._conn
        if conn is None:
            raise HTTPException(503, "Tiger Data not configured")
        with conn.cursor() as c:
            c.execute("""SELECT time_bucket('1 month', week)::date, sum(calls)::int, sum(closed_calls)::int
                         FROM break_calls_weekly GROUP BY 1 ORDER BY 1""")
            months = [{"month": str(m), "calls": n, "closed": k} for m, n, k in c.fetchall()]
            c.execute("""SELECT count(*), count(closed), min(opened)::date, max(opened)::date FROM break_calls""")
            total, closed, first, last = c.fetchone()
            c.execute("""SELECT percentile_cont(array[.25,.5,.75]) WITHIN GROUP (ORDER BY extract(epoch FROM closed - opened) / 3600), count(*)
                         FROM break_calls WHERE type = 'Water Leak' AND closed IS NOT NULL""")
            q, n_closed_leaks = c.fetchone()
            c.execute("""SELECT size, sum(calls)::int FROM break_calls_weekly WHERE type = 'Water Leak' AND size <> 'unsnapped' GROUP BY 1""")
            by_size = dict(c.fetchall())
        L = np.array([p[4] for p in ENGINE.pieces])
        _HISTORY = {
            "source": "City of Houston 311 water-break dashboard (EMC/WaterBreak_Dashboard), snapshot frozen 2024-06-20",
            "calls": total, "closed": closed, "first": str(first), "last": str(last), "months": months,
            "leak_hours_to_close": {"p25": round(q[0], 1), "median": round(q[1], 1), "p75": round(q[2], 1), "n": n_closed_leaks},
            "assumed_repair_hours": 6,
            "leak_share_transmission": round(by_size.get("transmission", 0) / max(sum(by_size.values()), 1), 3),
            "pipe_length_share_transmission": round(float(L[ENGINE.diam >= 24].sum() / L.sum()), 3),
        }
    return _HISTORY


_HISTORY = None


@app.get("/year")
def year():
    """Simulated 2027 (pipeline/sim_year.py) from Tiger Data: weekly dead-valve cost split into what the
    planner's top-100 repairs recover and what is still lost, from the sim_daily continuous aggregate."""
    global _YEAR
    if _YEAR is None:
        conn = store._conn
        if conn is None:
            raise HTTPException(503, "Tiger Data not configured")
        with conn.cursor() as c:
            c.execute("""SELECT time_bucket('7 days', day, origin => '2027-01-01'::timestamptz)::date AS week,
                                sum(customer_hours) FILTER (WHERE scenario = 'paper'),
                                sum(customer_hours) FILTER (WHERE scenario = 'real'),
                                sum(customer_hours) FILTER (WHERE scenario = 'fixed')
                         FROM sim_daily GROUP BY 1 ORDER BY 1""")
            weeks = [{"week": str(w), "dead_valve_cost": round(r - p), "after_repairs": round(f - p)} for w, p, r, f in c.fetchall()]
            c.execute("""SELECT scenario, sum(customer_hours), max(peak_customers) FROM sim_daily GROUP BY 1""")
            tot = {s: {"customer_hours": round(h), "peak_customers": int(m)} for s, h, m in c.fetchall()}
            c.execute("SELECT count(*) FROM sim_breaks WHERE scenario = 'paper' AND phase = 'gush'")
            n = c.fetchone()[0]
            c.execute("SELECT count(*) FROM sim_customers_out")
            rows = c.fetchone()[0]
        _YEAR = {"year": 2027, "breaks": n, "minute_rows": rows, "totals": tot, "weeks": weeks}
    return _YEAR


_YEAR = None


class Ask(BaseModel):
    q: str


class Brief(BaseModel):
    run: dict


@app.post("/ask")
def ask(body: Ask):
    from server import llm
    try:
        parsed = llm.parse_question(body.q)        # {"place": ..., "opening": ..., "t_first": ...}
    except Exception as e:  # quota, billing, network: say so instead of a bare 500
        raise HTTPException(503, f"Gemini unavailable: {str(e)[:120]}")
    lonlat = llm.geocode(parsed["place"])
    if not lonlat:
        raise HTTPException(404, f"could not locate {parsed['place']!r}")
    n = nearest(*lonlat)
    params = {k: parsed[k] for k in ("opening", "t_first", "t_dead", "t_repair") if parsed.get(k) is not None}
    return {"parsed": parsed, "lonlat": lonlat, "piece": n["piece"], "run": brk(n["piece"], **params)}


@app.post("/brief")
def brief(body: Brief):
    from server import llm
    try:
        return {"brief": llm.crew_brief(body.run)}
    except Exception as e:
        raise HTTPException(503, f"Gemini unavailable: {str(e)[:120]}")
