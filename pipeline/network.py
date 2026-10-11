"""Build the water network and valve-isolation segments.

A segment is the smallest set of pipe pieces that can be isolated by closing
valves (Walski). We compute it twice:

  paper   every valve on a main works
  real    valves the City records as inoperable (CONDITION = 'INOP') cannot
          be closed, so the segments on either side merge

Model
  - Pipe endpoints rounded to ~0.1 m form junction nodes (City data is noded).
  - A valve lying on a main (<= SNAP_M) becomes a cut point. If it sits on a
    junction node, every pipe meeting there is separated at that node. If it
    sits inside a pipe, the pipe is split into two pieces at the valve.
  - Valves farther than SNAP_M from any main are on laterals/hydrant leads and
    are ignored for main isolation. In-line valves get SNAP_INLINE_M.
  - Hydrant and service valves never cut a main, however close they sit: they
    isolate the lead, not the main (data_audit.md D1).
  - Abandoned/proposed and non-potable mains are dropped (D4).
  - A dead end within TEE_M of another pipe's interior is an unnoded tee: the
    other pipe is split there and joined to the dead end (D2).
  - Pieces that touch at a non-cut node are joined (union-find).

Outputs data/build/network.pkl for export.py.
"""
import json
import math
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
RAW, BUILD = ROOT / "data" / "raw", ROOT / "data" / "build"

SNAP_M = 1.0        # valve must lie this close to a main to count as a main valve
SNAP_INLINE_M = 3.0  # same, for valves the City records as in-line (D3)
TEE_M = 1.0         # dead end this close to another pipe's interior = unnoded tee
INLINE_USE = {"INL", "IN LINE", "IN LINE - SLF"}
LEAD_USE = {"HYD LEAD", "HL", "SERVICE", "SERV", "FIRE SERVICE"}
HYDRANT_VALVE_SUBTYPE = 33
NODE_M = 0.5        # valve this close to a junction node sits "at" the node
CUSTOMER_M = 120.0  # max distance customer point -> main
HYDRANT_M = 40.0    # max distance hydrant -> main
LAT0 = 29.76
KX, KY = 111_320 * math.cos(math.radians(LAT0)), 110_574  # metres per degree


def xy(lon, lat):
    return np.column_stack([(np.asarray(lon) + 95.4) * KX, (np.asarray(lat) - LAT0) * KY])


