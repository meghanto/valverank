"""Numbers behind validation/data_audit_extra.md. Deterministic (seed 7); reads data/raw only,
except the date calibration, which queries the City's live HPW odor-request layer.

Usage: uv run --project pipeline python pipeline/audit_extra.py
"""
import collections
import datetime as dt
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from ingest import post
from network import HYDRANT_VALVE_SUBTYPE, LEAD_USE, xy

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
ODOR = "https://geohwp.houstontx.gov/arcgis/rest/services/04_BaseData_Operations/SSO_Stoppages_Odor/FeatureServer/8"
BBOX = (-95.9, -95.0, 29.5, 30.2)
URI_START = dt.datetime(2021, 2, 14, 6, tzinfo=dt.timezone.utc)  # midnight CST, Feb 14 2021
R = 150.0  # m, neighbourhood radius for the density-controlled INOP share
rng = np.random.default_rng(7)
load = lambda n: json.loads((RAW / n).read_text())
day = lambda ms: dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def in_bbox(lon, lat):
    return (lon > BBOX[0]) & (lon < BBOX[1]) & (lat > BBOX[2]) & (lat < BBOX[3])


def coords(feats, xk="x", yk="y"):
    keep = [f for f in feats if f.get("geometry") and f["geometry"].get(xk) is not None]
    return keep, np.array([f["geometry"][xk] for f in keep]), np.array([f["geometry"][yk] for f in keep])


def section(t):
    print(f"\n=== {t}")


# ---------------------------------------------------------------- 311: profile
section("311 profile")
uri = load("uri311.json")
A = [f["attributes"] for f in uri]
print("records", len(A), "| no geometry", sum(not f.get("geometry") for f in uri))
print("Issue", collections.Counter(a["Issue"] for a in A).most_common())
print("Status x Addr_type", collections.Counter((a["Status"], a["Addr_type"]) for a in A))
print("Issue of ungeocoded", collections.Counter(a["Issue"] for f, a in zip(uri, A) if not f.get("geometry")))
print("city", collections.Counter(a["city"] for a in A).most_common(8))
print("duplicate CASE_NUMBE", len(A) - len({a["CASE_NUMBE"] for a in A}))
geo, lon, lat = coords(uri)
print("extent lon", lon.min().round(4), lon.max().round(4), "lat", lat.min().round(4), lat.max().round(4),
      "| in bbox", f"{in_bbox(lon, lat).mean():.4f}")
cc = collections.Counter(zip(lon.round(6), lat.round(6)))
print("distinct coords", len(cc), "| coords shared by >1 record", sum(v > 1 for v in cc.values()),
      "| records on shared coords", sum(v for v in cc.values() if v > 1), "| max stack", max(cc.values()))
ci = collections.Counter(zip(lon.round(6), lat.round(6), (f["attributes"]["Issue"] for f in geo)))
print("extra records with same coord+Issue", sum(v - 1 for v in ci.values() if v > 1))
P = xy(lon, lat)
ch = xy([-95.3693], [29.7604])[0]  # Houston City Hall, 901 Bagby
print("records within 50 m of City Hall", int((np.hypot(*(P - ch).T) < 50).sum()))

# ---------------------------------------------------------------- 311: dates from case-number prefix
section("311 date range (HPW request-id calibration)")
pre = np.array([a["CASE_NUMBE"].split("-")[0] for a in A])
print("prefix length", collections.Counter(len(p) for p in pre), "| Issue of 6-digit prefixes",
      collections.Counter(a["Issue"] for a, p in zip(A, pre) if len(p) == 6))
cal = post(f"{ODOR}/query", {"where": "START_DATE >= DATE '2021-01-15' AND START_DATE < DATE '2021-03-20'",
                              "outFields": "REQUEST_ID,START_DATE", "returnGeometry": "false"})["features"]
cal = sorted((int(c["attributes"]["REQUEST_ID"]), c["attributes"]["START_DATE"]) for c in cal
             if c["attributes"]["REQUEST_ID"] and c["attributes"]["START_DATE"])
