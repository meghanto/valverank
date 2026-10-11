"""Third scenario 'fixed': the City's records, after repairing the planner's top N dead valves.

Reads web/public/data/repair.json (planner order), marks the top N valves as working,
re-runs the segmentation rule (network.py) and the supply-loss pass (supply.py) on a copy
of the network, and writes data/build/fixed/{ids.json, seg.npy, supply.pkl}. server/engine.py
loads these as scenario 'fixed' when present. Nothing in data/build itself is modified.

  uv run --project pipeline python pipeline/fixed.py [N=100]
"""
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "data" / "build"
OUT = BUILD / "fixed"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    OUT.mkdir(exist_ok=True)
    ids = [v["id"] for v in json.loads((ROOT / "web/public/data/repair.json").read_text())["valves"][:n]]
    N = pickle.load(open(BUILD / "network.pkl", "rb"))
    vi_of = {v["attributes"]["OBJECTID"]: i for i, v in enumerate(N["valves"])}
    for oid in ids:
        N["valves"][vi_of[oid]]["attributes"]["CONDITION"] = "GOOD"  # repaired

    # segmentation, same rule as network.py ('real' on the repaired valve set)
    sys.path.insert(0, str(ROOT))
    from server.engine import closable
    pieces, cut = N["pieces"], N["cut_valves"]
    inc = defaultdict(list)
    for k, (_, a, b, _, _) in enumerate(pieces):
        inc[a].append(k); inc[b].append(k)
    par = list(range(len(pieces)))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for node, ks in inc.items():
        vs = cut.get(node)
        if vs and any(closable(N["valves"][v]["attributes"], "real") for v in vs):
            continue
        for k in ks[1:]:
            a, b = find(ks[0]), find(k)
            if a != b:
                par[a] = b
    seg = np.array([find(k) for k in range(len(pieces))])
    print(f"top {n} repaired: real segments {len(np.unique(N['seg']['real']))} -> {len(np.unique(seg))}")
    N["seg"]["real"] = seg

    # supply loss on the repaired network (supply.py reads BUILD/network.pkl and writes BUILD/supply.pkl)
    tmp = OUT / "tmp"
    tmp.mkdir(exist_ok=True)
    pickle.dump(N, open(tmp / "network.pkl", "wb"))
    sys.path.insert(0, str(ROOT / "pipeline"))
    import supply
    supply.BUILD = tmp
    supply.main()
    S = pickle.load(open(tmp / "supply.pkl", "rb"))
    pickle.dump(S["real"], open(OUT / "supply.pkl", "wb"))
    np.save(OUT / "seg.npy", seg)
    (OUT / "ids.json").write_text(json.dumps(ids))
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
