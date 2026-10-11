"""Brute-force check of supply.articulation_loss on the real network.

For sampled segments: remove the segment, BFS from all sources, count
customers no longer reachable (excluding the segment itself). Must equal the
DFS result exactly.
"""
import pickle
from collections import defaultdict, deque

import numpy as np

from supply import BUILD, closable

N = pickle.load(open(BUILD / "network.pkl", "rb"))
S = pickle.load(open(BUILD / "supply.pkl", "rb"))
rng = np.random.default_rng(0)
inc = defaultdict(list)
for k, (_, a, b, _, _) in enumerate(N["pieces"]):
    inc[a].append(k); inc[b].append(k)

for scen in ("paper", "real"):
    r = S[scen]
    comp = np.searchsorted(r["roots"], N["seg"][scen])
    n = len(r["roots"])
    cp = N["cust_piece"]
    cust = np.bincount(comp[cp[cp >= 0]], minlength=n)
    adj = [set() for _ in range(n)]
    for node, vs in N["cut_valves"].items():
        if any(closable(N["valves"][v]["attributes"], scen) for v in vs):
            segs = {int(comp[k]) for k in inc.get(node, [])}
            for a in segs:
                adj[a] |= segs - {a}
    src = set(r["sources"])

    def reach(removed):
        seen = np.zeros(n, bool)
        q = deque(s for s in src if s != removed)
        for s in q:
            seen[s] = True
        while q:
            v = q.popleft()
            for w in adj[v]:
                if w != removed and not seen[w]:
                    seen[w] = True; q.append(w)
        return seen

    base = reach(-1)
    with_loss = np.where(r["lost_cust"] > 0)[0]
    sample = list(rng.choice(with_loss, 15, replace=False)) + list(rng.choice(n, 15, replace=False)) + [int(np.argmax(r["lost_cust"]))]
    bad = 0
    for v in sample:
        seen = reach(v)
        brute = int(cust[base & ~seen].sum() - (cust[v] if base[v] else 0))
        if brute != int(r["lost_cust"][v]):
            bad += 1
            print(f"  MISMATCH {scen} seg {v}: dfs {int(r['lost_cust'][v])} brute {brute}")
    print(f"{scen}: {len(sample) - bad}/{len(sample)} match")