cid = np.array([c[0] for c in cal], float)
ct = np.maximum.accumulate(np.array([c[1] for c in cal], float))  # enforce monotone
print("calibration points", len(cal), "ids", int(cid.min()), "-", int(cid.max()))
ids = np.array([int(p) for p in pre if len(p) == 8], float)
est = np.interp(ids, cid, ct)
print("8-digit prefixes", len(ids), "range", int(ids.min()), "-", int(ids.max()))
for q in (0, 1, 50, 99, 100):
    print(f"  p{q:<3} est. date (UTC) {dt.datetime.fromtimestamp(np.percentile(est, q) / 1000, dt.timezone.utc):%Y-%m-%d %H:%M}")
cst = collections.Counter(dt.datetime.fromtimestamp(t / 1000 - 6 * 3600, dt.timezone.utc).strftime("%m-%d") for t in est)
print("  per day (CST)", sorted(cst.items()))
suf = np.array([int(a["CASE_NUMBE"].split("-")[1]) for a in A])
print("311 case-number suffix range", suf.min(), "-", suf.max(), "| span", suf.max() - suf.min())

# ---------------------------------------------------------------- facilities: profile
section("facilities profile")
FAC = {
    "adult_care": ("Latitude", "Company", "PriSic"), "correctional": ("Latitude", "Company", "PriSic"),
    "hospitals": (None, "NAME", "ADMIN"), "trauma": (None, "COMPANY", "LevelClass"),
    "schools": (None, "School_Name", "Instruction_Type"), "fire_stations": (None, "LABEL", "Admin"),
    "nursing": (None, "FacName", "ProgType"), "assisted_living": (None, "FacName", "ProgType"),
    "icf": (None, "FacName", "COH_Servic"),
}
for name, (_, nk, ck) in FAC.items():
    fs = load(f"facilities_{name}.json")
    g, x, y = coords(fs)
    c = collections.Counter(zip(x.round(6), y.round(6)))
    names = [f["attributes"].get(nk) for f in fs]
    blank = sum(1 for n in names if not str(n or "").strip())
    dupname = len(names) - len({str(n or "").strip().upper() for n in names})
    print(f"{name}: n={len(fs)} nogeom={len(fs) - len(g)} inbbox={in_bbox(x, y).sum()} "
          f"lon[{x.min():.3f},{x.max():.3f}] lat[{y.min():.3f},{y.max():.3f}] "
          f"sharedcoord_recs={sum(v for v in c.values() if v > 1)} maxstack={max(c.values())} "
          f"blank_{nk}={blank} dup_{nk}={dupname}")
    print("   ", ck, collections.Counter(f["attributes"].get(ck) for f in fs).most_common(8))
sch = load("facilities_schools.json")
print("schools status", collections.Counter(f["attributes"]["School_Status"] for f in sch).most_common(),
      "| update", collections.Counter(str(f["attributes"]["Update_Date"]).split()[0] for f in sch
                                      if f["attributes"].get("Update_Date")).most_common(3))
print("schools city", collections.Counter(f["attributes"]["School_City"] for f in sch).most_common(6))
ac = load("facilities_adult_care.json")
print("adult_care MatchLC", collections.Counter(f["attributes"]["MatchLC"] for f in ac).most_common(),
      "| ProdDate", collections.Counter(f["attributes"]["ProdDate"] for f in ac).most_common(3))
for name in ("nursing", "assisted_living"):
    fs = load(f"facilities_{name}.json")
    print(name, "COH_Servic", collections.Counter(f["attributes"].get("COH_Servic") for f in fs).most_common())

