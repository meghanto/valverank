# How it works (learn this cold)

## One sentence
When a main breaks, crews close the nearest valves. If one of those valves is broken, they have to go to the next one out, so more homes lose water. We compute that on Houston's real network.

## The four steps

**1. Network.** The City's GIS has 290,959 pipe lines; 290,411 are in-use drinking-water mains. Where two pipe ends share a coordinate, they're connected. That gives a graph of 270,356 junctions.

**2. Valves cut the graph.** 166,362 valves are in the GIS. We keep a valve only if it sits within 1 m of a main (3 m for valves the City labels in-line) and is not a hydrant or service valve: 92,763 qualify. The rest are on service lines or hydrant leads, which don't isolate a main.
- Valve at a junction: closing it separates the pipes that meet there.
- Valve in the middle of a pipe: we split the pipe in two at the valve.

**3. Isolation segment.** This is the group of pipes you can't avoid shutting off together, because there's no working valve between them (Walski's term; it's standard in water engineering). We find these with union-find: join every pair of pipe pieces that meet at a point with no working valve. Each resulting group is a segment.

We do this twice:

| Scenario | Rule | Segments | Avg customers out per break |
|---|---|---|---|
| **Paper** | Every valve closes | 72,253 | 16.3 |
| **Real** | Valves marked `INOP` in City records can't close | 55,076 | **38.6** |

Fewer segments means bigger ones: dead valves merge neighboring segments.

**4. Supply loss.** Some segments are the only path between a water source (218 plants, pump stations and tanks) and the segments beyond them. Closing such a segment cuts those off too. We find every such case in one pass (articulation points in the segment graph) and check it against brute force.

**5. Count who's affected.** Each of the 544,011 customer accounts is attached to its nearest main (if within 120 m), and each hydrant to its nearest main (within 40 m). Customers out = the accounts in the closed segment plus those cut off downstream. (The table above includes downstream loss.)

"Average customers per break" is weighted by pipe length, because longer pipe means more chances to break.

## Terms a judge may use
- **Isolation segment / valve isolation:** step 3.
- **Unintended isolation:** closing a segment can also cut off segments downstream that have no other path to a plant, pump station or tank. **We model this** (connectivity only). It adds 3.2 customers per break on paper and 7.9 with the City's valve records. Tidwell & Antoine (2,000 reported) is still a miss: that grid is looped, so what people lost was probably pressure, which needs a hydraulic model.
- **Hydraulic model:** a pressure and flow simulation (EPANET, WaterGEMS). **We don't do hydraulics.** Ours is connectivity only: who *can* be cut off, not water pressure.
- **Valve exercising:** turning each valve periodically so it doesn't seize. Industry guidance is every valve within about 5 years. 78% of Houston's main valves were last inspected 5+ years before today.

## Honest limits (say them before the judge does)
1. The data is a June 2023 snapshot. Pipes change slowly (~0.3%/yr). Dead valves don't fix themselves, so the inoperable count is a floor.
2. Customer accounts aren't people. An apartment complex can be a single account.
3. Validation: only 2 news-reported breaks give comparable counts. Beltway 8 & Bellfort: reported 74–80, model 38. Tidwell: a miss, explained above. These are directional checks, not proof.
4. The broken-valve flags are the City's records. An independent check (Winter Storm Uri 311 valve requests) found no association, so frame every number as "what the City's records imply".

## Why it matters (the pitch number)
Every isolation segment broken once, weighted by pipe length × 11,119 breaks/yr:
- Neighborhood mains: dead valves multiply customer-hours without water by **2.4**, 1.03 M → 2.49 M a year.
- Citywide dead-valve cost: **3.75 M customer-hours a year** = 1.46 M longer shut-offs on neighborhood mains (City records + connectivity, robust) + 2.29 M extra gushing on large mains (pressure model, uncalibrated). Say the split before a judge asks.
- Repair planner: the top 10 dead valves recover 33% of that cost, top 100 61%, top 500 76%. The top valves sit on large mains, so this rests on the pressure model.
- Don't quote the transmission totals (45 M) as a headline. They come from modeled low pressure while a big main gushes, they depend on the break-size and response-time assumptions, and no valve repair changes them.

**[Cost figures unverified: C will source them before the pitch.]** Replacing a main costs on the order of $1M per mile. Repairing a valve costs a few thousand dollars. The repair planner picks the valves whose repair shrinks outages the most.
