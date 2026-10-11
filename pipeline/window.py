"""Local-window hydraulic solve around a break, checked against the full-city solve.

Window = every junction within RADIUS_M of the break. Junctions on the window
edge (touching a pipe that leaves the window) become fixed-head reservoirs at
their baseline head. This is the method the browser uses (epanet-js), so its
accuracy is measured here first.

Usage: uv run python window.py [n_breaks] [radius_m]
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np
from wntr.epanet.toolkit import ENepanet

from hydraulic import BUILD, INP, REQUIRED_PSI, PSI_PER_FT

EMIT_FRACTION = 0.25  # break opening as a share of the full bore (assumption, also a UI slider)


def load_full():
    """Parse houston.inp once into arrays."""
    J, R, P, V = {}, {}, [], []
    sec = None
    for line in open(INP):
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("["):
            sec = line
            continue
        f = line.split()
        if sec == "[JUNCTIONS]":
            J[f[0]] = (float(f[1]), float(f[2]))
        elif sec == "[RESERVOIRS]":
            R[f[0]] = float(f[1])
        elif sec == "[PIPES]":
            P.append((f[0], f[1], f[2], float(f[3]), float(f[4]), float(f[5]), f[7]))
        elif sec == "[VALVES]":
            V.append(f)
    return J, R, P, V


def solve_inp(text, path, emit=None):
    path.write_text(text)
    en = ENepanet()
    en.ENopen(str(path), str(path.with_suffix(".rpt")), "")
    if emit:
        en.ENsetnodevalue(en.ENgetnodeindex(emit[0]), 3, emit[1])
    en.ENopenH(); en.ENinitH(0); en.ENrunH()
    n = en.ENgetcount(0)
    out = {en.ENgetnodeid(i): en.ENgetnodevalue(i, 11) for i in range(1, n + 1)}
    en.ENcloseH(); en.ENclose()
    return out


def emitter_coeff(diam_in, frac=EMIT_FRACTION, p_ref=55.0):
    a = np.pi * (diam_in / 12) ** 2 / 4
    q = 0.6 * a * np.sqrt(2 * 32.2 * p_ref / PSI_PER_FT) * 448.83
    return frac * q / np.sqrt(p_ref)


def main():
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    radius = float(sys.argv[2]) if len(sys.argv) > 2 else 2000.0
    J, R, P, V = load_full()
    H = np.load(BUILD / "hydraulic_index.npz")
    N = pickle.load(open(BUILD / "network.pkl", "rb"))
    nodes = H["nodes"]
    # junction coordinates (metres) for window selection
    coord = {}
    for p in N["pieces"]:
        coord.setdefault(p[1], p[3][0]); coord.setdefault(p[2], p[3][-1])
    from hydraulic import xy
    jxy = {}
    for i, n in enumerate(nodes):
        c = coord[int(n)]
        jxy[f"J{i}"] = xy([c[0]], [c[1]])[0]

    # baseline full solve: heads
    en = ENepanet(); en.ENopen(str(INP), str(BUILD / "w.rpt"), ""); en.ENopenH()
    en.ENinitH(0); en.ENrunH()
    nn = en.ENgetcount(0)
    ids = [en.ENgetnodeid(i) for i in range(1, nn + 1)]
    base_p = {s: en.ENgetnodevalue(i + 1, 11) for i, s in enumerate(ids)}
    base_h = {s: en.ENgetnodevalue(i + 1, 10) for i, s in enumerate(ids)}  # EN_HEAD
    pipes = [p for p in P if p[0].startswith("P")]
    # junctions fed by a source link (reservoir connector or FCV): pin them to baseline head
    src_j = {p[2] for p in P if not p[0].startswith("P") and p[2].startswith("J")}
    src_j |= {v[2] for v in V if v[2].startswith("J")}
    pdiam = {p[0]: p[4] for p in pipes}
    rng = np.random.default_rng(1)
    picks = rng.choice(len(pipes), nb, replace=False)
    tmp = BUILD / "win.inp"
    errs, times, lows = [], [], []
    for pi in picks:
        pid, a, b, L, d, c, st = pipes[pi]
        if d >= 24:
            continue  # transmission breaks use the full model
        brk = a
        cx = jxy[brk]
        inside = {j for j, q in jxy.items() if j in J and np.hypot(*(q - cx)) <= radius}
        lines_j, lines_r, lines_p = [], [], []
        edge = set()
        win_pipes = []
        for p in pipes:
            ia, ib = p[1] in inside, p[2] in inside
            if ia and ib:
                win_pipes.append(p)
            elif ia or ib:
                edge.add(p[1] if ia else p[2])
        edge |= inside & src_j
        for j in inside - edge:
            lines_j.append(f"{j} {J[j][0]:.2f} {J[j][1]:.4f}")
        for j in edge:  # boundary: fixed head from baseline
            lines_r.append(f"{j} {base_h[j]:.3f}")
        for p in win_pipes:
            lines_p.append(f"{p[0]} {p[1]} {p[2]} {p[3]:.2f} {p[4]:.1f} {p[5]:.0f} 0 Open")
        # sources inside the window keep their reservoirs/valves out: boundary heads already carry them
        text = "\n".join(["[JUNCTIONS]"] + lines_j + ["", "[RESERVOIRS]"] + lines_r + ["", "[PIPES]"] + lines_p +
                         ["", "[OPTIONS]", "Units GPM", "Headloss H-W", "Trials 200", "Accuracy 0.001",
                          "Demand Model PDA", "Minimum Pressure 0", f"Required Pressure {REQUIRED_PSI}",
                          "Pressure Exponent 0.5", "", "[TIMES]", "Duration 0", "", "[END]", ""])
        if brk in edge:
            continue
        coeff = emitter_coeff(d)
        t = time.time()
        loc = solve_inp(text, tmp, (brk, coeff))
        dt = time.time() - t
        en.ENsetnodevalue(en.ENgetnodeindex(brk), 3, coeff)
        en.ENinitH(0); en.ENrunH()
        full = {s: en.ENgetnodevalue(i + 1, 11) for i, s in enumerate(ids) if s in loc and s not in edge}
        en.ENsetnodevalue(en.ENgetnodeindex(brk), 3, 0)
        e = np.array([abs(loc[s] - full[s]) for s in full])
        drop = np.array([base_p[s] - full[s] for s in full])
        errs.append((e.max(), np.percentile(e, 95), drop.max()))
        times.append(dt)
        lows.append(len(inside))
    errs = np.array(errs)
    print(f"radius {radius:.0f} m, {len(errs)} distribution breaks; window junctions median {np.median(lows):.0f}")
    print(f"local solve time median {np.median(times) * 1000:.0f} ms (incl. file write)")
    print(f"abs error vs full solve, psi: max-per-break median {np.median(errs[:, 0]):.2f}, worst {errs[:, 0].max():.2f}; "
          f"p95-per-break median {np.median(errs[:, 1]):.3f}")
    print(f"max pressure drop at break (full solve) median {np.median(errs[:, 2]):.1f} psi")
    worst = np.argsort(-errs[:, 0])[:3]
    print("worst cases (max err, p95 err, max drop):", errs[worst].round(2).tolist())


if __name__ == "__main__":
    main()
