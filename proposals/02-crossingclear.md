# CrossingClear: when a train blocks the road, who loses their ambulance?

> **One line:** Freight trains block Houston crossings for hours, cutting neighborhoods off from fire and EMS. CrossingClear uses 24,000+ federal blocked-crossing reports and the City's live crossing sensors to map which homes fall outside the fire department's response-time targets when crossings are blocked. It also reroutes units around them.

**Targets:** Best Overall ($1,000), Best Pitch/Demo ($500). This has no Environment fit. An environmental-justice framing is possible but secondary.

---

## 1. The problem

| Fact | Number | Source |
|---|---|---|
| Blocked-crossing reports filed for Houston (Feb 2020 – Oct 10 2026) | **24,442** | FRA Blocked Crossing Incident Reporter API, pulled 2026-10-10 |
| Reports saying **first responders were seen unable to cross** | **11,536 (47%)** | Same, `communityImpacts` flag 1 |
| Reports in 2024 vs. 2026 so far | 5,657 vs. **5,434** (2026 is nearly at 2024's total with 2.5 months left) | Same |
| Reported blockages lasting 1 hour or more | **10,037 (41%)** | Same, `duration` field |
| Most-reported crossings | Eastwood St 3,188, Milby St 2,294, Leeland St 1,924, Cullen Blvd 1,458 (East End) | Same |
| Texas's rank among states for blocked-crossing reports | **#1** (11,711, ahead of Ohio's 10,461) | [FRA Report to Congress](https://railroads.dot.gov/sites/fra.dot.gov/files/2024-01/FRA%20Report%20to%20Congress_Blocked%20Crossing%20Portal.pdf) |
| HFD reroutes due to stopped trains | 1,300+ in 2021 *[news; re-verify]* | via [ABC13](https://abc13.com/post/first-responders-delayed-train-blocks-intersection-east-houston/5453276/) |
| HFD 90th-percentile first arrival, 2025 | Fire 10:35, EMS 13:46 *[re-verify]* | [HFD reports](https://www.houstontx.gov/fire/reportsandstats/index.html) |

These are crowd-sourced reports, and a few crossings dominate, which suggests repeat reporters. Present them as "reported", not as measured ground truth.

**Human cost:** in 2019 ABC13 documented an ambulance forced to reroute while a man was pinned under a car in east Houston. In Polk County, Texas, an 11-week-old died after paramedics were delayed by a train ([ABC13](https://abc13.com/amp/post/union-pacific-railroad-crossings-closed-polk-county-legget-texas/13871299/)). No Houston EMS-delay death is documented; don't claim one. Separately, Sergio Rodriguez, a 15-year-old Milby High student, was killed by a train walking to school in Dec 2024 ([Houston Chronicle](https://www.houstonchronicle.com/news/houston-texas/education/hisd/article/sergio-rodriguez-rail-crossings-21249543.php)). That is a pedestrian death, not an EMS case. Train Watch showed false "blocked" readings in Jul 2026, so routing must handle uncertain sensor readings. See `news.md` §2.

---

## 2. What we build

1. **Road graph** for Houston's East End and nearby areas, from OSMnx, with the 584 public at-grade crossings (FRA inventory) marked as edges that can be blocked.
2. **Blockage model per crossing.** From the FRA reports, estimate for each crossing:
   - the probability it is blocked, by hour of week
   - a duration distribution (reports give ranges, so sample within them)
3. **Coverage analysis.** From the City's 94 fire stations, compute drive time to every address under (a) no blockages and (b) blockages sampled from the model by Monte Carlo. Output each address's probability of missing HFD's own response target.
4. **Train-aware routing.** For any incident address and current blockage state (live Train Watch or replay), compute the fastest route that avoids blocked crossings, and the minutes saved against a naive route.
5. **Live layer.** The City's Train Watch feed (56 sensored crossings) shows current status. We have been recording it every minute since Sat 2:50 PM, which gives us our own history.

---

## 3. 90-second demo

| Time | Judge sees | Narration |
|---|---|---|
| 0–15 s | East End map with the 584 crossings. Heat dots sized by reports. | "Houstonians have filed 24,000 blocked-train reports. In half of them, someone watched an ambulance or fire truck unable to get through." |
| 15–40 s | **Judge clicks** any address. Two routes animate from the nearest station: the naive one stops at a blocked crossing, the train-aware one detours. Δ minutes shown. | "Here's what a blocked crossing costs this street." |
| 40–65 s | **Judge drags** an hour-of-week slider to Friday 10 PM (the worst hour in the data). A coverage layer shrinks, and a counter shows homes now outside HFD's target. | "At this hour, this many homes lose on-time coverage." |
| 65–80 s | Planning panel: "If one crossing got a grade separation or a sensor, which one helps most?" Ranked list. | "This is where the City should spend the next grade-separation dollar." |
| 80–90 s | Live Train Watch strip, recorded since Saturday afternoon | "And this runs live off the City's own sensors." |

---

## 4. Fit with Orion's judging criteria

| Criterion | How CrossingClear scores |
|---|---|
| **Originality** | No Devpost project found for train-blocked emergency coverage in Houston. **Commercial prior art exists:** TRAINFO predicts blockages and feeds emergency dispatch. Our angle is an open, address-level coverage audit and capital-planning tool, not another alert app. |
| **Relevance to track** | General track and Pitch. No environment fit, apart from an environmental-justice angle for the East End. |
| **Impact** | A life-safety problem every Houston judge recognizes, measured in our own data. Texas leads the nation in reports. |
| **Demo** | The most visceral of the three: click an address, watch the ambulance get stuck. |
| **Technical implementation** | Graph routing with blockable edges, Monte Carlo coverage, a time-of-week blockage model, and crossing-priority ranking. Routing alone is basic; the coverage and Monte Carlo work carries the technical weight. |

---

## 5. Business case

- **Buyers:** City of Houston Office of Emergency Management and HFD planning (station coverage, pre-planned detours). The City's Train Watch program (an Aug 2025 pilot, ~70 sensors) is the natural home. Private ambulance operators and delivery fleets are secondary.
- **Capital-planning use:** rank crossings for grade-separation funding by homes regaining coverage per dollar. The federal Railroad Crossing Elimination grant program funds exactly this *[verify current program status]*.
- **Existing alternatives:**

  | Alternative | Gap |
  |---|---|
  | Houston Train Watch | Shows status only; no routing or coverage analysis |
  | TRAINFO (commercial) | Proprietary; built for dispatch; no open coverage audit. **Ran the City of Houston's "Smart Railroad Crossings Project" in 2022–23** ([white paper](https://trainfo.ca/wp-content/uploads/47415-TR-Trainfo-White-Paper-FINAL-Web.pdf)), so the target customer already knows them. |
  | Satori Defense (commercial) | Real-time Houston crossing intelligence (57 "TRAINFO-monitored" crossings), sold to drayage, petrochemical, **fire and emergency management**. Closed data; its Mar 2026 "3-year high" claim isn't supported by FRA data (see `news.md` §2.2b). |
  | Waze and consumer navigation | Not tied to fire/EMS response targets |

- **Differentiation:** open data, Houston-specific, quantifies coverage loss per address, and ranks fixes.
- **Beyond the hackathon:** the same pipeline works for any city using FRA data (162k reports nationally).

## 6. Technical design

```
FRA BCIR API ─┐
FRA crossing inventory (Socrata) ─┼─► ingest (Python) ─► per-crossing hour-of-week blockage model
HFD stations (ArcGIS) ─┘                                    │
OSMnx road graph (East End + buffer) ─► blockable edges at crossings
                                                            │
             Monte Carlo: sample blockage states → multi-source Dijkstra from stations
                                                            │
             per-address P(miss target), Δ minutes, crossing-priority ranking
                                                            │
             export static JSON/PMTiles ─► React + MapLibre/deck.gl; Train Watch fetched live in browser
```

- Keep the scope to the East End plus adjacent districts: hundreds of crossings, a few dozen stations.
- Precompute the Monte Carlo results. The browser only animates routes and looks up the selected hour.
- The Train Watch query is CORS-friendly ArcGIS JSON *[verify CORS]*. Fall back to our recorded snapshots.

## 7. Data (each endpoint queried on 2026-10-10)

| Data | Endpoint | Size |
|---|---|---|
| Blocked-crossing reports | `https://www.fra.dot.gov/blockedcrossings/api/incidents?state=TX&city=Houston&pageSize=500&page=N` | 24,442 Houston |
| Crossing inventory | `https://data.transportation.gov/resource/m2f8-22s6.json` | 584 Houston public at-grade |
| Live crossing status | `services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Train_Watch_Layer/FeatureServer/0/query` | 56 crossings |
| Fire stations | `HFD_94_FIRE_STATIONS` (same ArcGIS org) | 94 |
| Road network | OpenStreetMap through OSMnx | — |

## 8. Claims we will and won't make

- **Will:** "Reported blockages put N homes outside HFD's target on Friday nights" (our measured output, labelled as model-based).
- **Won't:** claim deaths in Houston, treat crowd reports as sensor truth, or say TRAINFO doesn't exist. Name it and differentiate.

## 9. Build plan

| Window | Work |
|---|---|
| Sat 3:30–6 PM | Ingest FRA reports, inventory and stations. Build the OSMnx graph and snap crossings to edges. Deploy a skeleton map. |
| Sat 6–10 PM | Blockage model, multi-source shortest paths, first coverage map |
| Sat 10 PM–2 AM | Monte Carlo, hour slider, click-to-route animation |
| Sun 2–6 AM | Crossing-priority ranking, live Train Watch strip, validation (compare against Train Watch where they overlap) |
| Sun 6–9 AM | Polish, README, **freeze 9 AM** |
| Sun 9 AM–12:30 PM | Devpost, slides, rehearsal, fallback video |

## 10. Risks

| Risk | Mitigation |
|---|---|
| "TRAINFO already does this" | Lead with coverage audit and capital planning, not alerts. Name TRAINFO in the pitch. |
| Routing around a blocked edge looks trivial | Put the technical story in the Monte Carlo coverage and crossing ranking |
| No live blockage during judging | Replay the worst recorded night. Live feed is a bonus. |
| Report noise and repeat reporters | Cap reports per reporter and crossing if possible. Show uncertainty bands. |
| No environment prize | Accept it. Max cash is $1,500, against $2,000 for the other two. |
