"""Valve repair planner: which inoperable valves to fix first.

Input: data/build/batch.jsonl (one simulated break per paper segment).
For paper segment s with dead first-ring valves D_s:
  extra_s = (real_ch - paper_ch) customer-hours per break
  rate_s  = BREAKS_PER_YEAR * length_s / total_length     (breaks/yr landing in s)
  value_s = extra_s * rate_s                               (customer-hours/yr lost to dead valves)
Repairing every valve in D_s recovers value_s (crews can close the first ring).

Greedy: each step repairs the valve with the most credit, where a segment's value
is split evenly over its still-dead ring valves (so 2-valve rings aren't invisible).
Writes web/public/data/repair.json: curve + ordered valves (id, lon, lat, gain).
"""
import json
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BREAKS_PER_YEAR = 11_119   # HPW FY2023 "water main breaks" (likely includes leak repairs; see data_audit.md)
TOP = 3000


def fix_timing(r, t_first=60, t_dead=90, t_repair=360):
    """Rows written before v2 shortened the real isolated phase to t_repair - t_dead.
    Customer counts are integers, so the isolated count is recovered exactly from the totals."""
    if r.get("v", 1) >= 2 or not r["dead"]:
        return r
    rest = (r["real_ch"] - r["gush"] * t_first / 60 - r["gush_dead"] * t_dead / 60)
    iso = round(rest / ((t_repair - t_dead) / 60))
    return dict(r, real_ch=round(r["gush"] * t_first / 60 + r["gush_dead"] * t_dead / 60 + iso * t_repair / 60), v=2)


def main():
    rows = [json.loads(l) for l in open(ROOT / "data/build/batch.jsonl") if l.strip()]
    rows = {r["seg"]: r for r in rows if "error" not in r}  # one row per segment (resumed runs may repeat)
    # transmission mains re-run on the corrected hydraulic model (audit §13); their pressure phase dominates.
    # Distribution rows keep the earlier run: gushing is ~1% of their customer-hours.
    trans = ROOT / "data/build/batch_b_trans.jsonl"
    if trans.exists():
        new = [json.loads(l) for l in open(trans) if l.strip()]
        rows.update({r["seg"]: r for r in new if "error" not in r})
    rows = [fix_timing(r) for r in rows.values()]
    N = pickle.load(open(ROOT / "data/build/network.pkl", "rb"))
    total_len = sum(p[4] for p in N["pieces"])
    covered_len = sum(r["length_m"] for r in rows)
    vxy = {v["attributes"]["OBJECTID"]: (v["geometry"]["x"], v["geometry"]["y"]) for v in N["valves"]}

    value, ring = {}, {}
    base_paper = base_real = 0.0
    split = {c: {"breaks_per_year": 0.0, "paper": 0.0, "real": 0.0, "gushing_paper": 0.0} for c in ("distribution", "transmission")}
    for r in rows:
        rate = BREAKS_PER_YEAR * r["length_m"] / total_len
        base_paper += r["paper_ch"] * rate
        base_real += r["real_ch"] * rate
        c = split["transmission" if r["exact"] else "distribution"]  # exact = diameter >= 24 in
        c["breaks_per_year"] += rate; c["paper"] += r["paper_ch"] * rate; c["real"] += r["real_ch"] * rate
        c["gushing_paper"] += r["gush"] * rate  # t_first = 60 min, so customers = customer-hours
        if r["dead"] and r["real_ch"] > r["paper_ch"]:
            value[r["seg"]] = (r["real_ch"] - r["paper_ch"]) * rate
            ring[r["seg"]] = set(r["dead"])
    by_valve = defaultdict(set)
    for s, d in ring.items():
        for v in d:
            by_valve[v].add(s)

    remaining = {s: set(d) for s, d in ring.items()}
    recovered, order, curve = 0.0, [], [0.0]
    credit = lambda v: sum(value[s] / len(remaining[s]) for s in by_valve[v] if remaining[s])
    cand = set(by_valve)
    while cand and len(order) < TOP:
        v = max(cand, key=credit)
        cand.discard(v)
        gain = 0.0
        for s in by_valve[v]:
            if remaining[s]:
                remaining[s].discard(v)
                if not remaining[s]:
                    gain += value[s]
        recovered += gain
        lon, lat = vxy[v]
        order.append({"id": v, "lon": round(lon, 5), "lat": round(lat, 5), "gain": round(gain)})
        curve.append(round(recovered))
    out = {
        "breaks_per_year": BREAKS_PER_YEAR,
        "coverage_share_of_pipe_length": round(covered_len / total_len, 3),
        "customer_hours_per_year": {"paper": round(base_paper), "real": round(base_real)},
        "dead_valve_cost_per_year": round(base_real - base_paper),
        "by_class": {c: {k: round(v) for k, v in d.items()} for c, d in split.items()},
        "recoverable_by_first_ring_repairs": round(sum(value.values())),
        "dead_valves_in_some_ring": len(by_valve),
        "curve": curve,
        "valves": order,
    }
    (ROOT / "web/public/data/repair.json").write_text(json.dumps(out, separators=(",", ":")))
    print({k: v for k, v in out.items() if k not in ("curve", "valves")})
    for n in (10, 50, 100, 500, 1000, len(order)):
        if n <= len(order):
            print(f"  repair top {n}: recovers {curve[n]:,} customer-hours/yr "
                  f"({curve[n] / max(out['dead_valve_cost_per_year'], 1):.0%} of the dead-valve cost)")


if __name__ == "__main__":
    main()
