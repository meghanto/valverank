"""Close the real-scenario segment at a news-reported break and compare pressures to baseline."""
import csv, math, pickle, sys, time
import numpy as np
from wntr.epanet.toolkit import ENepanet
from hydraulic import BUILD, INP, REQUIRED_PSI, xy

N = pickle.load(open(BUILD / "network.pkl", "rb"))
H = np.load(BUILD / "hydraulic_index.npz")
nodes = H["nodes"]; pieces = N["pieces"]; mains = N["mains"]; cp = N["cust_piece"]
mids = np.array([xy(*np.asarray(p[3][len(p[3]) // 2]).reshape(2, 1))[0] for p in pieces])
diam = np.array([mains[p[0]].get("DIAMETER") or 0 for p in pieces])
cust_node = np.zeros(len(nodes))
idx = {int(n): i for i, n in enumerate(nodes)}
cnt = np.bincount(cp[cp >= 0], minlength=len(pieces))
for k, (_, a, b, _, _) in enumerate(pieces):
    cust_node[idx[a]] += cnt[k] / 2; cust_node[idx[b]] += cnt[k] / 2

en = ENepanet(); en.ENopen(str(INP), str(BUILD / "bt.rpt"), ""); en.ENopenH()
nn = en.ENgetcount(0); nl = en.ENgetcount(2)
jid = np.array([int(en.ENgetnodeid(i)[1:]) if en.ENgetnodeid(i)[0] == "J" else -1 for i in range(1, nn + 1)])
def link(k):
    try:
        return en.ENgetlinkindex(f"P{k}")
    except Exception:  # piece dropped (zero length or unconnected)
        return None

def solve():
    en.ENinitH(0); en.ENrunH()
    return np.array([en.ENgetnodevalue(i, 11) for i in range(1, nn + 1)])

base = solve()
J = jid >= 0
for ev in csv.DictReader(open(BUILD.parent.parent / "validation/news_breaks.csv")):
    if ev["id"] not in sys.argv[1:]: continue
    p = xy([float(ev["lon"])], [float(ev["lat"])])[0]
    d = np.hypot(*(mids - p).T)
    want = float(ev["diameter_in"]) if ev["diameter_in"].replace('.', '').isdigit() else None
    c = np.where((d < 150) & ((diam == want) if want else True))[0]
    k0 = c[np.argmin(d[c])]
    for scen in ("paper", "real"):
        seg = N["seg"][scen]; ks = np.where(seg == seg[k0])[0]
        closed = [l for l in map(link, ks) if l]
        for l in closed: en.ENsetlinkvalue(l, 4, 0)  # EN_INITSTATUS closed
        t = time.time(); pr = solve(); dt = time.time() - t
        for l in closed: en.ENsetlinkvalue(l, 4, 1)
        inside = set()
        for k in ks: inside |= {idx[pieces[k][1]], idx[pieces[k][2]]}
        jn = np.where(J)[0]; cn = cust_node[jid[jn]]
        ins = np.isin(jid[jn], list(inside))
        low = (pr[jn] < REQUIRED_PSI) & (base[jn] >= REQUIRED_PSI) & ~ins
        drop = base[jn] - pr[jn]
        print(f"{ev['id']} {scen}: closed {len(closed)} pipes ({diam[k0]:.0f}in main), solve {dt:.1f}s | "
              f"customers in segment {cn[ins].sum():.0f}; outside segment <{REQUIRED_PSI:.0f} psi: {low.sum()} nodes / {cn[low].sum():.0f} customers; "
              f"drop>5psi {cn[(drop > 5) & ~ins].sum():.0f} cust, drop>1psi {cn[(drop > 1) & ~ins].sum():.0f} cust, max drop outside {drop[~ins].max():.1f} psi")
