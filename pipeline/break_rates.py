"""Break rate by pipe diameter: 311 leak calls blended with pipe length (credibility / Poisson-gamma).

rate_c per km = (calls_c + A * r0) / (km_c + A), with r0 = overall calls per km and A = PRIOR_CALLS / r0 km,
so a class needs ~PRIOR_CALLS calls before its own data outweighs length-proportional weighting.
Writes data/build/break_rates.json: diameter class edges + relative rate (1.0 = length-proportional).
Source calls: Tiger Data break_calls (pipeline/break_calls.py). Direction matches the literature
(smaller mains break more often per km).

  uv run --project pipeline python pipeline/break_rates.py
"""
import json
import os
import pickle
from pathlib import Path

import numpy as np
import psycopg

ROOT = Path(__file__).resolve().parent.parent
EDGES = [5, 7, 9, 13, 21, 37]  # classes: <=4, 6, 8, 10-12, 14-20, 24-36, 42+ (inches)
LABELS = ["<=4", "6", "8", "10-12", "14-20", "24-36", "42+"]
PRIOR_CALLS = 25


def main():
    url = os.environ.get("TIGER_DATABASE_URL") or next(
        l.split("=", 1)[1] for l in (ROOT / ".env").read_text().splitlines() if l.startswith("TIGER_DATABASE_URL="))
    N = pickle.load(open(ROOT / "data/build/network.pkl", "rb"))
    d = np.array([float(N["mains"][p[0]].get("DIAMETER") or 8) for p in N["pieces"]])
    km = np.bincount(np.digitize(d, EDGES), weights=np.array([p[4] for p in N["pieces"]]) / 1000, minlength=7)
    with psycopg.connect(url) as c:
        dd = np.array([r[0] for r in c.execute("SELECT diameter FROM break_calls WHERE type = 'Water Leak' AND diameter > 0").fetchall()])
    calls = np.bincount(np.digitize(dd, EDGES), minlength=7)
    r0 = calls.sum() / km.sum()
    a = PRIOR_CALLS / r0
    rel = (calls + a * r0) / (km + a) / r0
    out = {"edges_in": EDGES, "labels": LABELS, "km": km.round(1).tolist(), "calls": calls.tolist(),
           "relative_rate": rel.round(4).tolist(), "prior_calls": PRIOR_CALLS,
           "share_24in_plus": {"length": round(km[5:].sum() / km.sum(), 4), "blended": round((rel * km)[5:].sum() / (rel * km).sum(), 4)}}
    (ROOT / "data/build/break_rates.json").write_text(json.dumps(out, indent=1))
    print(out["relative_rate"], out["share_24in_plus"])


if __name__ == "__main__":
    main()
