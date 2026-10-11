"""Break engine: timeline of one break, fast (local window) or exact (full city).

Phases (see pipeline/sim.py for the definitions):
  gush        break open, nothing closed                         t_first min
  gush_dead   working ring valves closed, dead valve open        t_dead min   (real only, if a dead valve is in the ring)
  isolated    segment closed (+ segments cut off downstream)     t_repair (repair starts once isolated)

Isolated phases use exact connectivity (segment + downstream supply loss).
Gushing phases use EPANET: a local window (RADIUS_M, boundary pinned to baseline
head) for mains < BIG_IN, or the full city for transmission mains or when
exact=True. Window accuracy vs full solve: validation/data_audit.md §10.
"""
import json
import os
import pickle
import tempfile
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from wntr.epanet.toolkit import ENepanet

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "data" / "build"
HYD = Path(os.environ.get("H2O_HYDRAULIC_DIR", BUILD))  # alternative hydraulic model (houston.inp + hydraulic_index.npz)
INP = HYD / "houston.inp"
REQUIRED_PSI = 20.0
# gushing-phase impact = pressure lost vs baseline, not an absolute floor: the uncalibrated baseline is
# weakest far from the plants (west Houston), so 'newly below 20 psi' lit up the wrong place (audit §10)
DROP_PSI = 15.0
ENGINE_REV = "3"  # bump when run() logic changes results (part of the cache version); pressure=False only adds a mode
# areas the 4 km window can't solve: Kingwood is fed by its own capped sources and ~10 boundary pipes,
# so pinning the window boundary at baseline head hides a 40+ psi drop (audit §13). Full solve there.
EXACT_BOXES = [(-95.30, 29.98, -95.10, 30.15)]  # lon0, lat0, lon1, lat1
PSI_PER_FT = 0.4335
RADIUS_M = 4000.0  # window accuracy at 4 km: median 0.5 psi, worst 3.9 psi vs full solve (29 breaks)
BIG_IN = 24
EN_EMITTER, EN_INITSTATUS, EN_HEAD, EN_PRESSURE = 3, 4, 10, 11


# scenario 'fixed': City records after repairing the planner's top N dead valves (pipeline/fixed.py)
FIXED = BUILD / "fixed"
FIXED_IDS = set(json.loads((FIXED / "ids.json").read_text())) if (FIXED / "ids.json").exists() else set()


def closable(a, scen):
    if a.get("NORMALPOSITION") == 0:
        return True
    if scen == "fixed":
        return a.get("CONDITION") != "INOP" or a.get("OBJECTID") in FIXED_IDS
    return not (scen == "real" and a.get("CONDITION") == "INOP")


def emitter_coeff(diam_in, opening, p_ref=55.0):
    area = np.pi * (diam_in / 12) ** 2 / 4
    return opening * 0.6 * area * np.sqrt(2 * 32.2 * p_ref / PSI_PER_FT) * 448.83 / np.sqrt(p_ref)


