"""Server-side field statistics for the City layers we use (provenance + quality).

Writes data/raw/meta/server_stats.json. Run any time to see whether the live
service has changed since our download.
"""
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path

META = Path(__file__).resolve().parent.parent / "data" / "raw" / "meta"
U = "https://geogimsms.houstontx.gov/arcgis/rest/services/"
LAYERS = {
    "mains": ("HPC/UtilityAnalysis_gx/MapServer/51", ["SUBTYPECD", "WATERTYPE", "LIFECYCLESTATUS", "OWNER", "PIPETYPE", "MATERIAL"],
              ["DATECREATED", "DATEMODIFIED", "INSERVICEDATE", "CONDITIONDATE", "QCDATE"]),
    "valves": ("HPC/UtilityAnalysis_gx/MapServer/39", ["SUBTYPECD", "LIFECYCLESTATUS", "OWNER", "VALVE_USE", "CONDITION", "NORMALPOSITION", "REASON_INOPERABLE"],
               ["DATECREATED", "DATEMODIFIED", "INSERVICEDATE", "CONDITIONDATE", "INSPECTIONDATE", "QCDATE"]),
    "control_valves": ("HPC/UtilityAnalysis_gx/MapServer/38", ["SUBTYPECD", "CONTROLVALVETYPE", "NORMALPOSITION", "LIFECYCLESTATUS"], ["DATEMODIFIED"]),
    "hydrants": ("HPC/UtilityAnalysis_gx/MapServer/46", ["LIFECYCLESTATUS", "OWNER", "CONDITION"], ["DATECREATED", "DATEMODIFIED", "INSPECTIONDATE", "HYDRANT_INSPECTED_DATE"]),
    "prs": ("HPC/UtilityAnalysis_gx/MapServer/48", ["LIFECYCLESTATUS"], ["DATEMODIFIED"]),
    "customers": ("CAS/Customer_Operation_gx/MapServer/1", ["CITY"], []),
}


def q(url, **p):
    data = urllib.parse.urlencode({**p, "f": "json"}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url + "/query", data=data), timeout=120))
    if "error" in r:
        raise RuntimeError(r["error"])
    return r


def iso(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.UTC).date().isoformat() if ms else None


def main():
    out = {"queried_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds")}
    for name, (path, groups, dates) in LAYERS.items():
        url = U + path
        rec = {"url": url, "count": q(url, where="1=1", returnCountOnly="true")["count"], "groups": {}, "dates": {}}
        for g in groups:
            r = q(url, where="1=1", groupByFieldsForStatistics=g,
                  outStatistics=json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID" if name != "customers" else "OBJECTID_12", "outStatisticFieldName": "n"}]))
            rec["groups"][g] = sorted(((f["attributes"][g], f["attributes"]["n"]) for f in r["features"]), key=lambda t: -t[1])
        for d in dates:
            st = [{"statisticType": t, "onStatisticField": d, "outStatisticFieldName": t} for t in ("min", "max")]
            try:
                a = q(url, where="1=1", outStatistics=json.dumps(st))["features"][0]["attributes"]
                nn = q(url, where=f"{d} IS NOT NULL", returnCountOnly="true")["count"]
                rec["dates"][d] = {"min": iso(a["min"]), "max": iso(a["max"]), "non_null": nn}
            except RuntimeError as e:  # some date fields reject statistics on this server
                rec["dates"][d] = {"error": str(e)[:80]}
        out[name] = rec
        print(name, rec["count"], flush=True)
    (META / "server_stats.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
