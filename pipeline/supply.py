"""Downstream supply loss ("unintended isolation").

Closing a segment's boundary valves can also cut off segments whose only path
to a water source runs through it. We model sources as the City's in-service
plants, pump stations and storage tanks (UtilityAnalysis_gx layer 44), snapped
to the nearest main.

Segment graph: one vertex per segment; an edge wherever segments meet at a
working valve. Add a super-source X joined to every segment that holds a
source. Removing segment v cuts off exactly the DFS subtrees of children c of
v with low[c] >= disc[v] (articulation-point rule), so one iterative Tarjan
DFS per scenario gives every segment's downstream loss in O(V + E).

Connectivity only: a segment reached through any pipe counts as supplied, so
this is still a lower bound on who loses water.

Writes data/build/supply.pkl: per scenario, per segment root id ->
downstream customers / hydrants, plus snap diagnostics.
"""
import json
import math
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
RAW, BUILD = ROOT / "data" / "raw", ROOT / "data" / "build"
SOURCE_SUBTYPES = {14: "Elevated Storage Tank", 15: "Treatment Plant", 16: "Pump Station", 17: "Ground Storage Tank"}
SNAP_M = 300.0       # facility point -> nearest main
MIN_DIAM_IN = 12     # prefer mains at least this large when snapping a facility
LAT0 = 29.76
KX, KY = 111_320 * math.cos(math.radians(LAT0)), 110_574


def xy(lon, lat):
    return np.column_stack([(np.asarray(lon) + 95.4) * KX, (np.asarray(lat) - LAT0) * KY])


def closable(a, scen):
    if a.get("NORMALPOSITION") == 0:
        return True
    return not (scen == "real" and a.get("CONDITION") == "INOP")


def articulation_loss(n, adj, sources, weight):
    """Return per-vertex weight cut off from the super-source when that vertex is removed.

    Vertices 0..n-1 are segments; vertex n is the super-source.
    """
    X = n
    adj = [list(a) + ([X] if v in sources else []) for v, a in enumerate(adj)] + [sorted(sources)]
    disc = np.full(n + 1, -1)
    low = np.zeros(n + 1, dtype=np.int64)
    sub = np.zeros(n + 1)
    lost = np.zeros(n + 1)
    parent = np.full(n + 1, -1)
    t = 0
    disc[X] = low[X] = t; t += 1
    stack = [(X, 0)]
    while stack:
        v, i = stack[-1]
        if i < len(adj[v]):
            stack[-1] = (v, i + 1)
            w = adj[v][i]
            if disc[w] == -1:
                parent[w] = v
                disc[w] = low[w] = t; t += 1
                sub[w] = weight[w]
                stack.append((w, 0))
            elif w != parent[v]:
                low[v] = min(low[v], disc[w])
        else:
            stack.pop()
            p = parent[v]
            if p >= 0:
                low[p] = min(low[p], low[v])
                sub[p] += sub[v]
                if p != X and low[v] >= disc[p]:
                    lost[p] += sub[v]
    return lost[:n], disc[:n] >= 0


def main():
    N = pickle.load(open(BUILD / "network.pkl", "rb"))
    pieces, seg, valves, mains = N["pieces"], N["seg"], N["valves"], N["mains"]
    cust_piece, hyd_piece, cut_valves = N["cust_piece"], N["hyd_piece"], N["cut_valves"]
    P = len(pieces)

    # --- sources: facility points -> nearest piece --------------------------
    fac = [f for f in json.loads((RAW / "structures_attrs.json").read_text())
           if f["attributes"]["SUBTYPECD"] in SOURCE_SUBTYPES and f["attributes"].get("LIFECYCLESTATUS") == "E"]
    samp, owner = [], []
    for k, p in enumerate(pieces):
        m = xy(*np.asarray(p[3]).T)
        for s in range(len(m) - 1):
            n = max(1, int(np.hypot(*(m[s + 1] - m[s])) // 5.0))
            for tt in np.linspace(0, 1, n + 1):
                samp.append(m[s] + tt * (m[s + 1] - m[s])); owner.append(k)
    samp, owner = np.asarray(samp), np.asarray(owner)
    diam = np.array([float(mains[p[0]].get("DIAMETER") or 0) for p in pieces])
    big = diam[owner] >= MIN_DIAM_IN
    t_all, t_big = cKDTree(samp), cKDTree(samp[big])
    owner_big = owner[big]
    F = xy([f["geometry"]["x"] for f in fac], [f["geometry"]["y"] for f in fac])
    db, jb = t_big.query(F)
    da, ja = t_all.query(F)
    src_piece, snaps = [], []
    for i, f in enumerate(fac):
        if db[i] <= SNAP_M:
            k, d, kind = int(owner_big[jb[i]]), float(db[i]), "big"
        elif da[i] <= SNAP_M:
            k, d, kind = int(owner[ja[i]]), float(da[i]), "any"
        else:
            k, d, kind = -1, float(da[i]), "none"
        snaps.append(dict(subtype=SOURCE_SUBTYPES[f["attributes"]["SUBTYPECD"]], dist_m=round(d, 1), kind=kind,
                          diam=float(diam[k]) if k >= 0 else None, lon=f["geometry"]["x"], lat=f["geometry"]["y"]))
        if k >= 0:
            src_piece.append(k)
    print("facilities:", len(fac), "snapped:", len(src_piece), Counter(s["kind"] for s in snaps))
    print("snap distance pct (m):", np.percentile([s["dist_m"] for s in snaps], [25, 50, 75, 90]).round(0))

    inc = defaultdict(list)
    for k, (_, a, b, _, _) in enumerate(pieces):
        inc[a].append(k); inc[b].append(k)

    out = dict(snaps=snaps)
    for scen in ("paper", "real"):
        s = seg[scen]
        roots, comp = np.unique(s, return_inverse=True)  # compact vertex ids
        n = len(roots)
        cust = np.bincount(comp[cust_piece[cust_piece >= 0]], minlength=n).astype(float)
        hyd = np.bincount(comp[hyd_piece[hyd_piece >= 0]], minlength=n).astype(float)
        adj = [set() for _ in range(n)]
        for node, vs in cut_valves.items():
            if not any(closable(valves[v]["attributes"], scen) for v in vs):
                continue
            segs = {int(comp[k]) for k in inc.get(node, [])}
            for a in segs:
                adj[a] |= segs - {a}
        sources = {int(comp[k]) for k in src_piece}
        lost_c, reached = articulation_loss(n, adj, sources, cust)
        lost_h, _ = articulation_loss(n, adj, sources, hyd)
        unreached_cust = int(cust[~reached].sum())
        print(f"{scen}: segments={n} source segments={len(sources)} "
              f"unreached segments={int((~reached).sum())} (customers {unreached_cust}) "
              f"segments with downstream loss={int((lost_c > 0).sum())} max downstream={int(lost_c.max())}")
        out[scen] = dict(roots=roots, lost_cust=lost_c, lost_hyd=lost_h, reached=reached, sources=sorted(sources))
    with open(BUILD / "supply.pkl", "wb") as fh:
        pickle.dump(out, fh)
    print("wrote", BUILD / "supply.pkl")


if __name__ == "__main__":
    main()