class Engine:
    def __init__(self):
        t0 = time.time()
        N = pickle.load(open(BUILD / "network.pkl", "rb"))
        S = pickle.load(open(BUILD / "supply.pkl", "rb"))
        H = np.load(HYD / "hydraulic_index.npz")
        self.scens = ("paper", "real")
        if FIXED_IDS:
            N["seg"]["fixed"] = np.load(FIXED / "seg.npy")
            S["fixed"] = pickle.load(open(FIXED / "supply.pkl", "rb"))
            self.scens = ("paper", "real", "fixed")
        self.N, self.S = N, S
        self.pieces, self.mains, self.valves, self.cut = N["pieces"], N["mains"], N["valves"], N["cut_valves"]
        P = len(self.pieces)
        nodes = H["nodes"]
        self.hidx = {int(n): i for i, n in enumerate(nodes)}          # network node -> hydraulic index
        self.diam = np.array([float(self.mains[p[0]].get("DIAMETER") or 8) for p in self.pieces])
        cp = N["cust_piece"]
        self.cust_piece = np.bincount(cp[cp >= 0], minlength=P).astype(float)
        hp = N["hyd_piece"]
        self.hyd_piece = np.bincount(hp[hp >= 0], minlength=P).astype(float)
        self.pa = np.array([self.hidx[p[1]] for p in self.pieces])
        self.pb = np.array([self.hidx[p[2]] for p in self.pieces])
        self.inc = defaultdict(list)
        for k, (_, a, b, _, _) in enumerate(self.pieces):
            self.inc[a].append(k); self.inc[b].append(k)

        # segment membership + segment graph (for downstream sets)
        self.members, self.sgraph, self.comp, self.src = {}, {}, {}, {}
        for s in self.scens:
            roots, comp = np.unique(N["seg"][s], return_inverse=True)
            self.comp[s] = comp
            mem = defaultdict(list)
            for k, c in enumerate(comp):
                mem[int(c)].append(k)
            self.members[s] = mem
            adj = [set() for _ in range(len(roots))]
            for node, vs in self.cut.items():
                if any(closable(self.valves[v]["attributes"], s) for v in vs):
                    segs = {int(comp[k]) for k in self.inc.get(node, [])}
                    for a in segs:
                        adj[a] |= segs - {a}
            self.sgraph[s] = adj
            self.src[s] = set(S[s]["sources"])

        # full EPANET model (exact solves + baseline heads for windows)
        self.lock = threading.Lock()
        self.en = en = ENepanet()
        en.ENopen(str(INP), str(BUILD / "engine.rpt"), "")
        en.ENopenH(); en.ENinitH(0); en.ENrunH()
        self.nn = en.ENgetcount(0)
        ids = [en.ENgetnodeid(i) for i in range(1, self.nn + 1)]
        self.jpos = np.array([i for i, s in enumerate(ids) if s[0] == "J"])
        self.jnode = np.array([int(ids[i][1:]) for i in self.jpos])
        nj = len(nodes)
        self.base_p = np.full(nj, np.nan)
        self.base_h = np.full(nj, np.nan)
        self.base_p[self.jnode] = [en.ENgetnodevalue(int(i) + 1, EN_PRESSURE) for i in self.jpos]
        self.base_h[self.jnode] = [en.ENgetnodevalue(int(i) + 1, EN_HEAD) for i in self.jpos]
        self.link = {}
        for k in range(P):
            try:
                self.link[k] = en.ENgetlinkindex(f"P{k}")
            except Exception:
                pass

        # INP arrays for windows
        self._parse_inp()
        node_xy = np.full((nj, 2), np.nan)
        from_pieces = {}
        for k, p in enumerate(self.pieces):
            from_pieces.setdefault(self.pa[k], p[3][0]); from_pieces.setdefault(self.pb[k], p[3][-1])
        lat0 = 29.76
        kx, ky = 111_320 * np.cos(np.radians(lat0)), 110_574
        for i, ll in from_pieces.items():
            node_xy[i] = ((ll[0] + 95.4) * kx, (ll[1] - lat0) * ky)
        self.node_xy = node_xy
        ok = np.where(np.isfinite(node_xy[:, 0]) & np.isfinite(self.base_h))[0]
        self.tree, self.tree_ids = cKDTree(node_xy[ok]), ok
        self.tmp = Path(tempfile.mkdtemp(prefix="h2o_"))
        # cache version: changes whenever model files or engine settings change, so stale results are never served
        import hashlib
        h = hashlib.sha1()
        for f in (INP, BUILD / "network.pkl", BUILD / "supply.pkl"):
            h.update(f.read_bytes())
        h.update(repr((ENGINE_REV, DROP_PSI, REQUIRED_PSI, RADIUS_M, BIG_IN, EXACT_BOXES, sorted(FIXED_IDS))).encode())
        self.version = h.hexdigest()[:10]
        print(f"engine ready in {time.time() - t0:.0f} s (version {self.version})", flush=True)

    def _parse_inp(self):
        elev, dem, pipes, src_j = {}, {}, [], set()
        sec = None
        for line in open(INP):
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("["):
                sec = line; continue
            f = line.split()
            if sec == "[JUNCTIONS]" and f[0][0] == "J":
                elev[int(f[0][1:])] = float(f[1]); dem[int(f[0][1:])] = float(f[2])
            elif sec == "[PIPES]":
                if f[0][0] == "P":
                    pipes.append((int(f[0][1:]), int(f[1][1:]), int(f[2][1:]), float(f[3]), float(f[4]), float(f[5])))
                elif f[2][0] == "J":
                    src_j.add(int(f[2][1:]))
            elif sec == "[VALVES]" and f[2][0] == "J":
                src_j.add(int(f[2][1:]))
        nj = len(self.base_h)
        self.elev = np.zeros(nj); self.dem = np.zeros(nj)
        for i, v in elev.items():
            self.elev[i] = v
        for i, v in dem.items():
            self.dem[i] = v
        arr = np.array(pipes)
        self.wp_k, self.wp_a, self.wp_b = arr[:, 0].astype(int), arr[:, 1].astype(int), arr[:, 2].astype(int)
        self.wp_L, self.wp_D, self.wp_C = arr[:, 3], arr[:, 4], arr[:, 5]
        self.is_src = np.zeros(nj, bool)
        self.is_src[list(src_j)] = True
        # pre-rendered INP lines so a window only joins strings
        self.jline = np.array([f"J{i} {self.elev[i]:.2f} {self.dem[i]:.4f}" for i in range(nj)], dtype=object)
        self.pline = np.array([f"P{k} J{a} J{b} {L:.2f} {D:.1f} {C:.0f} 0 " for k, a, b, L, D, C in
                               zip(self.wp_k, self.wp_a, self.wp_b, self.wp_L, self.wp_D, self.wp_C)], dtype=object)

    # ------------------------------------------------------------------ hydraulics
    def _window(self, center, closed_k, emit):
        """Local solve. Returns (junction ids, pressures)."""
        inside = np.zeros(len(self.base_h), bool)
        inside[self.tree_ids[self.tree.query_ball_point(self.node_xy[center], RADIUS_M)]] = True
        ia, ib = inside[self.wp_a], inside[self.wp_b]
        both = ia & ib
        edge = np.zeros_like(inside)
        edge[self.wp_a[ia & ~ib]] = True
        edge[self.wp_b[ib & ~ia]] = True
        edge |= inside & self.is_src
        junc = np.where(inside & ~edge)[0]
        res = np.where(edge)[0]
        if not len(junc):  # piece outside the hydraulic model (unsupplied fragment): no pressure result
            return junc, np.zeros(0)
        closed = np.zeros(len(self.pieces), bool)
        closed[list(closed_k)] = True
        sel = np.where(both)[0]
        status = np.where(closed[self.wp_k[sel]], "Closed", "Open")
        L = ["[JUNCTIONS]", *self.jline[junc]]
        L += ["", "[RESERVOIRS]"] + [f"J{i} {self.base_h[i]:.3f}" for i in res]
        L += ["", "[PIPES]", *(self.pline[sel] + status)]
        L += ["", "[OPTIONS]", "Units GPM", "Headloss H-W", "Trials 200", "Accuracy 0.001", "Demand Model PDA",
              "Minimum Pressure 0", f"Required Pressure {REQUIRED_PSI}", "Pressure Exponent 0.5", "", "[TIMES]",
              "Duration 0", "", "[END]", ""]
        f = self.tmp / f"w{threading.get_ident()}.inp"
        f.write_text("\n".join(L))
        en = ENepanet()
        en.ENopen(str(f), str(f.with_suffix(".rpt")), "")
        if emit is not None and inside[emit[0]] and not edge[emit[0]]:
            en.ENsetnodevalue(en.ENgetnodeindex(f"J{emit[0]}"), EN_EMITTER, emit[1])
        en.ENopenH(); en.ENinitH(0); en.ENrunH()
        pr = np.array([en.ENgetnodevalue(i, EN_PRESSURE) for i in range(1, len(junc) + 1)])  # junctions first, in file order
        en.ENcloseH(); en.ENclose()
        return junc, pr

    def _full(self, closed_k, emit):
        en = self.en
        with self.lock:
            ls = [self.link[k] for k in closed_k if k in self.link]
            for l in ls:
                en.ENsetlinkvalue(l, EN_INITSTATUS, 0)
            if emit and not np.isfinite(self.base_h[emit[0]]):
                emit = None  # break node not in the hydraulic model
            ei = en.ENgetnodeindex(f"J{emit[0]}") if emit else None
            if emit:
                en.ENsetnodevalue(ei, EN_EMITTER, emit[1])
            try:
                en.ENinitH(0); en.ENrunH()
                pr = np.array([en.ENgetnodevalue(int(i) + 1, EN_PRESSURE) for i in self.jpos])
            finally:
                for l in ls:
                    en.ENsetlinkvalue(l, EN_INITSTATUS, 1)
                if emit:
                    en.ENsetnodevalue(ei, EN_EMITTER, 0)
        return self.jnode, pr

    def _gush_out(self, k, closed_k, emit, exact):
        junc, pr = (self._full if exact else lambda c, e: self._window(self.pa[k], c, e))(closed_k, emit)
        out = (self.base_p[junc] - pr) >= DROP_PSI
        return set(junc[out].tolist())

    # ------------------------------------------------------------------ connectivity
    def _downstream(self, s, seg):
        """Segments cut off from every source when segment `seg` is closed.

        From the supply DFS (pipeline/supply.py): the cut-off set is the union of the
        DFS subtrees of seg's children c with low[c] >= disc[seg]."""
        d = self.S[s]["dfs"]
        if d["disc"][seg] < 0:
            return []
        kids = np.where(d["parent"] == seg)[0]
        kids = kids[d["low"][kids] >= d["disc"][seg]]
        if not len(kids):
            return []
        disc = d["disc"]
        m = np.zeros(len(disc), bool)
        for c in kids:
            m |= (disc >= disc[c]) & (disc <= d["fin"][c])
        return np.where(m)[0].tolist()

    def _downstream_bfs(self, s, seg):
        """Reference implementation (BFS) for tests."""
        adj, src = self.sgraph[s], self.src[s]
        seen = {seg}
        q = deque(x for x in src if x != seg)
        seen |= set(q)
        while q:
            v = q.popleft()
            for w in adj[v]:
                if w not in seen:
                    seen.add(w); q.append(w)
        # unreachable now but reachable before: only search near seg (its component in the full graph)
        lost, q2, seen2 = [], deque([seg]), {seg}
        while q2:
            v = q2.popleft()
            for w in adj[v]:
                if w not in seen2:
                    seen2.add(w)
                    if w not in seen and self.S[s]["reached"][w]:  # had supply before, has none now
                        lost.append(w); q2.append(w)
        return lost

    def _pieces_of_junctions(self, js):
        if not js:
            return []
        m = np.zeros(len(self.base_h), bool)
        m[list(js)] = True
        return np.where(m[self.pa] | m[self.pb])[0].tolist()

    # ------------------------------------------------------------------ public
    def run(self, k, opening=0.25, t_first=60, t_dead=90, t_repair=360, exact=False, pressure=True):
        """pressure=False: connectivity only (milliseconds); gushing phases come back with pending=True."""
        t0 = time.time()
        k = int(k)
        lon, lat = self.pieces[k][3][0]
        in_box = any(a <= lon <= c and b <= lat <= d for a, b, c, d in EXACT_BOXES)
        exact = bool(exact or self.diam[k] >= BIG_IN or in_box)
        emit = (int(self.pa[k]), emitter_coeff(self.diam[k], opening))
        cs = {s: int(self.comp[s][k]) for s in self.scens}
        seg_p = self.members["paper"][cs["paper"]]
        segset = set(seg_p)

        def ring(scen):
            """First ring of the paper segment: pieces next to a closable valve, and the dead valve ids."""
            working, dead = [], []
            for q in seg_p:
                for n in (self.pieces[q][1], self.pieces[q][2]):
                    vs = self.cut.get(n)
                    if not vs or all(o in segset for o in self.inc[n]):
                        continue
                    if any(closable(self.valves[v]["attributes"], scen) for v in vs):
                        working.append(q)
                    else:
                        dead += [self.valves[v]["attributes"]["OBJECTID"] for v in vs]
            return working, sorted(set(dead))
        rings = {s: ring(s) for s in self.scens if s != "paper"}
        ring_working, ring_dead = rings["real"]

        gush = self._gush_out(k, [], emit, exact) if pressure else None
        result = dict(piece=k, diameter=float(self.diam[k]), exact=bool(exact), dead_valves=ring_dead,
                      repaired_valves=sorted(set(ring_dead) & FIXED_IDS),
                      params=dict(opening=opening, t_first=t_first, t_dead=t_dead, t_repair=t_repair))
        gd_cache = {}
        for s in self.scens:
            seg_pieces = self.members[s][cs[s]]
            down = self._downstream(s, cs[s])
            iso_pieces = list(seg_pieces) + [q for d in down for q in self.members[s][d]]
            phases = [("gush", t_first, self._pieces_of_junctions(gush) if pressure else None)]
            if s != "paper" and rings[s][1]:
                key = tuple(sorted(rings[s][0]))
                if key not in gd_cache:
                    gd_cache[key] = self._pieces_of_junctions(self._gush_out(k, rings[s][0], emit, exact)) if pressure else None
                phases.append(("gush_dead", t_dead, gd_cache[key]))
            # repair starts once the break is isolated, so a dead valve delays it by t_dead
            phases.append(("isolated", t_repair, iso_pieces))
            rows, ch = [], 0.0
            for name, minutes, pcs in phases:
                if pcs is None:  # pressure not solved yet
                    rows.append(dict(phase=name, minutes=minutes, customers=0, hydrants=0, pieces=[], pending=True))
                    continue
                c = float(self.cust_piece[pcs].sum()) if pcs else 0.0
                ch += c * minutes / 60
                rows.append(dict(phase=name, minutes=minutes, customers=round(c),
                                 hydrants=int(self.hyd_piece[pcs].sum()) if pcs else 0, pieces=pcs))
            result[s] = dict(phases=rows, customer_hours=round(ch),
                             segment_customers=round(float(self.cust_piece[seg_pieces].sum())),
                             downstream_customers=round(float(sum(self.cust_piece[self.members[s][d]].sum() for d in down))))
        result["partial"] = not pressure
        result["solve_ms"] = round((time.time() - t0) * 1000)
        return result


if __name__ == "__main__":
    import json, sys
    e = Engine()
    for k in map(int, sys.argv[1:]):
        for exact in (False, True):
            r = e.run(k, exact=exact)
            brief = lambda s: " | ".join(f"{p['phase']} {p['minutes']}m {p['customers']}c" for p in r[s]["phases"])
            print(f"{k} exact={r['exact']} {r['solve_ms']} ms dead={len(r['dead_valves'])} "
                  f"PAPER {r['paper']['customer_hours']} c-h [{brief('paper')}] REAL {r['real']['customer_hours']} c-h [{brief('real')}]")
