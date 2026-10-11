"""Steady-state pressure model of the Houston water network (EPANET 2.2).

UNCALIBRATED. Every assumption is a module constant below and is reported
with results. Builds data/build/houston.inp from network.pkl and solves the
baseline (no breaks) with the EPANET toolkit.

Assumptions
  - Pipes: City GIS mains, diameter as recorded (missing -> DEFAULT_DIAM_IN),
    Hazen-Williams C by material (HW_C).
  - Junction elevation: nearest hydrant's DEMELEV2018 (metres in the City data).
  - Demand: customer accounts snapped to each pipe, split to its two ends, at
    DEMAND_GPM_PER_ACCOUNT x PEAK_FACTOR.
  - Sources: the 218 in-service plants / pump stations / tanks (layer 44) as
    fixed-head reservoirs at ground + SOURCE_PSI, joined to their snapped main.
  - Pressure-reducing stations, pump curves, tank levels: not modelled.
  - Pressure-driven demand (EPANET PDA) so isolated junctions get zero flow
    instead of breaking the solve.
"""
import json
import math
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
RAW, BUILD = ROOT / "data" / "raw", ROOT / "data" / "build"
INP = BUILD / "houston.inp"
OUT = BUILD                     # --out=DIR: where the .inp / index / baseline files go (inputs always from BUILD)
ALLOC_ITERS = 0                 # --alloc=N: redistribute the capped source total to the sources that need it
HEADROOM = 1.0                  # --headroom=X: pump capacity = X x dispatched flow (TCEQ: peak hour with largest pump out)
ALLOC_TARGET_PSI = 35.0         # TCEQ normal-operation minimum; dispatch aims groundwater at shortfalls below it

DEMAND_GPM_PER_ACCOUNT = 0.27   # ~390 gal/day per account (assumed)
PEAK_FACTOR = 1.0
SOURCE_PSI = 65.0               # assumed discharge pressure at every groundwater/pump/tank source
SURFACE_PSI = 75.0              # assumed high-service discharge at the 3 surface-water plants
GW_SHARE = None                 # if set: all non-surface sources together capped at this share of demand
# Surface-water plants located from the network itself: dead ends of >=84in mains
# (East matches the geocoded plant address within 0.4 km).
SURFACE_PLANTS = {"East": (-95.2170, 29.7463), "Southeast": (-95.1541, 29.6309), "Northeast": (-95.2042, 29.9340)}
REQUIRED_PSI = 20.0             # TCEQ minimum during emergencies; below = "lost water"
DEFAULT_DIAM_IN = 8.0
HW_C = {"PVC": 150, "HDP": 150, "PLA": 150, "FRP": 140, "AC": 140, "DI": 130, "STL": 120, "PCCP": 120,
        "SRC": 120, "CONC": 120, "COP": 130, "GALV": 100, "CI": 100, "BWP": 100}
HW_DEFAULT = 120
PSI_PER_FT = 0.4335
LAT0 = 29.76
KX, KY = 111_320 * math.cos(math.radians(LAT0)), 110_574
M2FT = 3.28084


def xy(lon, lat):
    return np.column_stack([(np.asarray(lon) + 95.4) * KX, (np.asarray(lat) - LAT0) * KY])


