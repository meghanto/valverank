"""Break timeline simulation on the full-city EPANET model.

A break runs through phases, each one steady-state solve:

  gush       break open, nothing closed                     for t_first minutes
  then, if every valve around the break works (paper):
  isolated   paper segment closed                           until t_repair
  if the City's records show a dead valve in that ring (real):
  gush_dead  working ring valves closed, dead one open, still gushing   for t_dead minutes
  isolated   the larger real segment closed                 until t_repair

Without water = junction pressure < REQUIRED_PSI (and >= it in the baseline).
Customer-hours = sum over phases of customers without water x phase hours.
Times and break size are assumptions exposed as parameters (UI sliders).
"""
import pickle
import time
from collections import defaultdict

import numpy as np
from wntr.epanet.toolkit import ENepanet

from hydraulic import BUILD, INP, PSI_PER_FT, REQUIRED_PSI

EN_EMITTER, EN_INITSTATUS, EN_DEMAND, EN_PRESSURE = 3, 4, 9, 11


def closable(a, scen):
    if a.get("NORMALPOSITION") == 0:
        return True
    return not (scen == "real" and a.get("CONDITION") == "INOP")


class Sim:
    def __init__(self, inp=INP):
        t = time.time()
        self.N = N = pickle.load(open(BUILD / "network.pkl", "rb"))
        H = np.load(BUILD / "hydraulic_index.npz")
        self.pieces, self.mains, self.seg = N["pieces"], N["mains"], N["seg"]
        nodes = H["nodes"]
        self.idx = {int(n): i for i, n in enumerate(nodes)}
        self.en = en = ENepanet()
        en.ENopen(str(inp), str(BUILD / "sim.rpt"), "")
        en.ENopenH()
        self.nn = en.ENgetcount(0)
        ids = [en.ENgetnodeid(i) for i in range(1, self.nn + 1)]
        self.jpos = np.array([i for i, s in enumerate(ids) if s[0] == "J"])      # EPANET index-1 of junctions
        self.jnode = np.array([int(ids[i][1:]) for i in self.jpos])              # -> hydraulic node index
        self.link = {}
        for k in range(len(self.pieces)):
            try:
                self.link[k] = en.ENgetlinkindex(f"P{k}")
            except Exception:
                pass
        # customers per hydraulic node
        cp = N["cust_piece"]
        cnt = np.bincount(cp[cp >= 0], minlength=len(self.pieces))
        self.cust_node = np.zeros(len(nodes))
        for k, (_, a, b, _, _) in enumerate(self.pieces):
            self.cust_node[self.idx[a]] += cnt[k] / 2
            self.cust_node[self.idx[b]] += cnt[k] / 2
        self.jcust = self.cust_node[self.jnode]
        # segment membership and boundary valve nodes
        self.members = {s: defaultdict(list) for s in ("paper", "real")}
        for s in ("paper", "real"):
            for k, r in enumerate(self.seg[s]):
                self.members[s][int(r)].append(k)
        self.inc = defaultdict(list)
        for k, (_, a, b, _, _) in enumerate(self.pieces):
            self.inc[a].append(k); self.inc[b].append(k)
        self.base = self._solve()
        print(f"Sim ready in {time.time() - t:.0f} s; junctions {len(self.jpos)}")

    def _solve(self):
        en = self.en
        en.ENinitH(0); en.ENrunH()
        return np.array([en.ENgetnodevalue(int(i) + 1, EN_PRESSURE) for i in self.jpos])

    def _with(self, closed=(), emit=None):
        en = self.en
        ls = [self.link[k] for k in closed if k in self.link]
        for l in ls:
            en.ENsetlinkvalue(l, EN_INITSTATUS, 0)
        if emit:
            en.ENsetnodevalue(emit[0], EN_EMITTER, emit[1])
        try:
            return self._solve()
        finally:
            for l in ls:
                en.ENsetlinkvalue(l, EN_INITSTATUS, 1)
            if emit:
                en.ENsetnodevalue(emit[0], EN_EMITTER, 0)

    def _out(self, p):
        """Junctions without water: newly below the threshold."""
        return (p < REQUIRED_PSI) & (self.base >= REQUIRED_PSI)

    def run(self, k, opening=0.25, t_first=60, t_dead=90, t_repair=360):
        pieces, valves, cut = self.pieces, self.N["valves"], self.N["cut_valves"]
        diam = float(self.mains[pieces[k][0]].get("DIAMETER") or 8)
        a_node = self.idx[pieces[k][1]]
        emit_node = self.en.ENgetnodeindex(f"J{a_node}")
        area = np.pi * (diam / 12) ** 2 / 4
        coeff = opening * 0.6 * area * np.sqrt(2 * 32.2 * 55 / PSI_PER_FT) * 448.83 / np.sqrt(55)
        emit = (emit_node, coeff)

        sp = self.members["paper"][int(self.seg["paper"][k])]
        sr = self.members["real"][int(self.seg["real"][k])]
        # paper ring: boundary nodes of the paper segment that carry a valve
        sp_set = set(sp)
        ring_working, ring_dead = [], []
        for q in sp:
            for n in (pieces[q][1], pieces[q][2]):
                vs = cut.get(n)
                if not vs or all(o in sp_set for o in self.inc[n]):
                    continue
                (ring_working if any(closable(valves[v]["attributes"], "real") for v in vs) else ring_dead).append((n, q))
        dead = len(ring_dead) > 0

        t0 = time.time()
        phases = []
        p_gush = self._with(emit=emit)
        phases.append(("gush", t_first, p_gush))
        p_iso_paper = self._with(closed=sp)
        timeline = {"paper": [("gush", t_first, p_gush), ("isolated", t_repair, p_iso_paper)]}
        if dead:
            # close the paper-segment pipes at working ring valves; dead-valve connections stay open
            near_working = {q for n, q in ring_working}
            p_gd = self._with(closed=near_working, emit=emit)
            p_iso_real = self._with(closed=sr)
            timeline["real"] = [("gush", t_first, p_gush), ("gush_dead", t_dead, p_gd),
                                ("isolated", max(t_repair - t_dead, 0), p_iso_real)]
        else:
            timeline["real"] = timeline["paper"]
        solve_s = time.time() - t0

        out = {"piece": k, "diameter": diam, "dead_valves_in_ring": len(ring_dead), "solve_s": round(solve_s, 1),
               "params": dict(opening=opening, t_first=t_first, t_dead=t_dead, t_repair=t_repair)}
        for scen, ph in timeline.items():
            rows, ch = [], 0.0
            for name, minutes, p in ph:
                o = self._out(p)
                c = float(self.jcust[o].sum())
                ch += c * minutes / 60
                rows.append(dict(phase=name, minutes=minutes, customers_out=round(c), junctions_out=int(o.sum()),
                                 out_nodes=self.jnode[o].tolist()))
            out[scen] = dict(phases=rows, customer_hours=round(ch))
        return out


if __name__ == "__main__":
    import sys
    sim = Sim()
    rng = np.random.default_rng(0)
    for k in map(int, sys.argv[1:] or rng.choice(len(sim.pieces), 5)):
        r = sim.run(k)
        def brief(s):
            return " | ".join(f"{p['phase']} {p['minutes']}m: {p['customers_out']}" for p in r[s]["phases"])
        print(f"piece {k} ({r['diameter']:.0f}in, dead in ring {r['dead_valves_in_ring']}, {r['solve_s']}s) "
              f"PAPER {r['paper']['customer_hours']} cust-h [{brief('paper')}]  REAL {r['real']['customer_hours']} cust-h [{brief('real')}]")
