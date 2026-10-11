# News-break ground-truth search log (2026-10-10)

Goal: find City of Houston main-break or planned-shutoff events where a published source gives a count of homes, customers, accounts, households or businesses without water.

**Result:** I found no new event with a count comparable to customer accounts. I appended 4 verified, locatable events with no usable count (NB13–NB16). They are context only and do not validate the model. Across about 900 Houston water-break articles scanned, the only City-of-Houston events with a home or customer count are the two already in the CSV (NB02 Beltway 8/Bellfort, NB07 Tidwell/Antoine), plus one pre-2010 event (see rejected list).

## Method

1. **Web search** (WebSearch tool, standard and extended). Queries:
   - "Houston water main break" "homes without water"
   - "customers without water" Houston main break
   - "Houston Public Works" "planned water outage" customers
   - "households" without water
   - "homes are without water"
   - "100/150/200/300 homes"
   - Kingwood, Clear Lake, Meyerland and Meadowglen/Wilcrest variants
   - site:houstonpublicworks.org and site:houstontx.gov press releases
   - HouPublicWorks tweets; Nextdoor agency posts; council newsletters (campaign-archive)
   - Spanish-language: "casas sin agua" Houston
   - Results were dominated by the same few stories: the 2020 96-inch break, Tidwell, Beltway 8 and the Highway 3 42-inch line.
2. **Exa and Perplexity search:** one Exa query ran, and then both tools failed (Exa hit its rate limit; Perplexity is out of quota).
3. **Google News RSS** (`news.google.com/rss/search`). Ran about 30 queries, some sliced by half-year from 2010 to 2026 and some restricted to a site (khou, fox26, abc13, click2houston, chron, houstonpublicmedia, houstonpress, communityimpact, theleadernews, hcnonline). I read the headlines and followed up on any Houston break story.
4. **Sitemap crawl** of every article URL, filtered by slug keywords, then fetched each article and regex-scanned the text for "N homes/customers/households/businesses/residents" near outage words:
   - abc13 (2008–2026 web and news sitemaps)
   - houstonchronicle.com (3,497 sitemap files)
   - chron.com (360 monthly sitemaps)
   - Community Impact (188 monthly sitemaps)
   - Fox 26 (46 sitemap pages)
   - Houston Public Media; Houston Press
   - About 600 Houston-relevant articles scanned.
5. **Wayback CDX enumeration** for sites with no sitemap or that block direct fetches: khou.com (curl and WebFetch both get 403; I read about 20 articles via Wayback), click2houston.com (pre-2019), myfoxhouston.com, houstonpublicworks.org, publicworks.houstontx.gov, houstontx.gov/mayor/press.
6. **Official sources:**
   - cityofhouston.news WordPress API: 248 water posts, no outage counts.
   - houstonpublicworks.org: news-and-public-notices, /boil-water, /public-notification-water-shut-offs.
   - City ArcGIS org (services.arcgis.com/NummVBqZSIJKUeVR): only 2020 road-closure layers; no outage layer.
   - ArcGIS Online search: nothing.
   - HPW X/Twitter syndication endpoint: HTTP 429.
   - Nextdoor HPW agency page: login wall.

## Most and least productive sources

- **Most productive (for any detail):** Houston Chronicle and chron.com breaking-news pages. They carry the most specific locations and sometimes pipe sizes. The full article body is in the page's embedded JSON-LD, so it can be read even when the page itself is paywalled.
- **Counts appear almost only when HPW's PIO gives one to FOX 26, KHOU, ABC13 or the Houston Press.** Tidwell (2,000) is the only such case since 2016.
- **Unproductive:** HPW's own web pages (no outage notices archived), the City newsroom, City ArcGIS, and Community Impact (Houston editions cover only citywide boil notices).
- Planned shutoff notices go out by door hanger, Nextdoor and 311, and none of those are public or archived.

## Events added (verified, no comparable count)

- **NB13** 2014-10-14, 2300 block of Bastrop St, transmission-line valve leak. Chronicle: "roughly 40,000 residents" threatened with low pressure or outage. The count is of residents, it was a threat rather than an actual outage, and it describes a transmission-pressure event, not a valve-isolation segment.
- **NB14** 2015-09-17, S Braeswood at Stella Link, contractor bore. "some customers" with no water; restored 7:30 p.m. (Chronicle; KPRC via Wayback).
- **NB15** 2016-02-19, Allen Pkwy at Taft, 8- or 12-inch line struck. "some of the businesses would be out of water" (Chronicle).
- **NB16** 2024-02-08, planned overnight tie-in outage, North Loop to W 25th St, Couch St to Rutland St (Memorial Heights TIRZ via Chronicle). Boundaries are published but no count. It could still serve an area-based check.

## Rejected (one line each)