def build():
    N = pickle.load(open(BUILD / "network.pkl", "rb"))
    S = pickle.load(open(BUILD / "supply.pkl", "rb"))
    pieces, mains, cp = N["pieces"], N["mains"], N["cust_piece"]

    # node coordinates (junction nodes from node_xy; synthetic valve nodes from piece ends)
    coord = {}
    nxy = N["node_xy"]
    for k, (_, a, b, ll, _) in enumerate(pieces):
        for n, pt in ((a, ll[0]), (b, ll[-1])):
            if n not in coord:
                coord[n] = nxy[n] if n < len(nxy) else xy([pt[0]], [pt[1]])[0]
    nodes = sorted(coord)
    idx = {n: i for i, n in enumerate(nodes)}
    P = np.array([coord[n] for n in nodes])

    # keep only what is connected to a source (unreached fragments would be singular)
    par = np.arange(len(nodes))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for _, a, b, _, _ in pieces:
        ra, rb = find(idx[a]), find(idx[b])
        if ra != rb:
            par[ra] = rb

    # elevation from nearest hydrant with a DEM value
    geo = {f["attributes"]["OBJECTID"]: f.get("geometry") for f in json.loads((RAW / "hydrants.json").read_text())}
    h = json.loads((RAW / "hydrants_attrs.json").read_text())
    he = [(g["x"], g["y"], f["attributes"]["DEMELEV2018"]) for f in h
          if (g := geo.get(f["attributes"]["OBJECTID"])) and f["attributes"].get("DEMELEV2018")]
    he = np.array(he)
    _, j = cKDTree(xy(he[:, 0], he[:, 1])).query(P)
    elev_ft = he[j, 2] * M2FT

    # demand per node
    dem = np.zeros(len(nodes))
    cnt = np.bincount(cp[cp >= 0], minlength=len(pieces))
    for k, (_, a, b, _, _) in enumerate(pieces):
        if cnt[k]:
            q = cnt[k] * DEMAND_GPM_PER_ACCOUNT * PEAK_FACTOR / 2
            dem[idx[a]] += q; dem[idx[b]] += q

    # sources: nearest network node to each snapped facility
    tree = cKDTree(P)
    src_nodes = [int(tree.query(xy([s["lon"]], [s["lat"]])[0])[1]) for s in S["snaps"] if s["kind"] != "none"]
    roots = np.array([find(i) for i in range(len(nodes))])
    big_root = np.bincount(roots).argmax()
    surf_nodes = []
    for lo, la in SURFACE_PLANTS.values():  # attach to the main network, not a nearby fragment
        _, cand = tree.query(xy([lo], [la])[0], k=200)
        surf_nodes.append(int(next(c for c in cand if roots[c] == big_root)))
    src_roots = {find(i) for i in src_nodes + surf_nodes}
    keep = np.array([find(i) in src_roots for i in range(len(nodes))])
    print(f"nodes {len(nodes)}, kept (connected to a source) {keep.sum()}, sources {len(src_nodes)}")

    lines = ["[TITLE]", "Houston water network, City GIS June 2023 snapshot. UNCALIBRATED.", "",
             "[JUNCTIONS]", ";ID Elev Demand"]
    for i in np.where(keep)[0]:
        lines.append(f"J{i} {elev_ft[i]:.2f} {dem[i]:.4f}")
    capped = GW_SHARE is not None
    cap = GW_SHARE * dem[keep].sum() / len(src_nodes) if capped else None
    caps = np.full(len(src_nodes), cap) if capped else None
    if capped:  # FCVs can't touch a reservoir: R -> pipe -> V junction -> FCV -> network
        for r, i in enumerate(src_nodes):
            lines.append(f"V{r} {elev_ft[i]:.2f} 0")
    lines += ["", "[RESERVOIRS]", ";ID Head"]
    for r, i in enumerate(src_nodes):
        lines.append(f"R{r} {elev_ft[i] + SOURCE_PSI / PSI_PER_FT:.2f}")
    for name, i in zip(SURFACE_PLANTS, surf_nodes):
        lines.append(f"S{name} {elev_ft[i] + SURFACE_PSI / PSI_PER_FT:.2f}")
    lines += ["", "[PIPES]", ";ID N1 N2 Length Diam Rough Minor Status"]
    n_pipe = 0
    for k, (_, a, b, _, L) in enumerate(pieces):
        ia, ib = idx[a], idx[b]
        if not keep[ia] or ia == ib:
            continue
        m = mains[pieces[k][0]]
        d = float(m.get("DIAMETER") or 0) or DEFAULT_DIAM_IN
        c = HW_C.get(m.get("MATERIAL"), HW_DEFAULT)
        lines.append(f"P{k} J{ia} J{ib} {max(L, 0.3) * M2FT:.2f} {d:.1f} {c} 0 Open")
        n_pipe += 1
    for r, i in enumerate(src_nodes):
        lines.append(f"C{r} R{r} {'V' + str(r) if capped else 'J' + str(i)} 30 48 130 0 CV")
    for name, i in zip(SURFACE_PLANTS, surf_nodes):
        lines.append(f"CS{name} S{name} J{i} 30 96 130 0 Open")
    if capped:
        lines += ["", "[VALVES]", ";ID N1 N2 Diam Type Setting Minor"]
        v_at = len(lines)
        for r, i in enumerate(src_nodes):
            lines.append(f"F{r} V{r} J{i} 48 FCV {caps[r]:.1f} 0")
    lines += ["", "[OPTIONS]", "Units GPM", "Headloss H-W", "Trials 200", "Accuracy 0.001",
              "Demand Model PDA", "Minimum Pressure 0", f"Required Pressure {REQUIRED_PSI}", "Pressure Exponent 0.5",
              "", "[TIMES]", "Duration 0", "", "[REPORT]", "Status No", "Summary No", "", "[END]", ""]
    INP.write_text("\n".join(lines))
    if capped and ALLOC_ITERS:
        caps = allocate(caps, service_areas(pieces, idx, keep, src_nodes, surf_nodes), dem) * HEADROOM
        for r, i in enumerate(src_nodes):
            lines[v_at + r] = f"F{r} V{r} J{i} 48 FCV {caps[r]:.1f} 0"
        INP.write_text("\n".join(lines))
    print(f"wrote {INP} ({n_pipe} pipes, {INP.stat().st_size / 1e6:.0f} MB); "
          f"surface plants {len(surf_nodes)} @ {SURFACE_PSI} psi; other sources {len(src_nodes)} @ {SOURCE_PSI} psi"
          + (f", capped at {cap:.0f} gpm each (GW_SHARE {GW_SHARE})" if capped and not ALLOC_ITERS else
             f", dispatched caps {caps.min():.0f}-{caps.max():.0f} gpm, total {caps.sum():.0f} (GW_SHARE {GW_SHARE})"
             if capped else ", uncapped"))
    np.savez(OUT / "hydraulic_index.npz", nodes=np.array(nodes), keep=keep, elev_ft=elev_ft, dem=dem,
             src_nodes=np.array(src_nodes))


