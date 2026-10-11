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
def brk(piece: int, opening: float = 0.25, t_first: int = 60, t_dead: int = 90, t_repair: int = 360, exact: bool = False):
    if not 0 <= piece < len(ENGINE.pieces):
        raise HTTPException(404, "no such pipe piece")
    if not (0.01 <= opening <= 1.0 and 0 <= t_first <= 1440 and 0 <= t_dead <= 1440 and 0 <= t_repair <= 4320):
        raise HTTPException(422, "parameter out of range")
    key = f"{piece}:{opening:.2f}:{t_first}:{t_dead}:{t_repair}:{int(exact)}"
    hit = store.get(key)
    if hit:
        return hit | {"cached": True}
    r = ENGINE.run(piece, opening, t_first, t_dead, t_repair, exact)
    store.put(key, r)
    return r | {"cached": False}


@app.get("/nearest")
def nearest(lon: float, lat: float):
    lat0 = 29.76
    kx, ky = 111_320 * np.cos(np.radians(lat0)), 110_574
    p = np.array([(lon + 95.4) * kx, (lat - lat0) * ky])
    d, i = ENGINE.tree.query(p)
    node = int(ENGINE.tree_ids[i])
    ks = np.where((ENGINE.pa == node) | (ENGINE.pb == node))[0]
    k = int(ks[np.argmax(ENGINE.diam[ks])]) if len(ks) else None
    return {"piece": k, "distance_m": round(float(d), 1)}


class Ask(BaseModel):
    q: str


class Brief(BaseModel):
    run: dict


@app.post("/ask")
def ask(body: Ask):
    from server import llm
    parsed = llm.parse_question(body.q)            # {"place": ..., "opening": ..., "t_first": ...}
    lonlat = llm.geocode(parsed["place"])
    if not lonlat:
        raise HTTPException(404, f"could not locate {parsed['place']!r}")
    n = nearest(*lonlat)
    params = {k: parsed[k] for k in ("opening", "t_first", "t_dead", "t_repair") if parsed.get(k) is not None}
    return {"parsed": parsed, "lonlat": lonlat, "piece": n["piece"], "run": brk(n["piece"], **params)}


@app.post("/brief")
def brief(body: Brief):
    from server import llm
    return {"brief": llm.crew_brief(body.run)}
