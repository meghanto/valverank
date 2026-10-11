# How it works (learn this cold)

## One sentence
When a main breaks, crews close the nearest valves. If one of those valves is broken, they have to go to the next one out, so more homes lose water. We compute that on Houston's real network.

## The four steps

**1. Network.** The City's GIS has 290,959 pipe lines. Where two pipe ends share a coordinate, they're connected. That gives a graph of 270,826 junctions.

**2. Valves cut the graph.** 166,362 valves are in the GIS. We keep a valve only if it sits within 1 m of a main (102,323 do). The rest are on service lines or hydrant leads, which don't isolate a main.
- Valve at a junction: closing it separates the pipes that meet there.
- Valve in the middle of a pipe: we split the pipe in two at the valve.

**3. Isolation segment.** This is the group of pipes you can't avoid shutting off together, because there's no working valve between them (Walski's term; it's standard in water engineering). We find these with union-find: join every pair of pipe pieces that meet at a point with no working valve. Each resulting group is a segment.

We do this twice:

| Scenario | Rule | Segments | Avg customers out per break |
|---|---|---|---|
| **Paper** | Every valve closes | 82,085 | 11.9 |
| **Real** | Valves marked `INOP` in City records can't close | 64,803 | **25.1** |

Fewer segments means bigger ones: dead valves merge neighboring segments.

**4. Count who's affected.** Each of the 544,011 customer accounts is attached to its nearest main (if within 120 m), and each hydrant to its nearest main (within 40 m). Customers in a segment = the people who lose water when any pipe in that segment breaks.

"Average customers per break" is weighted by pipe length, because longer pipe means more chances to break.

## Terms a judge may use
- **Isolation segment / valve isolation:** step 3.
- **Unintended isolation:** closing a segment can also cut off pipes downstream that have no other supply path. **We don't model this yet.** That's why we underestimate big feeder-main breaks (Tidwell & Antoine: 2,000 reported, model says 5).
- **Hydraulic model:** a pressure and flow simulation (EPANET, WaterGEMS). **We don't do hydraulics.** Ours is connectivity only: who *can* be cut off, not water pressure.
- **Valve exercising:** turning each valve periodically so it doesn't seize. Industry guidance is every valve within about 5 years. 78% of Houston's main valves were last inspected 5+ years before today.

## Honest limits (say them before the judge does)
1. The data is a June 2023 snapshot. Pipes change slowly (~0.3%/yr). Dead valves don't fix themselves, so the inoperable count is a floor.
2. Customer accounts aren't people. An apartment complex can be a single account.
3. Validation: 3 news-reported breaks have outage counts. Beltway 8 & Bellfort: reported 74–80, model 28. Tidwell: a miss, explained above. These are directional checks, not proof.

## Why it matters (the pitch number)
**[Cost figures unverified: C will source them before the pitch.]** Replacing a main costs on the order of $1M per mile. Repairing a valve costs a few thousand dollars. The repair planner picks the valves whose repair shrinks outages the most.