def service_areas(pieces, idx, keep, src_nodes, surf_nodes):
    """Label every node with its network-nearest source (pipe length); surface plants -> -1."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    a = np.array([idx[p[1]] for p in pieces]); b = np.array([idx[p[2]] for p in pieces])
    w = np.array([max(p[4], 0.3) for p in pieces])
    ok = keep[a] & (a != b)
    n = len(keep)
    G = coo_matrix((w[ok], (a[ok], b[ok])), shape=(n, n)).tocsr()
    roots = list(src_nodes) + list(surf_nodes)
    _, _, owner = dijkstra(G, directed=False, indices=roots, min_only=True, return_predecessors=True)
    lab = {r: k for k, r in enumerate(src_nodes)}
    lab.update({r: -1 for r in surf_nodes})
    return np.array([lab.get(o, -1) for o in owner])


def allocate(caps, cell, dem):
    """Dispatch the fixed source total (GW_SHARE x demand) to where pressure is short.

    The uniform per-source cap starves areas fed mainly by their own plants (Kingwood)
    while sources whose head sits below the local grade line idle. Each round, sources
    running below their cap give up the unused flow; it goes to sources running at
    their cap in proportion to the demand-weighted pressure shortfall below
    ALLOC_TARGET_PSI in their service area (network-nearest source). The total never
    changes, so the system is no stiffer than the uniform-cap model.
    """
    from wntr.epanet.toolkit import ENepanet
    en = ENepanet()
    en.ENopen(str(INP), str(OUT / "alloc.rpt"), "")
    en.ENopenH()
    links = [en.ENgetlinkindex(f"F{r}") for r in range(len(caps))]
    nn = en.ENgetcount(0)
    ids = [en.ENgetnodeid(i) for i in range(1, nn + 1)]
    jn = np.array([k + 1 for k, s in enumerate(ids) if s[0] == "J"])
    ji = np.array([int(ids[k - 1][1:]) for k in jn])
    caps = caps.copy()
    floor = 0.1 * caps.mean()
    for it in range(ALLOC_ITERS):
        for l, c in zip(links, caps):
            en.ENsetlinkvalue(l, 5, c)  # EN_INITSETTING
        en.ENinitH(0); en.ENrunH()
        q = np.array([max(en.ENgetlinkvalue(l, 8), 0.0) for l in links])  # EN_FLOW
        p = np.array([en.ENgetnodevalue(int(k), 11) for k in jn])
        short = dem[ji] * np.clip(ALLOC_TARGET_PSI - p, 0, ALLOC_TARGET_PSI) / ALLOC_TARGET_PSI
        c = cell[ji]
        need = np.bincount(c[c >= 0], weights=short[c >= 0], minlength=len(caps))
        sat = q >= caps * 0.99
        keep_q = np.maximum(q, floor)  # idle sources keep a small setting (an FCV at 0 slows the solver ~6x)
        free = (caps - keep_q)[~sat].clip(0).sum()
        print(f"  alloc round {it}: {sat.sum()} sources at cap, {free:.0f} gpm unused; "
              f"< {ALLOC_TARGET_PSI:.0f} psi {(p < ALLOC_TARGET_PSI).mean():.4f}, < {REQUIRED_PSI:.0f} psi {(p < REQUIRED_PSI).mean():.4f}")
        wt = need * sat
        if free < 1 or not sat.any():
            break
        wt = wt / wt.sum() if wt.sum() > 0 else sat / sat.sum()
        caps = np.where(sat, caps + free * wt, np.minimum(caps, keep_q))
    en.ENcloseH(); en.ENclose()
    return caps


def solve_baseline():
    from wntr.epanet.toolkit import ENepanet
    en = ENepanet()
    en.ENopen(str(INP), str(OUT / "houston.rpt"), "")
    t = time.time()
    en.ENopenH(); en.ENinitH(0); en.ENrunH()
    print(f"baseline solve {time.time() - t:.1f} s")
    n = en.ENgetcount(0)  # EN_NODECOUNT
    pres = np.array([en.ENgetnodevalue(i, 11) for i in range(1, n + 1)])  # EN_PRESSURE (psi)
    dem = np.array([en.ENgetnodevalue(i, 9) for i in range(1, n + 1)])    # EN_DEMAND (delivered)
    ids = [en.ENgetnodeid(i) for i in range(1, n + 1)]
    en.ENcloseH(); en.ENclose()
    j = np.array([s.startswith("J") for s in ids])
    for i, s in enumerate(ids):
        if s.startswith("S"):
            print(f"  surface plant {s[1:]}: head pressure {pres[i]:.0f}, outflow {-dem[i]:.0f} gpm")
    p = pres[j]
    print("junction pressure psi pct [1,5,25,50,75,95,99]:", np.percentile(p, [1, 5, 25, 50, 75, 95, 99]).round(1))
    print(f"share < {REQUIRED_PSI} psi: {(p < REQUIRED_PSI).mean():.3f}; share 40-80 psi: {((p >= 40) & (p <= 80)).mean():.3f}")
    if OUT != BUILD:
        print(f"share < 35 psi: {(p < 35).mean():.4f}; < 40 psi: {(p < 40).mean():.4f}")
    print(f"delivered demand {dem[j].sum():.0f} gpm")
    np.save(OUT / "baseline_pressure.npy", np.column_stack([[int(s[1:]) for s in np.array(ids)[j]], p]))


if __name__ == "__main__":
    for a in sys.argv[1:]:
        if a.startswith("--gw="):
            GW_SHARE = float(a.split("=")[1])
        elif a.startswith("--out="):
            OUT = Path(a.split("=", 1)[1]).resolve()
            OUT.mkdir(parents=True, exist_ok=True)
            INP = OUT / "houston.inp"
        elif a.startswith("--headroom="):
            HEADROOM = float(a.split("=")[1])
        elif a.startswith("--alloc="):
            ALLOC_ITERS = int(a.split("=")[1])
    if "solve" not in sys.argv[1:]:
        build()
    solve_baseline()
