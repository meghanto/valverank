"""Citywide batch: one break per paper segment through server.engine (default parameters).

Break location = the segment's largest-diameter piece (ties: longest). Writes
data/build/batch.jsonl, one line per paper segment:
  seg, piece, length_m (segment pipe length, the break-likelihood weight),
  paper_ch, real_ch (customer-hours without water), dead (dead ring valve ids),
  gush, gush_dead (customers below 20 psi in those phases)

  uv run --project pipeline python pipeline/batch.py [workers] [limit]
"""
import json
import multiprocessing as mp
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data" / "build" / "batch.jsonl"
E = None


def init():
    global E
    from server.engine import Engine
    E = Engine()


def one(task):
    seg, k, length = task
    try:
        r = E.run(k)
    except Exception as e:  # keep going; record the failure
        return {"seg": seg, "piece": k, "error": str(e)[:200]}
    ph = {p["phase"]: p["customers"] for p in r["real"]["phases"]}
    return {"seg": seg, "piece": k, "length_m": round(length, 1), "paper_ch": r["paper"]["customer_hours"],
            "real_ch": r["real"]["customer_hours"], "dead": r["dead_valves"], "gush": ph.get("gush", 0),
            "gush_dead": ph.get("gush_dead", 0), "exact": r["exact"], "ms": r["solve_ms"]}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    import pickle
    N = pickle.load(open(ROOT / "data/build/network.pkl", "rb"))
    pieces, mains, seg = N["pieces"], N["mains"], N["seg"]["paper"]
    best, length = {}, defaultdict(float)
    for k, p in enumerate(pieces):
        s = int(seg[k])
        length[s] += p[4]
        key = (float(mains[p[0]].get("DIAMETER") or 0), p[4])
        if s not in best or key > best[s][0]:
            best[s] = (key, k)
    done = set()
    if OUT.exists():
        done = {json.loads(l)["seg"] for l in OUT.read_text().splitlines() if l.strip()}
    tasks = [(s, k, length[s]) for s, (_, k) in best.items() if s not in done]
    # transmission (exact, slow) last so the distribution results land first
    tasks.sort(key=lambda t: float(mains[pieces[t[1]][0]].get("DIAMETER") or 0) >= 24)
    if limit:
        tasks = tasks[:limit]
    print(f"{len(best)} paper segments, {len(done)} done, {len(tasks)} to run on {workers} workers", flush=True)
    t0 = time.time()
    with mp.Pool(workers, initializer=init) as pool, open(OUT, "a") as fh:
        for i, row in enumerate(pool.imap_unordered(one, tasks, chunksize=16)):
            fh.write(json.dumps(row) + "\n")
            if i % 2000 == 0:
                fh.flush()
                el = time.time() - t0
                print(f"{i}/{len(tasks)}  {el / 60:.1f} min  eta {el / max(i, 1) * (len(tasks) - i) / 60:.0f} min", flush=True)
    print("done", (time.time() - t0) / 60, "min")


if __name__ == "__main__":
    main()
