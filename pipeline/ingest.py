"""Download City of Houston water GIS layers to data/raw/*.json.

Layers come from public ArcGIS REST services (no auth). Queries use POST
because GET URLs carrying >~1k object IDs return 404.
"""
import concurrent.futures as cf
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
UTIL = "https://geogimsms.houstontx.gov/arcgis/rest/services/HPC/UtilityAnalysis_gx/MapServer"
CAS = "https://geogimsms.houstontx.gov/arcgis/rest/services/CAS/Customer_Operation_gx/MapServer"

LAYERS = {
    "mains": (f"{UTIL}/51", "OBJECTID,DIAMETER,MATERIAL,INSERVICEDATE,LIFECYCLESTATUS,PIPETYPE,COUNCILDISTRICT", True),
    "valves": (
        f"{UTIL}/39",
        "OBJECTID,CONDITION,CONDITIONDATE,REASON_INOPERABLE,VALVE_USE,DIAMETER,INSERVICEDATE,SUBTYPECD,NORMALPOSITION,LIFECYCLESTATUS",
        True,
    ),
    "hydrants": (f"{UTIL}/46", "OBJECTID,CONDITION,INSERVICEDATE,LIFECYCLESTATUS", True),
    "customers": (f"{CAS}/1", "OBJECTID_12,ZIP", True),
}


def post(url: str, params: dict) -> dict:
    data = urllib.parse.urlencode({**params, "f": "json"}).encode()
    err = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=180) as r:
                out = json.load(r)
            if "error" in out:
                raise RuntimeError(out["error"])
            return out
        except Exception as e:  # network flakiness on city servers
            err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url}: {err}")


def fetch_layer(name: str) -> None:
    url, fields, geom = LAYERS[name]
    ids = sorted(post(f"{url}/query", {"where": "1=1", "returnIdsOnly": "true"})["objectIds"])
    chunks = [ids[i : i + 1000] for i in range(0, len(ids), 1000)]

    def one(chunk):
        r = post(
            f"{url}/query",
            {
                "objectIds": ",".join(map(str, chunk)),
                "outFields": fields,
                "returnGeometry": "true" if geom else "false",
                "outSR": "4326",
            },
        )
        return r["features"]

    feats = []
    with cf.ThreadPoolExecutor(8) as ex:
        for part in ex.map(one, chunks):
            feats.extend(part)
    out = RAW / f"{name}.json"
    out.write_text(json.dumps(feats))
    print(f"{name}: {len(feats)} / {len(ids)} features -> {out}", flush=True)


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(LAYERS)
    with cf.ThreadPoolExecutor(len(names)) as ex:
        list(ex.map(fetch_layer, names))