class DSU:
    def __init__(self, n):
        self.p = np.arange(n)

    def find(self, a):
        p = self.p
        root = a
        while p[root] != root:
            root = p[root]
        while p[a] != root:
            p[a], a = root, p[a]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def load(name):
    return json.loads((RAW / f"{name}.json").read_text())


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    extra = {f["attributes"]["OBJECTID"]: f["attributes"] for f in load("mains_attrs")}
    raw = [f for f in load("mains") if f.get("geometry", {}).get("paths")]
    for f in raw:
        f["attributes"].update(extra[f["attributes"]["OBJECTID"]])
    mains = [f for f in raw
             if f["attributes"].get("LIFECYCLESTATUS") not in ("A", "P")
             and f["attributes"].get("WATERTYPE") not in ("NOPW", "NOPC")]
    print("mains with geometry:", len(raw), "kept (in use, potable):", len(mains))

    # --- pipes as polylines in metres -------------------------------------
    pipes = []  # (main_idx, coords_xy ndarray, coords_lonlat list)
    for i, f in enumerate(mains):
        for path in f["geometry"]["paths"]:
            if len(path) >= 2:
                ll = np.asarray(path)
                pipes.append((i, xy(ll[:, 0], ll[:, 1]), path))
    print("pipe parts:", len(pipes))

    # --- junction nodes from endpoints ------------------------------------
    def key(p):
        return (round(p[0] * 10), round(p[1] * 10))  # 0.1 m grid

    node_id, node_xy, deg = {}, [], Counter()
    ends = []
    for _, c, _ in pipes:
        e = []
        for p in (c[0], c[-1]):
            k = key(p)
            if k not in node_id:
                node_id[k] = len(node_xy)
                node_xy.append(p)
            e.append(node_id[k])
            deg[node_id[k]] += 1
        ends.append(e)
    node_xy = np.asarray(node_xy)
    print("nodes:", len(node_xy), "degree hist:", dict(sorted(Counter(deg.values()).items())[:6]))

    # --- valves: snap to mains ----------------------------------------------
    valves = [v for v in load("valves") if v.get("geometry")]
    vxy = xy([v["geometry"]["x"] for v in valves], [v["geometry"]["y"] for v in valves])
    node_tree = cKDTree(node_xy)

    # dense samples along pipes for nearest-pipe queries
    samp_xy, samp_pipe, samp_seg, samp_t = [], [], [], []
    for pi, (_, c, _) in enumerate(pipes):
        for s in range(len(c) - 1):
            a, b = c[s], c[s + 1]
            n = max(1, int(np.hypot(*(b - a)) // 2.0))
            for t in np.linspace(0, 1, n + 1):
                samp_xy.append(a + t * (b - a)); samp_pipe.append(pi); samp_seg.append(s); samp_t.append(t)
    samp_xy = np.asarray(samp_xy)
    samp_pipe, samp_seg, samp_t = map(np.asarray, (samp_pipe, samp_seg, samp_t))
    samp_tree = cKDTree(samp_xy)
    print("pipe samples:", len(samp_xy))

    def seg_dist(p, a, b):
        ab = b - a
        L = ab @ ab
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p - a) @ ab) / L))
        q = a + t * ab
        return float(np.hypot(*(p - q))), t

    pipe_cuts = defaultdict(list)      # pipe -> [(seg, t, valve idx | ("J", node))]

    # --- unnoded tees ---------------------------------------------------------
    own = defaultdict(set)
    for pi, (a_n, b_n) in enumerate(ends):
        own[a_n].add(pi); own[b_n].add(pi)
    dangling = [n for n, c in deg.items() if c == 1]
    _, dnear = samp_tree.query(node_xy[dangling], k=8)
    n_tee = 0
    for n, cand in zip(dangling, dnear):
        p = node_xy[n]
        best = (TEE_M, None, None, None)
        for si in set(int(samp_pipe[j]) for j in cand) - own[n]:
            c = pipes[si][1]
            for s in range(len(c) - 1):
                d, t = seg_dist(p, c[s], c[s + 1])
                if d <= best[0]:
                    best = (d, si, s, t)
        if best[1] is not None:
            pipe_cuts[best[1]].append((best[2], best[3], ("J", n)))
            n_tee += 1
    print("unnoded tees joined:", n_tee)

    node_valves = defaultdict(list)    # node -> valve idx
    valve_place = {}
    nd, nn = node_tree.query(vxy)
    _, near = samp_tree.query(vxy, k=8)
    for vi, p in enumerate(vxy):
        a = valves[vi]["attributes"]
        if a.get("SUBTYPECD") == HYDRANT_VALVE_SUBTYPE or a.get("VALVE_USE") in LEAD_USE:
            valve_place[vi] = ("lead", None, float(nd[vi]))
            continue
        snap = SNAP_INLINE_M if a.get("VALVE_USE") in INLINE_USE else SNAP_M
        if nd[vi] <= NODE_M:
            node_valves[int(nn[vi])].append(vi)
            valve_place[vi] = ("node", int(nn[vi]), 0.0)
            continue
        best = (1e9, None, None, None)
        for si in set(int(samp_pipe[j]) for j in near[vi]):
            c = pipes[si][1]
            for s in range(len(c) - 1):
                d, t = seg_dist(p, c[s], c[s + 1])
                if d < best[0]:
                    best = (d, si, s, t)
        if best[0] <= snap:
            pipe_cuts[best[1]].append((best[2], best[3], vi))
            valve_place[vi] = ("pipe", best[1], best[0])
        else:
            valve_place[vi] = ("off", None, best[0])
    kinds = Counter(k for k, _, _ in valve_place.values())
    print("valve placement:", dict(kinds))

    # --- pieces: split pipes at interior valves -----------------------------
    # piece = (pipe idx, start node token, end node token, lonlat coords, length m)
    pieces, piece_pipe = [], []
    vnode_base = len(node_xy)
    valve_node_of = {}  # interior valve -> synthetic node id
    for pi, (mi, c, ll) in enumerate(pipes):
        cuts = sorted(pipe_cuts.get(pi, []), key=lambda c: (c[0], c[1]))
        a_node, b_node = ends[pi]
        if not cuts:
            pieces.append((pi, a_node, b_node, ll, float(np.sum(np.hypot(*np.diff(c, axis=0).T)))))
            piece_pipe.append(pi)
            continue
        prev_node, prev_pt = a_node, (0, 0.0)
        for s, t, vi in cuts + [(len(c) - 2, 1.0, None)]:
            if vi is None:
                cur_node = b_node
            elif isinstance(vi, tuple):  # unnoded tee: split here, join the dead end
                cur_node = vi[1]
            else:
                cur_node = vnode_base + len(valve_node_of)
                valve_node_of[vi] = cur_node
            # coordinates from prev_pt to (s, t)
            ps, pt = prev_pt
            pts = [np.asarray(ll[ps]) + pt * (np.asarray(ll[ps + 1]) - np.asarray(ll[ps]))]
            pts += [np.asarray(ll[k]) for k in range(ps + 1, s + 1)]
            pts.append(np.asarray(ll[s]) + t * (np.asarray(ll[s + 1]) - np.asarray(ll[s])))
            pts = np.asarray(pts)
            m = xy(pts[:, 0], pts[:, 1])
            length = float(np.sum(np.hypot(*np.diff(m, axis=0).T))) if len(m) > 1 else 0.0
            pieces.append((pi, prev_node, cur_node, pts.tolist(), length))
            piece_pipe.append(pi)
            prev_node, prev_pt = cur_node, (s, t)
    print("pieces:", len(pieces), "interior valve nodes:", len(valve_node_of))

    # cut nodes: valve id lists per node (junction or synthetic)
    cut_valves = defaultdict(list)
    for n, vs in node_valves.items():
        cut_valves[n].extend(vs)
    for vi, n in valve_node_of.items():
        cut_valves[n].append(vi)

    def is_closable(vi, scenario):
        v = valves[vi]["attributes"]
        if v.get("NORMALPOSITION") == 0:  # normally closed: always a boundary
            return True
        if scenario == "real" and v.get("CONDITION") == "INOP":
            return False
        return True

    inc = defaultdict(list)  # node -> piece ids
    for k, (_, a, b, _, _) in enumerate(pieces):
        inc[a].append(k)
        inc[b].append(k)

    result = {}
    for scen in ("paper", "real"):
        dsu = DSU(len(pieces))
        for n, ks in inc.items():
            vs = cut_valves.get(n)
            if vs and any(is_closable(v, scen) for v in vs):
                continue  # a working valve here separates the pieces
            for k in ks[1:]:
                dsu.union(ks[0], k)
        seg = np.array([dsu.find(k) for k in range(len(pieces))])
        result[scen] = seg
        sizes = Counter(seg.tolist())
        print(f"{scen}: segments={len(sizes)}  median pieces/segment={np.median(list(sizes.values())):.0f}")

    # --- customers and hydrants -> nearest piece ----------------------------
    piece_samples, piece_of_sample = [], []
    for k, (_, _, _, ll, _) in enumerate(pieces):
        pts = np.asarray(ll)
        m = xy(pts[:, 0], pts[:, 1])
        for s in range(len(m) - 1):
            n = max(1, int(np.hypot(*(m[s + 1] - m[s])) // 5.0))
            for t in np.linspace(0, 1, n + 1):
                piece_samples.append(m[s] + t * (m[s + 1] - m[s])); piece_of_sample.append(k)
    ptree = cKDTree(np.asarray(piece_samples))
    piece_of_sample = np.asarray(piece_of_sample)

    def assign(feats, maxd):
        g = [f["geometry"] for f in feats if f.get("geometry")]
        P = xy([q["x"] for q in g], [q["y"] for q in g])
        d, j = ptree.query(P)
        out = np.where(d <= maxd, piece_of_sample[j], -1)
        return out, P

    cust_piece, cust_xy = assign(load("customers"), CUSTOMER_M)
    hyd = load("hydrants")
    hyd_piece, hyd_xy = assign(hyd, HYDRANT_M)
    print(f"customers assigned: {(cust_piece >= 0).mean():.1%} of {len(cust_piece)}; hydrants: {(hyd_piece >= 0).mean():.1%} of {len(hyd_piece)}")

    with open(BUILD / "network.pkl", "wb") as fh:
        pickle.dump(
            dict(
                mains=[f["attributes"] for f in mains],
                pieces=pieces,
                seg=result,
                valves=valves,
                valve_place=valve_place,
                cut_valves=dict(cut_valves),
                node_xy=node_xy,
                valve_node_of=valve_node_of,
                node_valves=dict(node_valves),
                cust_piece=cust_piece,
                hyd=hyd,
                hyd_piece=hyd_piece,
            ),
            fh,
        )
    print("wrote", BUILD / "network.pkl")


if __name__ == "__main__":
    sys.exit(main())
