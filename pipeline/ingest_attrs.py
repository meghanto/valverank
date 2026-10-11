"""Download extra attribute columns (no geometry) for audit: data/raw/{name}_attrs.json."""
import concurrent.futures as cf
import json
import sys
from pathlib import Path

from ingest import UTIL, post

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
EXTRA = {
    "mains": (f"{UTIL}/51", "OBJECTID,SUBTYPECD,WATERTYPE,OWNER,CONDITION,DATECREATED,DATEMODIFIED,REPLACEMENTYR,MEASUREDLENGTH"),
    "valves": (f"{UTIL}/39", "OBJECTID,OWNER,DATECREATED,DATEMODIFIED,INSPECTIONDATE,CURRENT_POSITION,SMALLMAINDIAMETER,TURNSTOOPEN"),
    "hydrants": (f"{UTIL}/46", "OBJECTID,OWNER,DATECREATED,DATEMODIFIED,INSPECTIONDATE,HYDRANT_INSPECTED_DATE"),
    "control_valves": (f"{UTIL}/38", "OBJECTID,SUBTYPECD,CONTROLVALVETYPE,NORMALPOSITION,LIFECYCLESTATUS,DIAMETER,DATEMODIFIED"),
    "structures": (f"{UTIL}/44", "OBJECTID,SUBTYPECD,NAME,FACILITYNAME,LIFECYCLESTATUS,WATERTYPE,OWNER,CAPACITY,LARGEMAINDIAMETER,SMALLMAINDIAMETER,OPERATIONALAREA,ZONE,DATEMODIFIED"),
    "prs": (f"{UTIL}/48", "OBJECTID,LIFECYCLESTATUS,LARGEMAINDIAMETER,SMALLMAINDIAMETER,PRESSURESETTINGINIPSI,DATEMODIFIED"),
}


def fetch(name):
    url, fields = EXTRA[name]
    geom = name in ("control_valves", "prs", "structures")
    ids = sorted(post(f"{url}/query", {"where": "1=1", "returnIdsOnly": "true"})["objectIds"])
    chunks = [ids[i:i + 1000] for i in range(0, len(ids), 1000)]
    one = lambda c: post(f"{url}/query", {"objectIds": ",".join(map(str, c)), "outFields": fields,
                                          "returnGeometry": str(geom).lower(), "outSR": "4326"})["features"]
    feats = []
    with cf.ThreadPoolExecutor(8) as ex:
        for part in ex.map(one, chunks):
            feats.extend(part)
    (RAW / f"{name}_attrs.json").write_text(json.dumps(feats))
    print(name, len(feats), "/", len(ids), flush=True)


if __name__ == "__main__":
    names = sys.argv[1:] or list(EXTRA)
    with cf.ThreadPoolExecutor(len(names)) as ex:
        list(ex.map(fetch, names))
