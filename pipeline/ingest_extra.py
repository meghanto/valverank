"""Download the two datasets the plan needed but never fetched (audit: validation/data_audit_extra.md).

1. Winter Storm Uri 311 water requests -> data/raw/uri311.json
2. Facilities affected by a water shutoff -> data/raw/facilities_<name>.json

Also writes each layer's REST metadata (and the ArcGIS Online item record when there is one)
to data/raw/meta/ and appends the files to data/MANIFEST.json.

Privacy: the 311 layer carries parcel-owner names, owner mailing addresses and HCAD account
numbers joined on by the publisher. We do not download them. The Data Axle layers carry
contact names, gender and ethnicity; we do not download those either.

Usage: uv run --project pipeline python pipeline/ingest_extra.py [name ...]
"""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

from ingest import post

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
META = RAW / "meta"
AGO = "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services"
CF = "https://geogimsms.houstontx.gov/arcgis/rest/services/HPC/CriticalFacilities/MapServer"

DATA_AXLE = ("OBJECTID,Company,PriSicCd,PriSic,NaicsCd,Naics,PriCity,PriZip,Latitude,Longitude,"
             "MatchLCCd,MatchLC,LocEmpSz,YrEstab,TransDate,ProdDate,ObsolDate,HQBranch,CallStat")

# name -> (layer url, outFields, output file)
LAYERS = {
    "uri311": (
        f"{AGO}/311_water2019/FeatureServer/0",
        "FID,CASE_NUMBE,Issue,Status,Score,Match_type,Addr_type,Stacked,COUNCIL_DI,NEIGHBORHO,"
        "city,zip,parcel_typ,state_clas,Lowmod_pct,LMI_Areas,X,Y",
        "uri311.json",
    ),
    # HPC/CriticalFacilities: Data Axle licensed data (see audit before shipping anything from it)
    "adult_care": (f"{CF}/0", DATA_AXLE, "facilities_adult_care.json"),
    "correctional": (f"{CF}/1", DATA_AXLE, "facilities_correctional.json"),
    # City of Houston open-data views (cohgis_ago), refreshed 2025
    "hospitals": (f"{AGO}/COH_Hospitals_view/FeatureServer/10", "*", "facilities_hospitals.json"),
    "trauma": (f"{AGO}/COH_Trauma_Centers_view/FeatureServer/9", "*", "facilities_trauma.json"),
    "schools": (
        f"{AGO}/COH_Schools_view/FeatureServer/0",
        "OBJECTID_1,District_Name,District_Type,School_Number,School_Name,Instruction_Type,Charter_Type,"
        "Residential_Facility,School_City,School_Zip,Grade_Range,School_Enroll_as_of_Oct_2022,"
        "School_Status,School_Status_Date,Update_Date",
        "facilities_schools.json",
    ),
    "fire_stations": (f"{AGO}/COH_Houston_Fire_Stations_view/FeatureServer/10", "*", "facilities_fire_stations.json"),
    # HHSC long-term-care extracts posted by a city user, April 2020
    "nursing": (f"{AGO}/Nursing_Facilities/FeatureServer/0", "*", "facilities_nursing.json"),
    "assisted_living": (f"{AGO}/Assisted_Living_Facilities/FeatureServer/0", "*", "facilities_assisted_living.json"),
    "icf": (f"{AGO}/Intermediate_Care_Facilities/FeatureServer/0", "*", "facilities_icf.json"),
}


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url + ("&" if "?" in url else "?") + "f=json", timeout=60) as r:
        return json.load(r)


def save_meta(name: str, url: str) -> None:
    meta = get_json(url)
    stem = url.split("/rest/services/")[1].replace("/FeatureServer", "").replace("/MapServer", "").replace("/", "_")
    (META / f"{stem}.json").write_text(json.dumps(meta, indent=1))
    if meta.get("serviceItemId"):
        item = get_json(f"https://www.arcgis.com/sharing/rest/content/items/{meta['serviceItemId']}")
        (META / f"{stem}_item.json").write_text(json.dumps(item, indent=1))


def fetch(name: str) -> tuple[str, int]:
    url, fields, fname = LAYERS[name]
    save_meta(name, url)
    ids = sorted(post(f"{url}/query", {"where": "1=1", "returnIdsOnly": "true"})["objectIds"])
    chunks = [ids[i : i + 1000] for i in range(0, len(ids), 1000)]
    one = lambda c: post(f"{url}/query", {"objectIds": ",".join(map(str, c)), "outFields": fields,
                                          "returnGeometry": "true", "outSR": "4326"})["features"]
    feats = []
    with cf.ThreadPoolExecutor(4) as ex:
        for part in ex.map(one, chunks):
            feats.extend(part)
    (RAW / fname).write_text(json.dumps(feats))
    print(f"{name}: {len(feats)} / {len(ids)} -> {fname}", flush=True)
    return fname, len(feats)


def update_manifest(results: list[tuple[str, int]]) -> None:
    path = ROOT / "data" / "MANIFEST.json"
    man = json.loads(path.read_text()) if path.exists() else {}
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    for fname, n in results:
        b = (RAW / fname).read_bytes()
        man[fname] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()[:16], "downloaded_utc": now, "records": n}
    path.write_text(json.dumps(dict(sorted(man.items())), indent=1))


if __name__ == "__main__":
    META.mkdir(parents=True, exist_ok=True)
    (META / "HPC_CriticalFacilities_MapServer.json").write_text(json.dumps(get_json(CF), indent=1))
    names = sys.argv[1:] or list(LAYERS)
    with cf.ThreadPoolExecutor(4) as ex:
        results = list(ex.map(fetch, names))
    update_manifest(results)
