"""Uncontrolled-break state: an orifice leak at the break node, no valves closed yet.

Emitter coefficient from a sharp-edged orifice of the pipe's bore (Cd 0.6) at
55 psi, scaled by the opening fraction. Counts customers newly below 20 psi.
"""
import csv, math, pickle, sys
import numpy as np
from wntr.epanet.toolkit import ENepanet
from hydraulic import BUILD, INP, REQUIRED_PSI, xy

N = pickle.load(open(BUILD / "network.pkl", "rb"))
H = np.load(BUILD / "hydraulic_index.npz")
nodes = H["nodes"]; pieces = N["pieces"]; mains = N["mains"]; cp = N["cust_piece"]
idx = {int(n): i for i, n in enumerate(nodes)}
mids = np.array([xy(*np.asarray(p[3][len(p[3]) // 2]).reshape(2, 1))[0] for p in pieces])
diam = np.array([mains[p[0]].get("DIAMETER") or 0 for p in pieces])
cust_node = np.zeros(len(nodes)); cnt = np.bincount(cp[cp >= 0], minlength=len(pieces))
for k, (_, a, b, _, _) in enumerate(pieces):
    cust_node[idx[a]] += cnt[k] / 2; cust_node[idx[b]] += cnt[k] / 2

en = ENepanet(); en.ENopen(str(INP), str(BUILD / "lt.rpt"), ""); en.ENopenH()
nn = en.ENgetcount(0)
jid = np.array([int(en.ENgetnodeid(i)[1:]) if en.ENgetnodeid(i)[0] == "J" else -1 for i in range(1, nn + 1)])
J = np.where(jid >= 0)[0]; cn = cust_node[jid[J]]

def solve():
    en.ENinitH(0); en.ENrunH()
    return np.array([en.ENgetnodevalue(i, 11) for i in range(1, nn + 1)]), np.array([en.ENgetnodevalue(i, 9) for i in range(1, nn + 1)])

base, _ = solve()
for ev in csv.DictReader(open(BUILD.parent.parent / "validation/news_breaks.csv")):
    if ev["id"] not in sys.argv[1:]: continue
    p = xy([float(ev["lon"])], [float(ev["lat"])])[0]
    d = np.hypot(*(mids - p).T)
    want = float(ev["diameter_in"]) if ev["diameter_in"].replace('.', '').isdigit() else None
    c = np.where((d < 150) & ((diam == want) if want else True))[0]
    k0 = c[np.argmin(d[c])]
    node = en.ENgetnodeindex(f"J{idx[pieces[k0][1]]}")
    D = diam[k0]
    A = math.pi * (D / 12) ** 2 / 4
    q_full = 0.6 * A * math.sqrt(2 * 32.2 * 55 / 0.4335) * 448.83
    for f in (1.0, 0.25, 0.05):
        en.ENsetnodevalue(node, 3, f * q_full / math.sqrt(55))  # EN_EMITTER
        pr, dm = solve()
        en.ENsetnodevalue(node, 3, 0)
        low = (pr[J] < REQUIRED_PSI) & (base[J] >= REQUIRED_PSI)
        print(f"{ev['id']} {D:.0f}in opening {f:.0%}: leak {dm[node - 1] - 0:.0f} gpm, break-node {pr[node - 1]:.0f} psi | "
              f"customers newly <20 psi {cn[low].sum():.0f}; drop>10psi {cn[(base[J] - pr[J]) > 10].sum():.0f}; median drop {np.median(base[J] - pr[J]):.1f} psi"
              f" | reported: {ev['reported_affected_count'] or '-'}")
