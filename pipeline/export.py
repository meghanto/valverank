"""Export the demo area and citywide stats for the web app.

Writes web/public/data/{pipes.geojson, valves.geojson, hydrants.geojson,
segments.json, stats.json}. Segment ids are remapped to compact ints per scenario.
"""
import datetime as dt
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BUILD, OUT = ROOT / "data" / "build", ROOT / "web" / "public" / "data"

# NW + central Houston: includes Tidwell & Antoine (29.857, -95.495), Heights, First Ward
BBOX = (-95.56, 29.73, -95.33, 29.90)
NOW = dt.datetime(2026, 10, 10, tzinfo=dt.UTC)


def year(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.UTC).year if ms else None


def in_bbox(lon, lat):
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


def r5(c):
    return [round(c[0], 5), round(c[1], 5)]


def main():
    N = pickle.load(open(BUILD / "network.pkl", "rb"))
    pieces, seg, valves, mains = N["pieces"], N["seg"], N["valves"], N["mains"]
    cust_piece, hyd_piece, hyd = N["cust_piece"], N["hyd_piece"], N["hyd"]
    cut_valves = N["cut_valves"]
    L = np.array([p[4] for p in pieces])
    OUT.mkdir(parents=True, exist_ok=True)

    # node -> pieces
    inc = defaultdict(list)
    for k, (_, a, b, _, _) in enumerate(pieces):
        inc[a].append(k)
        inc[b].append(k)

    def closable(vi, scen):
        a = valves[vi]["attributes"]
        if a.get("NORMALPOSITION") == 0:
            return True
        return not (scen == "real" and a.get("CONDITION") == "INOP")

    # ---------- per-segment aggregates (citywide) ----------
    agg = {}
    for scen in ("paper", "real"):
        s = seg[scen]
        cust = np.bincount(s[cust_piece[cust_piece >= 0]], minlength=len(pieces))
        hydc = np.bincount(s[hyd_piece[hyd_piece >= 0]], minlength=len(pieces))
        length = np.bincount(s, weights=L, minlength=len(pieces))
        agg[scen] = dict(cust=cust, hyd=hydc, length=length)
    # downstream supply loss (pipeline/supply.py), indexed like cust: by segment root
    S = pickle.load(open(BUILD / "supply.pkl", "rb"))
    for scen in ("paper", "real"):
        down, downh = np.zeros(len(pieces)), np.zeros(len(pieces))
        down[S[scen]["roots"]] = S[scen]["lost_cust"]
        downh[S[scen]["roots"]] = S[scen]["lost_hyd"]
        agg[scen]["down"], agg[scen]["downh"] = down, downh

    # volume drained when a segment is emptied (gal): pi r^2 L, diameter in inches
    diam_in = np.array([float(mains[p[0]].get("DIAMETER") or 0) for p in pieces])
    vol_gal = np.pi * (diam_in * 0.0254 / 2) ** 2 * L * 264.172
    for scen in ("paper", "real"):
        agg[scen]["vol"] = np.bincount(seg[scen], weights=vol_gal, minlength=len(pieces))

    # boundary valves per segment and "dead valves" inside the real segment
    bound = {scen: defaultdict(set) for scen in ("paper", "real")}
    dead_inside = defaultdict(set)
    for n, vs in cut_valves.items():
        ks = inc.get(n, [])
        for scen in ("paper", "real"):
            if any(closable(v, scen) for v in vs):
                for k in ks:
                    for v in vs:
                        if closable(v, scen):
                            bound[scen][seg[scen][k]].add(v)
            elif scen == "real":
                for k in ks:
                    for v in vs:
                        dead_inside[seg["real"][k]].add(v)

    # ---------- demo-area selection ----------
    def mid(ll):
        return ll[len(ll) // 2]

    sel = [k for k, p in enumerate(pieces) if in_bbox(*mid(p[3]))]
    sel_set = set(sel)
    # include whole segments that touch the bbox so outages render completely
    for scen in ("paper", "real"):
        touch = {seg[scen][k] for k in sel}
        sel_set |= {k for k in range(len(pieces)) if seg[scen][k] in touch}
    sel = sorted(sel_set)
    print("demo pieces:", len(sel))

    remap = {scen: {} for scen in ("paper", "real")}

    def rid(scen, s):
        m = remap[scen]
        if s not in m:
            m[s] = len(m)
        return m[s]

    feats = []
    for k in sel:
        mi = pieces[k][0]
        a = mains[mi]
        feats.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [r5(c) for c in pieces[k][3]]},
            "properties": {
                "k": k,
                "sp": rid("paper", seg["paper"][k]),
                "sr": rid("real", seg["real"][k]),
                "d": a.get("DIAMETER"),
                "m": a.get("MATERIAL"),
                "y": year(a.get("INSERVICEDATE")),
            },
        })
    (OUT / "pipes.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))

    # segments.json: per compact id -> [customers, hydrants, length_m, gallons, [valve ids], [dead valve ids],
    #                                   downstream customers, downstream hydrants]
    segs = {}
    for scen in ("paper", "real"):
        out = []
        inv = sorted(remap[scen].items(), key=lambda kv: kv[1])
        for s, _ in inv:
            g = agg[scen]
            out.append([
                int(g["cust"][s]), int(g["hyd"][s]), round(float(g["length"][s])), round(float(g["vol"][s])),
                sorted(valves[v]["attributes"]["OBJECTID"] for v in bound[scen].get(s, ())),
                sorted(valves[v]["attributes"]["OBJECTID"] for v in dead_inside.get(s, ())) if scen == "real" else [],
                int(g["down"][s]), int(g["downh"][s]),
            ])
        segs[scen] = out
    (OUT / "segments.json").write_text(json.dumps(segs, separators=(",", ":")))

    # valves on mains in demo area
    vf = []
    for vi, (kind, _, _) in N["valve_place"].items():
        if kind not in ("node", "pipe"):
            continue
        v = valves[vi]
        g, a = v["geometry"], v["attributes"]
        if not in_bbox(g["x"], g["y"]):
            continue
        cy = year(a.get("CONDITIONDATE"))
        vf.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": r5([g["x"], g["y"]])},
            "properties": {
                "id": a["OBJECTID"],
                "c": a.get("CONDITION") or "UNK",
                "r": a.get("REASON_INOPERABLE"),
                "cy": cy,
                "d": a.get("DIAMETER"),
                "iy": year(a.get("INSERVICEDATE")),
            },
        })
    (OUT / "valves.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": vf}, separators=(",", ":")))

    hf = []
    for i, h in enumerate(hyd):
        g = h.get("geometry")
        k = int(hyd_piece[i])
        if g and in_bbox(g["x"], g["y"]) and k >= 0 and seg["paper"][k] in remap["paper"]:
            hf.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": r5([g["x"], g["y"]])},
                       "properties": {"sp": remap["paper"][seg["paper"][k]], "sr": remap["real"][seg["real"][k]]}})
    (OUT / "hydrants.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": hf}, separators=(",", ":")))

    # ---------- citywide stats ----------
    w = L / L.sum()
    st = {}
    for scen in ("paper", "real"):
        s = seg[scen]
        st[scen] = dict(
            segments=int(len(np.unique(s))),
            expected_customers_per_break=round(float(np.sum(agg[scen]["cust"][s] * w)), 1),
            expected_customers_per_break_with_downstream=round(float(np.sum((agg[scen]["cust"][s] + agg[scen]["down"][s]) * w)), 1),
            share_pipe_length_with_downstream_loss=round(float(np.sum(w * (agg[scen]["down"][s] > 0))), 3),
            max_customers_with_downstream=int((agg[scen]["cust"] + agg[scen]["down"]).max()),
            expected_hydrants_per_break=round(float(np.sum(agg[scen]["hyd"][s] * w)), 2),
            expected_gallons_drained=round(float(np.sum(agg[scen]["vol"][s] * w))),
            max_customers=int(agg[scen]["cust"].max()),
        )
    cp, cr = agg["paper"]["cust"][seg["paper"]], agg["real"]["cust"][seg["real"]]
    st["share_pipes_real_gt_paper"] = round(float(np.sum(w * (cr > cp))), 3)
    st["share_pipes_real_gt_2x"] = round(float(np.sum(w * (cr > 2 * cp + 1))), 3)
    st["valves_total"] = len(valves)
    st["valves_inop"] = sum(1 for v in valves if v["attributes"].get("CONDITION") == "INOP")
    st["valves_on_mains"] = sum(1 for k, _, _ in N["valve_place"].values() if k in ("node", "pipe"))
    st["valves_on_mains_inop"] = sum(
        1 for vi, (k, _, _) in N["valve_place"].items() if k in ("node", "pipe") and valves[vi]["attributes"].get("CONDITION") == "INOP")
    ages = [(NOW - dt.datetime.fromtimestamp(valves[vi]["attributes"]["CONDITIONDATE"] / 1000, dt.UTC)).days / 365.25
            for vi, (k, _, _) in N["valve_place"].items() if k in ("node", "pipe") and valves[vi]["attributes"].get("CONDITIONDATE")]
    st["valves_on_mains_last_inspected_5y_plus_share"] = round(float(np.mean(np.array(ages) >= 5)), 3)
    st["data_snapshot"] = "City of Houston public GIS, last edited 2023-06-05"
    st["demo_bbox"] = BBOX
    (OUT / "stats.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    for f in OUT.iterdir():
        print(f.name, f"{f.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
