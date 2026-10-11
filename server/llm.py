"""Gemini: parse a question into break parameters; word a crew brief from engine numbers.

Gemini never produces a number shown to the user: parse_question returns a place
and parameters that the engine then runs; crew_brief receives the engine's
numbers and is told to use only those.
"""
import functools
import json
import os
import time
import urllib.parse
import urllib.request

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")  # 2.5-flash is closed to new API keys


_CLIENT = None


def _client():
    """One client per process: a temporary client is garbage-collected mid-request and closes its HTTP pool."""
    global _CLIENT
    if _CLIENT is None:
        from google import genai
        # 20 s per attempt: an occasional Gemini call stalls 30+ s; the retry is usually fast
        _CLIENT = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                               http_options={"timeout": 20_000, "retry_options": {"attempts": 2}})
    return _CLIENT


def parse_question(q: str) -> dict:
    prompt = (
        "Extract a Houston water-main break scenario from the user's question. Reply with JSON only: "
        '{"place": "<street intersection or address in Houston, TX>", "opening": <0.01-1 or null>, '
        '"t_first": <minutes until crews close the first valves, or null>, "t_dead": <extra minutes when a valve is dead, or null>, '
        '"t_repair": <minutes until repaired, or null>}. Use null for anything not stated. Question: ' + q)
    cfg = {"response_mime_type": "application/json"}
    try:  # extraction needs little reasoning; default thinking took 11-38 s
        r = _client().models.generate_content(model=MODEL, contents=prompt, config=cfg | {"thinking_config": {"thinking_level": "minimal"}})
    except Exception:
        r = _client().models.generate_content(model=MODEL, contents=prompt, config=cfg | {"thinking_config": {"thinking_level": "low"}})
    out = json.loads(r.text)
    if not out.get("place"):
        raise ValueError("no place in question")
    return out


_STREET_WORDS = r"(road|rd|street|st|drive|dr|avenue|ave|boulevard|blvd|lane|ln|parkway|pkwy|freeway|fwy|way)\.?$"


_INTERSECTIONS = None


def _local_intersection(a: str, b: str):
    """Look up 'A|B' in data/build/intersections.json (pipeline/streets.py); (lon, lat) or None."""
    global _INTERSECTIONS
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    if _INTERSECTIONS is None:
        f = root / "data" / "build" / "intersections.json"
        _INTERSECTIONS = json.loads(f.read_text()) if f.exists() else {}
    sys.path.insert(0, str(root / "pipeline"))
    from streets import norm
    hit = _INTERSECTIONS.get("|".join(sorted([norm(a), norm(b)])))
    return tuple(hit) if hit else None


OVERPASS = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]


@functools.lru_cache(maxsize=256)  # repeated demo questions answer instantly
def _intersection(a: str, b: str):
    """Shared OSM node of two named streets inside Houston (Overpass); (lon, lat) or None."""
    import re
    names = [re.sub(_STREET_WORDS, "", x.strip(), flags=re.I).strip() for x in (a, b)]
    names = [re.sub(r"^(n|s|e|w|north|south|east|west)\.?\s+", "", n, flags=re.I) for n in names]  # 'N Wayside' = 'North Wayside Drive'
    if not all(names):
        return None
    esc = [re.escape(n) for n in names]
    bb = "29.45,-95.95,30.20,-94.95"  # Houston service area (a bbox is far cheaper than an area query)
    q = (f'[out:json][timeout:25];way({bb})["highway"]["name"~"{esc[0]}",i]->.a;'
         f'way({bb})["highway"]["name"~"{esc[1]}",i]->.b;node(w.a)(w.b);out 1;')
    last = None
    for url in OVERPASS:  # the main host refuses or times out under load; mail.ru mirror verified 2026-10-11
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": "valverank-hackathon/0.1"})
            els = json.load(urllib.request.urlopen(req, timeout=30)).get("elements", [])
            return (els[0]["lon"], els[0]["lat"]) if els else None
        except Exception as e:
            last = e
    raise last


