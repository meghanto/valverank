# Houston water main breaks: reported outage sizes (validation set)

Compiled 2026-10-10 from local news. The data is in `news_breaks.csv`. All events are inside the City of Houston and on city lines. Bellaire (Aug 2026), Cypress, NW Harris County MUDs, Fulshear and Willis were excluded.

| id | date | location | dia (in) | reported affected | duration | boil | valve quote |
|---|---|---|---|---|---|---|---|
| NB01 | 2015-08-13 | Pembridge Dr @ Albin | 8 | none ("end of the block") | ~4 h shutoff | no | yes |
| NB02 | 2016-08-30 | Beltway 8 @ Bellfort | 12 | **74–80 homes and businesses** | ~2 h | no | — |
| NB03 | 2018-06-26 | Memorial Dr (Aura Memorial Apts) | — | 1 apartment complex | ~2 days | no | — |
| NB04 | 2020-02-27 | Clinton Dr @ 610 East Loop | 96 | ~50% of city supply; homes, businesses, TMC | 6–8 h repair, 2-day boil notice | citywide | yes |
| NB05 | 2021-04-30 | "parts of east Houston" (no location) | — | **6,000 residents** | Fri–Mon; boil notice to May 4 | yes | yes (Turner) |
| NB06 | 2022-12-08 | 3700 blk Timmons Ln | 16 | "several residents" (URL: "dozens") | several hours | no | — |
| NB07 | 2023-02-06 | W Tidwell @ Antoine | 16 | **2,000 customers** | ~4 p.m. Mon → 8 p.m. Tue | no | — |
| NB08 | 2023-09-08 | 6622 Keller St (Keller @ Flowers) | — | 9 HISD schools (KPRC: 3) | most of a day | no | "isolated the leak" |
| NB09 | 2024-09-25 | Hwy 3 @ El Dorado (planned) | 42 | homes/businesses S of BW8, no count | several days | no | shutdown quote |
| NB10 | 2025-01-26 | Sabine St, First Ward | 8 | not stated | same day | no | "shut off water" |
| NB11 | 2025-08-24 | 12434 Wellington Park Dr, 77072 | — | residents, no count | hours (one says 24 h) | no | yes ("valves were turned off") |
| NB12 | 2026-07-24 | Richmond Ave W of Chimney Rock | — | "multiple businesses", no count | ~13 h | no | — |

## Reliability notes

- **Few events report a usable count.** Only NB02 (80), NB05 (6,000 residents) and NB07 (2,000 customers) give a number of affected premises or people. NB03 and NB08 give counts of buildings (1 complex, 9 schools). The other events give location, diameter and duration but no size. Houston outlets rarely publish customer counts, and Houston Public Works seems to give a number only for large events.
- **NB07 Tidwell/Antoine numbers conflict.** FOX 26 quotes Houston Public Works: "2,000 customers". The Houston Press quotes HPW spokesperson Erin Jones: "about 2,000 homes". The Chronicle says "2,000 homes and businesses". But the Chronicle's photo captions and the first chron.com piece (written before HPW's figure) say "some 100" / "more than 100 homes". Treat 2,000 as HPW's official customer count and ~100 as early anecdote. Most of the 2,000 had low pressure ("trickle") rather than no water.
- **NB08 schools conflict.** FOX 26 says nine HISD schools; KPRC's headline says three. Neither gives a count of homes.
- **NB04 Clinton Dr is a transmission-main event** (96-inch, from the East/Northeast plant). The outlets disagree on the source plant ("East" in the Chronicle, "Northeast" in FOX 26) and on its share of city supply ("about 50%" vs "40–50%"). Do not use it as a distribution-outage benchmark. It is the only event that describes the valve-isolation process.
- **NB05 has no published break location.** ABC13 is the only source for "6,000 residents". KPRC and FOX 26 give no count. Lat/lon is blank. The water handout site (Cimarron Elementary, 29.7807, -95.1928) is only a weak proxy for the area.
- **NB09 is a planned shutdown** to repair a leak, not an emergency break. It is included for the 42-inch shutdown-extent statement.
- **NB02 location:** Beltway 8 @ Bellfort is near the city limit, but a City of Houston Public Works spokesman handled it, so it was a city line.
- **Geocoding:** Intersections come from OSM via Overpass: the shared node of the two named ways. Addresses come from Nominatim. NB04 is the centroid of the Clinton Dr segment closest to 610 (~±300 m). NB10 uses Sabine St @ Washington Ave because no cross street was reported. NB12 uses Richmond @ Chimney Rock, but the break was a few blocks west of there. NB11 matched to the street, not the house number.
- **Valve difficulty:** no article said a valve failed or could not be closed. The closest are the NB04 search for "the correct valve" and NB05, where the mayor says a valve replacement became a full line replacement. A Feb 2025 ABC13 story (east Houston, construction crew hit a main; first 311 call 6:43 p.m., water turned off 9:30 p.m.) shows slow shut-off. It was left out because it gives no outage count and its exact location was not checked.