- 2004-04-10 SE Houston, "About 500 homes" without water, 24-inch main (chron.com 500-homes-without-water-after-main-breaks-1474510): has a count, but it is outside the 2010–2026 window and 19 years before the network snapshot. Kept as a lead; see below.
- 2023-02-07 Chronicle/chron "more than 100 homes" / "some 100 homes", Tidwell & Antoine: duplicate of NB07 (those quotes are already recorded there).
- 2023-02-07 KHOU "around 2,000 customers" (via Wayback) and ABC13 12783315 "About 2,000 water customers": duplicates of NB07.
- 2016-08-30 FOX 26 water-main-break-in-southwest-houston: duplicate of NB02.
- 2026-08-18 S Rice Ave & Pine St, Bellaire High School and Horn Elementary: City of Bellaire water system, not Houston.
- 2013-01 NW Harris County "about 100 homes" and an apartment complex (chron champions-klein): a MUD system, not the City.
- 2013-04-22 HPM "350 Homes In West Are Without Water": West, Texas (fertilizer plant explosion).
- 2021-02 Uri items (Independence Heights, apartments, "roughly 200 homes" Harris County neighborhood on FOX 26): citywide freeze, not a single isolation.
- 2020-02-27 96-inch East Loop (already NB04), with "7,600 homes" in Clinton Park: that figure counts homes in the neighbourhood, not homes without water.
- 2021-04-30 east Houston boil notice: already NB05.
- 2024-09-24 Highway 3 42-inch planned shutdown: already NB09; map only, no count.
- 2018-02/03 102-inch shutdown north of I-10 and 66-inch Will Clayton boil advisory (KPRC): ZIP codes and pressure only, no count.
- 2017-07-19 Kingwood hydrant-replacement outages (chron 11300082): list of subdivisions, no count, no dates per street.
- 2017-12-01 Southwest Pump Station valve replacement (HPM): pressure only.
- 2015-08-07 Hobby Airport, 2024-07-22 and 2026-05-07 Space Center Houston, 2025-01-10 HISD Wisdom HS, 2023-09-08 HISD schools (NB08): single facilities or schools, not customer counts.
- 2025-03-27 Yale St & Center St (ABC13/KPRC/KHOU): businesses closed by flooding; no statement on loss of service and no count.
- 2025-08-24 Wellington Park (KHOU/ABC13): duplicate of NB11.
- 2016-09-28 Clinton Dr 8-ft transmission repair (KPRC): no outage.
- 2022-01-21 W 43rd & Watonga (ABC13): city rerouted supply, "no one is going without it".
- 2025-07-30 Blalock Rd (ABC13/KHOU/FOX 26): rerouted, no customers affected.
- 2024-01-10 TMC 54-inch wastewater collapse damaging a water line: HPW says water service was not interrupted.
- 2023-08-23 downtown criminal courthouse and "several businesses" outage (FOX 26/Chronicle): no count; break location vague.
- 2023-10-11 Sycamore Valley (KPRC): "several residents", multi-day; no count or break location.
- 2024-10-07 Nantucket at Fannin Station apartments, 72 h (FOX 26): one private complex; cause unclear.
- 2022-08 Royalton at River Oaks high-rise: a private building line.
- 2022-12-09 Timmons Ln: already NB06.
- 2026-07-24 Richmond Ave: already NB12.
- 2026-02-10 Round Spring Dr, Kingwood (KPRC/KHOU): flooding only; no outage statement.
- 2026-02-10 Bissonnet; 2026-01-25 Chimney Rock/Westheimer; 2026-08-12 downtown near Daikin Park; 2025-05-27 Griggs; 2024-06-12 Bissonnet & Morningside: flooding stories, no outage count.
- Hitchcock, La Porte, Willis, Arcola, Beaumont, Deer Park, Fulshear, Tomball, Pasadena, League City and other non-City systems: excluded.
- Spam/aggregator pages (vestcallcenter.nbxsoluciones.com, proposable staging, kobo.nacsa.gov.sl, mojo.iimu.ac.in, solatatech.com) claiming 36-inch breaks and household counts: unsourced, likely generated; ignored.

## Unverified leads (not fetched or not readable)

- https://www.chron.com/news/houston-texas/article/500-homes-without-water-after-main-breaks-1474510.php — fetched and verified ("About 500 homes in southeast Houston... broken 24-inch water main"), but the event is from 2004. Add it only if pre-2010 events are acceptable. The article gives no street; SE Houston only.
- https://www.khou.com/article/news/local/temporary-water-service-outage-for-heights-residents-businesses/285-d3c5394d-2de6-4152-85fc-a21b97c9208e — planned Heights outage (probably the same as NB16); KHOU returns 403 and Wayback has no good snapshot.
- https://www.khou.com/article/news/local/downtown-houston-apartment-water-line-break/285-284ed209-656e-4a74-b83f-423c9328f1ea — 403, not read.
- https://www.khou.com/article/news/local/fiber-optic-cable-water-line-problems/285-b6fa0f60-c781-419e-8ac4-32f7a6c738e7 — 403, not read.
- https://www.khou.com/article/news/local/water-shooting-high-into-the-air-from-broken-water-line-in-galleria-area/285-995067de-4655-4e83-add2-6d7a7e2f07c3 — Wayback snapshot 20260125143316 exists; not read.
- https://abc13.com/archive/9361854 (Meadowglen & Wilcrest) and https://abc13.com/archive/9285661 (Fondren & W Airport) — water was cut to "some buildings and residents"; undated pages, no count.
- https://www.houstonchronicle.com/neighborhood/humble-kingwood/article/Public-Works-repairing-water-line-break-that-is-16304900.php — 2021-07-09 Kingwood, "Several Kingwood residents are without water"; the body was truncated, so I could not confirm the street.
- http://myfoxhouston.com/story/26619452/galleria-area-residents-left-with-water-main-break-lake-for-days — found in the Wayback CDX listing; not read.
- HPW posts on X (@HouPublicWorks) and Nextdoor (agency-detail/tx/houston/houston-public-works-and-engineering) probably carry PIO customer counts for many repairs. They need a logged-in browser or the X API, which this session did not have.

## Recommendation

News coverage will not produce 15 or more comparable events: Houston outlets almost never print a customer count. Better routes:

- A Texas Public Information Act request to HPW for work orders with "customers out of service" / valve-closure records.
- HPW's X archive through an authenticated client.
- The 311 sewer and water datasets, inferring outage areas from clusters of no-water calls.
