"""Street-intersection index from the City's street centerlines, for geocoding "X and Y" questions offline.

Source: geohwp 05_BaseData_Other-COH-Utilities/Street/FeatureServer/0 (232,174 centerline segments).
Segments meet at shared endpoints; every endpoint touched by two differently named streets is an
intersection. Writes data/build/intersections.json: {"NAME_A|NAME_B": [lon, lat]} with names
normalized by norm() (server/llm.py uses the same function).

  uv run --project pipeline python pipeline/streets.py
"""
import concurrent.futures as cf
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://geohwp.houstontx.gov/arcgis/rest/services/05_BaseData_Other-COH-Utilities/Street/FeatureServer/0/query"
RAW = ROOT / "data" / "raw" / "streets.json"
OUT = ROOT / "data" / "build" / "intersections.json"
PAGE = 2000

_DIR = r"^(N|S|E|W|NE|NW|SE|SW|NORTH|SOUTH|EAST|WEST)\.?\s+"
_TYPE = r"\s+(ROAD|RD|STREET|ST|DRIVE|DR|AVENUE|AVE|AV|BOULEVARD|BLVD|LANE|LN|PARKWAY|PKWY|FREEWAY|FWY|WAY|CT|COURT|PL|PLACE|CIR|TRL|HWY|EXPY)\.?$"


def norm(name: str) -> str:
    """'N Wayside Dr' -> 'WAYSIDE'; 'Westheimer Road' -> 'WESTHEIMER'."""
    n = re.sub(r"\s+", " ", (name or "").upper().strip())
    n = re.sub(_DIR, "", n)
    n = re.sub(_TYPE, "", n)
    return n.strip()


def page(offset):
    q = {"where": "1=1", "outFields": "NAME", "returnGeometry": "true", "outSR": 4326, "geometryPrecision": 6,
         "resultOffset": offset, "resultRecordCount": PAGE, "orderByFields": "OBJECTID", "f": "json"}
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=120))["features"]
        except Exception as e:
            err = e
    raise err


def main():
    if not RAW.exists():
        n = json.load(urllib.request.urlopen(URL + "?where=1%3D1&returnCountOnly=true&f=json", timeout=60))["count"]
        with cf.ThreadPoolExecutor(8) as ex:
            feats = [f for fs in ex.map(page, range(0, n, PAGE)) for f in fs]
        print(f"downloaded {len(feats)} of {n} segments")
        RAW.write_text(json.dumps([[f["attributes"]["NAME"], [[p[0], p[-1]] for p in f["geometry"]["paths"]]]
                                   for f in feats if f.get("geometry")]))
    rows = json.loads(RAW.read_text())
    at = defaultdict(set)
    for name, paths in rows:
        nm = norm(name)
        if not nm:
            continue
        for ends in paths:
            for x, y in ends:
                at[(round(x, 5), round(y, 5))].add(nm)
    idx = {}
    for (x, y), names in at.items():
        if len(names) < 2:
            continue
        names = sorted(names)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                idx.setdefault(f"{names[i]}|{names[j]}", [x, y])
    OUT.write_text(json.dumps(idx, separators=(",", ":")))
    print(f"{len(idx)} named intersections -> {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
    for a, b in [("Westheimer", "Kirby"), ("Tidwell", "Antoine"), ("Clinton", "N Wayside Dr")]:
        print(" ", a, b, idx.get("|".join(sorted([norm(a), norm(b)]))))


if __name__ == "__main__":
    sys.exit(main())