# ---------------------------------------------------------------- valve test
section("311 'Water Main Valve' vs INOP valves")
val = load("valves.json")
va = [f["attributes"] for f in val]
V = xy([f["geometry"]["x"] for f in val], [f["geometry"]["y"] for f in val])
cond = np.array([a["CONDITION"] for a in va], object)
cdate = np.array([a["CONDITIONDATE"] or 0 for a in va], float)
main = np.array([a["SUBTYPECD"] != HYDRANT_VALVE_SUBTYPE and a["VALVE_USE"] not in LEAD_USE for a in va])
inop = cond == "INOP"
pre_uri = inop & (cdate > 0) & (cdate < URI_START.timestamp() * 1000)
post_uri = inop & (cdate >= URI_START.timestamp() * 1000)
print(f"valves {len(va)} | main-isolation {main.sum()} | INOP {inop.sum()} (pre-Uri {pre_uri.sum()}, "
      f"post-Uri {post_uri.sum()}, undated {(inop & (cdate == 0)).sum()}) | known-OK "
      f"{np.isin(cond, ['GOOD', 'FAIR', 'POOR']).sum()} | unknown {(cond == None).sum()}")  # noqa: E711

issue = np.array([f["attributes"]["Issue"] for f in geo])


def dedupe(pts):
    _, i = np.unique(pts.round(1), axis=0, return_index=True)
    return pts[np.sort(i)]


wmv = dedupe(P[issue == "Water Main Valve"])
oth = dedupe(P[issue != "Water Main Valve"])
leak = dedupe(P[issue == "Water Leak"])
svc = dedupe(P[issue == "Water Service"])
cus = load("customers.json")
CU = xy([f["geometry"]["x"] for f in cus], [f["geometry"]["y"] for f in cus])
cus_s = CU[rng.choice(len(CU), 20000, replace=False)]
# valve-distribution baseline: random valves, displaced by the empirical request->nearest-valve offsets
tree_all = cKDTree(V)
_, j = tree_all.query(wmv)
off = wmv - V[j]
vb = V[rng.choice(len(V), 20000, replace=False)] + off[rng.integers(0, len(off), 20000)]
print(f"query sets (unique locations): WMV {len(wmv)} (of {(issue == 'Water Main Valve').sum()} geocoded), "
      f"other-311 {len(oth)}, leak {len(leak)}, service {len(svc)}, customers {len(cus_s)}, valve-baseline {len(vb)}")


def metrics(Q, sel, flag):
    """Q: points; sel: valve subset; flag: INOP-type mask (within sel)."""
    Vs, fl = V[sel], flag[sel]
    t_f, t_o, t_a = cKDTree(Vs[fl]), cKDTree(Vs[~fl]), cKDTree(Vs)
    d_f, _ = t_f.query(Q)
    d_o, _ = t_o.query(Q)
    d_a, ia = t_a.query(Q)
    near_f = fl[ia]
    nb = t_a.query_ball_point(Q, R)
    share = np.array([fl[n].mean() if len(n) else np.nan for n in nb])
    return dict(d_f=d_f, d_o=d_o, d_a=d_a, near_f=near_f, share=share, nnb=np.array([len(n) for n in nb]))


def boot_diff(a, b, n=2000):
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    d = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(n)]
    return a.mean() - b.mean(), np.percentile(d, [2.5, 97.5])


