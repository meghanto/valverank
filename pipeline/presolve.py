"""Presolve every break that needs a full-city solve (mains >= 24 in, Kingwood) at default assumptions.

Writes gzip JSON results (same encoding and key as the API) to $H2O_CACHE_DIR/<engine version>/,
which the API serves before solving. Sharded so several machines can split the work:

  uv run --project pipeline python pipeline/presolve.py SHARD NSHARDS WORKERS [OUT_DIR]

Resumable: existing files are skipped.
"""
import gzip
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
E = None
OUT = None


def init(out):
    global E, OUT
    from server.engine import Engine
    E = Engine()
    OUT = Path(out) / E.version
    OUT.mkdir(parents=True, exist_ok=True)


def one(k):
    from server.app import run_key
    from server.codec import encode
    key = run_key(E.version, k)
    f = OUT / (key.replace(":", "_") + ".json.gz")
    if f.exists():
        return 0
    t = time.time()
    r = encode(E.run(k), len(E.pieces))
    tmp = f.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(json.dumps(r, separators=(",", ":")).encode(), 6))
    tmp.rename(f)
    return time.time() - t


def tasks():
    import pickle
    import numpy as np
    from server.engine import BIG_IN, EXACT_BOXES
    N = pickle.load(open(ROOT / "data/build/network.pkl", "rb"))
    out = []
    for k, p in enumerate(N["pieces"]):
        d = float(N["mains"][p[0]].get("DIAMETER") or 8)
        lon, lat = p[3][0]
        if d >= BIG_IN or any(a <= lon <= c and b <= lat <= dd for a, b, c, dd in EXACT_BOXES):
            out.append(k)
    return out


def main():
    shard, nshards, workers = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    out = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("H2O_CACHE_DIR", str(ROOT / "data/build/cache"))
    todo = tasks()[shard::nshards]
    print(f"shard {shard}/{nshards}: {len(todo)} pieces on {workers} workers -> {out}", flush=True)
    t0, done = time.time(), 0
    with mp.Pool(workers, initializer=init, initargs=(out,)) as pool:
        for i, dt in enumerate(pool.imap_unordered(one, todo, chunksize=4)):
            done += dt > 0
            if i % 200 == 0:
                el = time.time() - t0
                print(f"{i}/{len(todo)} {el / 60:.1f} min eta {el / max(i, 1) * (len(todo) - i) / 60:.0f} min", flush=True)
    print(f"done {done} new in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