def geocode(place: str):
    """Street intersections via Overpass ('A and B', 'A & B', 'A at B'); otherwise Nominatim (1 req/s). (lon, lat) or None."""
    import re
    core = re.sub(r",?\s*houston.*$", "", place, flags=re.I).strip()
    parts = re.split(r"\s+(?:and|&|at|@|/)\s+|\s*[&@/]\s*", core, maxsplit=1, flags=re.I)
    if len(parts) == 2:
        hit = _local_intersection(*parts)  # City street centerlines, offline and instant
        if hit:
            return hit
        for attempt in range(2):  # Overpass rate-limits bursts (429); one retry
            try:
                hit = _intersection(*parts)
                if hit:
                    return hit
                break
            except Exception:
                time.sleep(2)
    q = place if "houston" in place.lower() else place + ", Houston, TX"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "valverank-hackathon/0.1"})
    time.sleep(1)
    res = json.load(urllib.request.urlopen(req, timeout=20))
    return (float(res[0]["lon"]), float(res[0]["lat"])) if res else None


def crew_brief(run: dict) -> str:
    facts = {
        "pipe_diameter_in": run["diameter"],
        "dead_valves_in_first_ring": run["dead_valves"],
        "assumptions": run["params"],
        "if_every_valve_worked": {"customer_hours_without_water": run["paper"]["customer_hours"],
                                  "phases": [{k: p[k] for k in ("phase", "minutes", "customers", "hydrants")} for p in run["paper"]["phases"]]},
        "with_city_valve_records": {"customer_hours_without_water": run["real"]["customer_hours"],
                                    "phases": [{k: p[k] for k in ("phase", "minutes", "customers", "hydrants")} for p in run["real"]["phases"]]},
    }
    if run.get("fixed"):
        facts["after_planned_repairs"] = {"valves_repaired_here": run.get("repaired_valves", []),
                                          "customer_hours_without_water": run["fixed"]["customer_hours"]}
    prompt = (
        "You write a short radio-style brief for a Houston Public Works valve crew responding to a water-main break. "
        "Use ONLY the numbers in FACTS; do not invent any number, street, or valve. 4-6 sentences, plain words. "
        "If dead_valves_in_first_ring is non-empty, name those valve numbers as recorded inoperable and say crews must "
        "go to the next ring; if it is empty, say every first-ring valve is recorded as working. Give the customers and "
        "hydrants affected in each phase ('gush' = pressure down 15 psi or more while the break flows; 'gush_dead' = "
        "still flowing because a valve is dead; 'isolated' = shut off for repair), and the customer-hours lost versus if "
        "every valve worked. If after_planned_repairs is present and lower, say what the planned repairs would save. "
        "End with: 'Model estimate from City records, June 2023 snapshot.' FACTS: " + json.dumps(facts))
    allowed = _numbers_in(facts) | {15.0, 2023.0}  # 15 psi threshold; snapshot year in the closing line
    for _ in range(2):  # Gemini may only reword engine numbers: any other number -> retry once, then template
        try:  # a short factual brief needs little reasoning; low thinking keeps it to a few seconds
            r = _client().models.generate_content(model=MODEL, contents=prompt, config={"thinking_config": {"thinking_level": "low"}})
        except Exception:
            r = _client().models.generate_content(model=MODEL, contents=prompt)
        text = r.text.strip()
        if _numbers_in(text) <= allowed:
            return text
    return _template_brief(run)


def _numbers_in(x) -> set:
    """Every number in a string or nested facts dict (commas stripped)."""
    import re
    if isinstance(x, str):
        return {float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", x)}
    out = set()
    stack = [x]
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            stack += list(v.values())
        elif isinstance(v, list):
            stack += v
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out.add(float(v))
    return out


def _template_brief(run: dict) -> str:
    dead = run["dead_valves"]
    lead = (f"Valves {', '.join(map(str, dead))} are recorded inoperable; go to the next ring." if dead
            else "Every first-ring valve is recorded as working.")
    ph = "; ".join(f"{p['phase']} {p['minutes']} min: {p['customers']:,} customers, {p['hydrants']} hydrants" for p in run["real"]["phases"])
    return (f"Break on a {run['diameter']:g}-inch main. {lead} {ph}. {run['real']['customer_hours']:,} customer-hours without water "
            f"vs {run['paper']['customer_hours']:,} if every valve worked. Model estimate from City records, June 2023 snapshot.")
