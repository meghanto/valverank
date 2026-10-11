"""Gemini: parse a question into break parameters; word a crew brief from engine numbers.

Gemini never produces a number shown to the user: parse_question returns a place
and parameters that the engine then runs; crew_brief receives the engine's
numbers and is told to use only those.
"""
import json
import os
import time
import urllib.parse
import urllib.request

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def _client():
    from google import genai
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def parse_question(q: str) -> dict:
    prompt = (
        "Extract a Houston water-main break scenario from the user's question. Reply with JSON only: "
        '{"place": "<street intersection or address in Houston, TX>", "opening": <0.01-1 or null>, '
        '"t_first": <minutes until crews close the first valves, or null>, "t_dead": <extra minutes when a valve is dead, or null>, '
        '"t_repair": <minutes until repaired, or null>}. Use null for anything not stated. Question: ' + q)
    r = _client().models.generate_content(model=MODEL, contents=prompt,
                                          config={"response_mime_type": "application/json"})
    out = json.loads(r.text)
    if not out.get("place"):
        raise ValueError("no place in question")
    return out


def geocode(place: str):
    """Nominatim (1 req/s policy); returns (lon, lat) or None."""
    q = place if "houston" in place.lower() else place + ", Houston, TX"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "h2out-hackathon/0.1"})
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
    prompt = (
        "You write a short radio-style brief for a Houston Public Works valve crew responding to a water-main break. "
        "Use ONLY the numbers in FACTS; do not invent any number, street, or valve. 4-6 sentences, plain words. "
        "Say which valve numbers are recorded inoperable and that crews must go to the next ring, the customers and "
        "hydrants affected in each phase, and the customer-hours lost versus if every valve worked. "
        "End with: 'Model estimate from City records, June 2023 snapshot.' FACTS: " + json.dumps(facts))
    return _client().models.generate_content(model=MODEL, contents=prompt).text.strip()