sets = {"WMV": wmv, "other311": oth, "leak": leak, "service": svc, "customers": cus_s, "valve_base": vb}
for label, sel, flag in [("ALL valves, INOP", np.ones(len(V), bool), inop),
                         ("MAIN valves, INOP", main, inop),
                         ("MAIN valves, INOP dated pre-Uri (others incl. post-Uri INOP)", main, pre_uri),
                         ("MAIN valves, INOP dated post-Uri", main, post_uri)]:
    print(f"\n-- {label}: base rate {flag[sel].mean():.4f} of {sel.sum()} valves")
    print(f"   {'set':<11}{'n':>7}{'med d_flag':>11}{'med d_other':>12}{'med d_any':>10}{'nearest=flag':>13}"
          f"{'flag<50m':>9}{'share@150m':>11}{'valves@150m':>12}")
    M = {k: metrics(q, sel, flag) for k, q in sets.items()}
    for k, m in M.items():
        print(f"   {k:<11}{len(sets[k]):>7}{np.median(m['d_f']):>11.0f}{np.median(m['d_o']):>12.0f}"
              f"{np.median(m['d_a']):>10.0f}{m['near_f'].mean():>13.4f}{(m['d_f'] < 50).mean():>9.4f}"
              f"{np.nanmean(m['share']):>11.4f}{np.median(m['nnb']):>12.0f}")
    for ref in ("other311", "customers", "valve_base"):
        d1, ci1 = boot_diff(M["WMV"]["near_f"].astype(float), M[ref]["near_f"].astype(float))
        d2, ci2 = boot_diff(M["WMV"]["share"], M[ref]["share"])
        print(f"   WMV - {ref:<10} nearest=flag {d1:+.4f} [{ci1[0]:+.4f},{ci1[1]:+.4f}]   "
              f"share@150m {d2:+.4f} [{ci2[0]:+.4f},{ci2[1]:+.4f}]")
    # within-cell comparison (1 km grid): controls for neighbourhood inspection coverage / valve density
    cell = lambda Q: tuple(map(tuple, np.floor(Q / 1000).astype(int)))
    cw, co = cell(wmv), cell(oth)
    by = collections.defaultdict(lambda: [[], []])
    for c, v in zip(cw, M["WMV"]["near_f"]):
        by[c][0].append(v)
    for c, v in zip(co, M["other311"]["near_f"]):
        by[c][1].append(v)
    both = [(np.mean(a), np.mean(b), len(a)) for a, b in by.values() if a and b]
    w = np.array([t[2] for t in both], float)
    diff = np.array([t[0] - t[1] for t in both])
    bs = [np.average(diff[i], weights=w[i]) for i in (rng.integers(0, len(diff), len(diff)) for _ in range(2000))]
    print(f"   within 1 km cells ({len(both)} cells, {int(w.sum())} WMV): WMV - other311 nearest=flag "
          f"{np.average(diff, weights=w):+.4f} [{np.percentile(bs, 2.5):+.4f},{np.percentile(bs, 97.5):+.4f}]")

# who did crews flag after Uri? INOP valves recorded Feb-Dec 2021 near WMV vs other requests
section("post-Uri INOP flags near requests")
mi = main & post_uri & (cdate < dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
t = cKDTree(V[mi])
for k in ("WMV", "other311", "customers", "valve_base"):
    d, _ = t.query(sets[k])
    print(f"{k:<11} share with a main INOP valve flagged 2021-02-14..2021-12-31 within 100 m: {(d < 100).mean():.4f}")

# ---------------------------------------------------------------- facilities: fitness for "who is affected"
section("facilities: reach of the water network and overlaps")
mains = load("mains.json")
mv = np.concatenate([np.asarray(p) for f in mains for p in f["geometry"]["paths"]])
tm = cKDTree(xy(mv[:, 0], mv[:, 1]))
for name in FAC:
    _, x, y = coords(load(f"facilities_{name}.json"))
    d, _ = tm.query(xy(x, y))
    print(f"{name:<16} n={len(x):>5}  main vertex within 120 m: {(d <= 120).mean():.3f}  (>500 m: {(d > 500).sum()})")
F = {n: xy(*coords(load(f"facilities_{n}.json"))[1:]) for n in ("adult_care", "nursing", "assisted_living")}
ta = cKDTree(F["adult_care"])
for n in ("nursing", "assisted_living"):
    d, _ = ta.query(F[n])
    print(f"{n} with a Data Axle adult-care point within 100 m: {(d < 100).mean():.3f}")
h21 = post("https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/COH_HOSPITALS/FeatureServer/0/query",
           {"where": "1=1", "outFields": "NAME", "returnGeometry": "false"})["features"]
h25 = {f["attributes"]["NAME"] for f in load("facilities_hospitals.json")}
h21 = {f["attributes"]["NAME"] for f in h21}
print(f"hospital names: 2025 view {len(h25)}, 2021 COH_HOSPITALS {len(h21)}, identical sets: {h25 == h21}, "
      f"only-2025 {len(h25 - h21)}, only-2021 {len(h21 - h25)}")
fsx = load("facilities_fire_stations.json")
print("fire stations LastUpdate", collections.Counter(str(f["attributes"].get("LastUpdate"))[:7] for f in fsx).most_common(4))
