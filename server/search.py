"""Place search: street intersections from the City's centerlines (instant, offline), street addresses via the
US Census Geocoder (free, public domain), OpenStreetMap Nominatim as the last fallback.

  suggest(q)  -> up to 8 intersections matching what was typed ("westh", "westheimer & kir", "kirby and w")
  locate(q)   -> (lon, lat, label) or None
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from streets import norm  # noqa: E402  same normalization as the index

_PAIRS = None
_SPLIT = re.compile(r"\s+(?:and|&|at|@|/|x)\s+|\s*[&@/]\s*", re.I)


def _pairs():
    global _PAIRS
    if _PAIRS is None:
        f = ROOT / "data" / "build" / "intersections.json"
        idx = json.loads(f.read_text()) if f.exists() else {}
        _PAIRS = [(k.split("|")[0], k.split("|")[1], v) for k, v in idx.items()]
    return _PAIRS


def _title(name: str) -> str:
    return " ".join(w.capitalize() if not re.match(r"^\d", w) else w.lower() for w in name.split())


def _q(raw: str) -> list[str]:
    raw = re.sub(r",?\s*houston.*$", "", raw.strip(), flags=re.I)
    return [norm(p) for p in _SPLIT.split(raw, maxsplit=1) if p.strip()]


def _splits(raw: str):
    """Candidate (street, cross street) readings: explicit separator first, else every word boundary."""
    parts = _q(raw)
    if len(parts) == 2:
        return [tuple(parts)]
    words = parts[0].split() if parts else []
    return [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]


def _match(a: str, b: str):
    for x, y, ll in _pairs():
        if x.startswith(a) and y.startswith(b):
            return x, y, ll
        if y.startswith(a) and x.startswith(b):
            return y, x, ll
    return None


def suggest(q: str, limit: int = 8):
    parts = _q(q)
    if not parts or not parts[0] or re.match(r"^\d", q.strip()):
        return []
    a = parts[0]
    b = parts[1] if len(parts) > 1 else ""
    if not b and " " in a:
        for s1, s2 in _splits(q):  # "tidwell antoine": two names without a separator
            hit = _match(s1, s2)
            if hit:
                return [{"label": f"{_title(hit[0])} & {_title(hit[1])}", "lon": hit[2][0], "lat": hit[2][1]}]
    out, seen = [], set()
    for x, y, ll in _pairs():
        for s1, s2 in ((x, y), (y, x)):
            if s1.startswith(a) and (not b or s2.startswith(b)):
                key = (s1, s2)
                if key not in seen:
                    seen.add(key)
                    out.append({"label": f"{_title(s1)} & {_title(s2)}", "lon": ll[0], "lat": ll[1]})
                break
        if len(out) >= 200:
            break
    # exact street-name matches first, then shorter cross streets (usually the major ones)
    out.sort(key=lambda r: (not r["label"].upper().startswith(a + " &"), len(r["label"])))
    return out[:limit]


def _census(q: str):
    addr = q if re.search(r"houston|tx\b", q, re.I) else q + ", Houston, TX"
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?" + urllib.parse.urlencode(
        {"address": addr, "benchmark": "Public_AR_Current", "format": "json"})
    m = json.load(urllib.request.urlopen(url, timeout=10))["result"]["addressMatches"]
    return (m[0]["coordinates"]["x"], m[0]["coordinates"]["y"], m[0]["matchedAddress"].title()) if m else None


def locate(q: str):
    for s1, s2 in _splits(q):
        hit = _match(s1, s2)
        if hit:
            return hit[2][0], hit[2][1], f"{_title(hit[0])} & {_title(hit[1])}"
    if not re.match(r"^\s*\d", q) and len(_q(q)) == 1 and " " not in _q(q)[0]:
        return None  # a single street name is not a place: pick a suggested intersection instead
    try:
        hit = _census(q)
        if hit:
            return hit
    except Exception:
        pass
    from server.llm import geocode  # Nominatim fallback
    ll = geocode(q)
    return (ll[0], ll[1], q) if ll else None
