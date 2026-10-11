"""Compare modelled isolation segments with news-reported Houston main breaks.

For each event with coordinates: find mains within RADIUS_M of the reported
point (preferring the reported diameter), and report customers in the paper vs
real segment of each candidate. Because geocodes are approximate, results are
given as the range over candidates, plus the closest matching pipe.
"""
import csv
import math
import pickle
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RADIUS_M = 150.0
LAT0 = 29.76
KX, KY = 111_320 * math.cos(math.radians(LAT0)), 110_574


def xy(lon, lat):
    return np.array([(lon + 95.4) * KX, (lat - LAT0) * KY])


def main():
    N = pickle.load(open(ROOT / "data/build/network.pkl", "rb"))
    pieces, seg, mains, cp = N["pieces"], N["seg"], N["mains"], N["cust_piece"]
    S = pickle.load(open(ROOT / "data/build/supply.pkl", "rb"))
    cust = {}
    for s in ("paper", "real"):  # customers out = in the segment + cut off downstream of it
        c = np.bincount(seg[s][cp[cp >= 0]], minlength=len(pieces)).astype(float)
        c[S[s]["roots"]] += S[s]["lost_cust"]
        cust[s] = c.astype(int)
    mids = np.array([xy(*p[3][len(p[3]) // 2]) for p in pieces])
    diam = np.array([mains[p[0]].get("DIAMETER") or 0 for p in pieces])

    rows = []
    for ev in csv.DictReader(open(ROOT / "validation/news_breaks.csv")):
        if not ev["lat"]:
            continue
        p = xy(float(ev["lon"]), float(ev["lat"]))
        d = np.hypot(*(mids - p).T)
        near = np.where(d <= RADIUS_M)[0]
        want = float(ev["diameter_in"]) if ev["diameter_in"] else None
        match = near[diam[near] == want] if want else near
        cand = match if len(match) else near
        if not len(cand):
            rows.append((ev, None))
            continue
        best = cand[np.argmin(d[cand])]
        rows.append((ev, dict(
            n=len(cand), matched_diam=bool(want and len(match)),
            best=(int(cust["paper"][seg["paper"][best]]), int(cust["real"][seg["real"][best]]), diam[best], round(float(d[best]))),
            paper=(int(cust["paper"][seg["paper"][cand]].min()), int(cust["paper"][seg["paper"][cand]].max())),
            real=(int(cust["real"][seg["real"][cand]].min()), int(cust["real"][seg["real"][cand]].max())),
        )))

    out = ["| ID | Date | Location | Reported | Diam | Candidates | Closest pipe: paper → real customers | Range paper | Range real |",
           "|---|---|---|---|---|---|---|---|---|"]
    for ev, r in rows:
        rep = ev["reported_affected_count"] or "—"
        if r is None:
            out.append(f"| {ev['id']} | {ev['date']} | {ev['location_text'][:40]} | {rep} | {ev['diameter_in'] or '—'} | 0 | no main within {RADIUS_M:.0f} m | | |")
            continue
        b = r["best"]
        out.append(
            f"| {ev['id']} | {ev['date']} | {ev['location_text'][:40]} | {rep} | {ev['diameter_in'] or '—'} "
            f"| {r['n']}{' (diam match)' if r['matched_diam'] else ''} | {b[0]} → {b[1]} ({b[2]:.0f}″, {b[3]} m) "
            f"| {r['paper'][0]}–{r['paper'][1]} | {r['real'][0]}–{r['real'][1]} |"
        )
    text = "\n".join(out)
    (ROOT / "validation/model_vs_news.md").write_text(
        "# Model vs. news-reported main breaks\n\nCustomers = City utility accounts within 120 m of the segment's mains, "
        "plus accounts in segments cut off from every plant/pump station/tank by closing it (pipeline/supply.py). "
        f"Candidates = mains within {RADIUS_M:.0f} m of the geocoded point (filtered to the reported diameter when one matches).\n\n"
        + text + "\n")
    print(text)


if __name__ == "__main__":
    main()
