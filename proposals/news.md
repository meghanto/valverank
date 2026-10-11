# News and evidence dossier: GreaseTrace, CrossingClear, Shutoff

Compiled 2026-10-10. Every claim has a verification status:

- **✅ verified**: we opened the primary source or article and the figure matches
- **⚠️ corrected**: the source says something different from what was previously circulated; the correct value is given
- **🔬 our data**: computed by us from City/FRA data on 2026-10-10
- **❓ unverified**: from search summaries or vendor material only; don't put it on a slide without opening the source

Each section ends with **counter-arguments a judge may raise** and the rebuttal.

---

## 0. Findings that change the pitches

| # | Finding | Impact |
|---|---|---|
| 1 | **The City's public water GIS (pipes, valves, hydrants) is a snapshot frozen around June 2023.** Last edit: 2023-06-05. The newest valve condition record is 2023-03-02. 🔬 | **Shutoff** must phrase claims as "according to the City's last published records (2023)". Revised: this is a moderate weakness, not a fatal one (see §3.4). |
| 2 | Published valve inspections fell **32,862 (2020) → 12,282 (2022) → 735 (2023) → 0 after**. 🔬 | Either the program slowed or publishing stopped. We can't tell which; say so. |
| 3 | Of the 13,017 valves the City inspected in 2022–23, **2,634 (20%) were inoperable**. 🔬 | A cleaner and more defensible stat than "13% of all valves" |
| 4 | **Grease + wipes caused 60% of public SSOs in FY2025**, not "70%". Grease alone was 38%. On sewer *mains* only, grease caused 61%. ✅ (City FY25 annual report) | GreaseTrace must cite the 60%. The City web page's "70%" is outdated. |
| 5 | The City's FOG program ran **30,032 grease-interceptor inspections** and **5,105 enforcement actions** in FY25, yet grease SSOs rose **550 → 686** (FY24 → FY25). ✅ | GreaseTrace's core argument: inspections are broad but not aimed at the sources of overflows |
| 6 | The SSO volume field `TOT_VOL_L` is **in gallons**. The Goodyear Dr spill the press reported as ">100,000 gallons" is recorded as 172,340. 🔬 | Volume claims are now usable |
| 7 | The City's "530 blocked-crossing reports in July 2025" matches the FRA portal's **549** for that month. 🔬 | The City appears to use FRA data; our dataset is the same one the City uses |
| 8 | Train Watch showed false "blocked" readings in July 2026 (crossings red all day with no train). ✅ | CrossingClear must account for uncertain sensor readings. This is also a selling point. |
| 9 | Sergio Rodriguez, a 15-year-old Milby High School student, was **killed by a train walking to school in Dec 2024**. ✅ | The CrossingClear human story is in Houston, not only Polk County. It was a pedestrian death, not an EMS delay; keep that distinction. |

---

## 1. GreaseTrace: sewage overflows

### 1.1 Primary source

**City of Houston FY2025 Wastewater Consent Decree Annual Report** (Jul 1 2024 – Jun 30 2025): <https://www.houstonpublicworks.org/media/5746/download> ✅

Public SSOs by cause (mains + laterals):

| Fiscal year | Grease | Rags/Wipes | Structural | Wet weather | Lift station | Other | **Total** |
|---|---|---|---|---|---|---|---|
| FY22 | 741 | 185 | 262 | 25 | 5 | 48 | **1,266** |
| FY23 | 671 | 169 | 284 | 33 | 13 | 65 | **1,235** |
| FY24 | 550 | 301 | 388 | 42 | 7 | 89 | **1,377** |
| FY25 | 686 | 395 | 515 | 34 | 10 | 173* | **1,813*** |

\*FY25 includes 102 SSOs caused by Hurricane Beryl power outages.

| Metric (FY25 unless noted) | Value |
|---|---|
| Grease + wipes share | 73% (FY22) → 68% → 62% → **60% (FY25)** |
| Volume spilled | 1,636,492 gal (FY24); 1,327,642 gal FY25 excluding Beryl, **2,635,286 gal** including it |
| SSOs reaching or next to water | **570 of 1,813** |
| Repeat-SSO locations | **112** (FY24 and FY25) |
| Permitted FOG generators | **19,210** |
| Grease-interceptor inspections | **30,032** |
| FOG enforcement actions | **5,105** |
| Smart manhole monitors | 474 installed in FY25; 2,969 total |
| Private laterals remediated | 518 after notice, 1,001 after a Health Dept inspection, 149 after a fine |

### 1.2 Consent decree facts

| Fact | Status | Source |
|---|---|---|
| DOJ/EPA settlement announced **Aug 27 2019**; complaint filed Sep 20 2018; **$4.4M civil penalty** (split with Texas) | ✅ | [DOJ](https://www.justice.gov/opa/pr/houston-texas-agrees-implement-comprehensive-measures-aimed-eliminating-sanitary-sewer-0) |
| DOJ: ~$2B over 15 years. **City: $6B (2019 est.) → $9B (2024 draft revised)**. These are different scopes; cite both with their source. | ✅ | DOJ; [City council deck Aug 2024](https://www.houstontx.gov/council/committees/servicedelivery/2024_08_28/consent_decree.pdf) |
| ~$1B spent and $2.5M in stipulated penalties as of Aug 2024; decree runs to **2036** | ✅ | City council deck |
| Requires ≥150 miles/yr of sewer **rehabilitation**, plus two cleaning programs, one targeting FOG areas | ✅ (150 mi is rehab, not cleaning) | DOJ |
| City claims smart manholes prevented **639 potential SSOs** | ✅ (City claim) | City council deck |
| Council deck quote: *"The majority of SSOs are caused by FOG & rags/wipes that customers improperly dispose of."* | ✅ | City council deck |

### 1.3 Our data checks 🔬

| Check | Result |
|---|---|
| Public SSOs by calendar year (City layer) | 2021: 1,301 · 2022: 1,237 · 2023: 1,203 · **2024: 1,697** · 2025: 1,571 |
| Calendar vs. fiscal | The widely quoted "1,377 in 2024" is **fiscal 2024** (Jul 2023–Jun 2024), not calendar 2024. Hoodline got this wrong. |
| Seasonality, 2021–2025 all SSOs by month | Jan 2,263 · Feb 2,246 · … · Aug **1,003** → winter is **~2.2×** the late-summer low. Matches the City's "twice as many in winter". |
| 2025 public SSOs by cause | Grease 667 (42%) · wipes/rags 350 (22%) |
| 2025 by watershed (all SSOs) | **Brays 1,025** · Sims 911 · Buffalo 583 · White Oak 531 · Greens 416 |
| Volume units | Gallons (Goodyear Dr: 172,340 in the data vs. ">100,000 gal" in the press) |
| The data records private grease-trap overflows | e.g. 9810 Gulf Fwy, 2026-01-03, structure type "Private Grease Trap", 23,020 gal |

### 1.4 Articles

| Date | Outlet | Headline | Status | Use |
|---|---|---|---|---|
| 2026-08-31 | Axios Houston (Shafaq Patel) | [Houston waterways repeatedly test high for E. coli](https://www.axios.com/local/houston/2026/08/31/houston-polluted-ecoli-bayous) | ✅ archive copy | Environment Texas found **Buffalo, White Oak and Carpenters bayous unsafe on every day tested** in 2024–25. Opening hook. |
| 2026-08-19 | KPRC | [New report warns of E. coli contamination in Houston bayous](https://www.click2houston.com/news/local/2026/08/19/new-report-warns-of-e-coli-contamination-in-houston-bayous-and-texas-waterways/) | ✅ | Same report; Bayou City Waterkeeper and Harris County Pollution Control |
| 2026-07 | Hoodline | [Raw sewage nightmare has Woodland Heights block fuming](https://hoodline.com/2026/07/raw-sewage-nightmare-has-woodland-heights-block-fuming-on-wrightwood/) | ❓ (AI-assisted outlet) | Resident impact |
| 2026-06-15 | Bayou City Waterkeeper | [What Houston's FY27 budget means for our water infrastructure](https://bayoucitywaterkeeper.org/what-houstons-fy27-budget-means-for-our-water-infrastructure/) | ✅ | ~1,200–1,600 public SSOs/yr; budget pressure |
| 2026-05 | CultureMap | [Betelgeuse Betelgeuse owner arrested](https://houston.culturemap.com/news/restaurants-bars/chris-cusack-betelgeuse-arrested-response/) | ✅ | Closest recent grease-trap enforcement story. Sensitive; mention only as "enforcement is blunt". |
| 2026-04-30 | Hoodline | [Houston's $2B sewer fix: progress or just more spills?](https://hoodline.com/2026/04/houston-s-2-billion-sewer-fix-progress-or-just-more-spills/) | ⚠️ | Quote (Kristen Schlemmer, Waterkeeper): *"The city's reporting is just not clear enough."* It confuses FY with calendar 2024 and names no specific missed deadlines. |
| 2026-04-01 | Bayou City Waterkeeper | [Five years of holding the City accountable](https://bayoucitywaterkeeper.org/justice-in-the-sewers-2026/) | ✅ | 1,377 (FY24) highest since the decree began; private-lateral gap |
| 2026-01-30 | FOX 26 | [Sewage flowing from online grocery giant into Brays Bayou](https://www.fox26houston.com/news/raw-sewage-houston-bayou-warehouse-illegal-dumping-brays-weee-distribution) | ✅ | 3350 Rogerdale Rd. Traced with **red tracer dye** by HPD, Public Works, HFD HazMat, Health, Harris County and TCEQ. No charges yet. **This was an illicit discharge, not grease.** Use it only as the "manual tracing takes six agencies" analogy. |
| 2026-01-02 | FOX 26 / ABC13 / KHOU | [100K-gallon spill into Sims Bayou](https://www.fox26houston.com/news/houston-boil-water-spill-100000-gallons-sims-bayou-2026-january) | ✅ | Goodyear Dr; **structural failure, not grease.** Good for the "this data is real" check; don't use as a grease example. |
| 2019-08-27 | DOJ | [Houston agrees to comprehensive measures…](https://www.justice.gov/opa/pr/houston-texas-agrees-implement-comprehensive-measures-aimed-eliminating-sanitary-sewer-0) | ✅ | Legal mandate |
| — | Houston Public Works | [Protect Our Pipes](https://houstonpublicworks.org/protect-our-pipes) | ⚠️ | Says "70% … caused by … fats, oils and grease". Outdated against FY25's 60% grease + wipes. Quote: *"Houston Public Works responds to twice as many sewer overflows"* in winter. |
| — | Houston Permitting Center | [FOG / special waste rules](https://houstonpermittingcenter.org/hhd1017) | ✅ | Code §47-512(b): grease traps pumped **every 90 days**; annual permit; unannounced inspections |

### 1.5 Counter-arguments and rebuttals

| Judge says | Evidence | Rebuttal |
|---|---|---|
| "The City already has a FOG program." | ✅ 19,210 permitted generators, 30,032 inspections, 5,105 enforcement actions (FY25) | And grease SSOs still rose 550 → 686. Inspections are site-by-site paperwork checks. Nothing links a downstream overflow to the upstream generators. We rank which of the 19,210 drain toward the 112 repeat-SSO sites. |
| "Most big spills are rain, not grease." | ✅ Wet-weather SSOs are only 25–42/yr by count, but storms dominate volume (Beryl ≈ half of FY25 gallons) | Grease drives how *often* spills happen; storms drive how *big* the largest are. We target the frequent, preventable kind. |
| "Structural failures and wipes are rising faster than grease." | ✅ Structural 262 → 515, wipes 185 → 395 (FY22 → FY25) | True. The tool attributes blockages by cause (grease, wipes, structural) rather than assuming grease. Rename the framing to "overflow source tracing" if needed. |
| "You're blaming restaurants." | — | Rankings are inspection priorities, not accusations. Household grease and wipes are major contributors too (the "Protect Our Pipes" campaign targets residents). |
| "The City has smart manholes." | ✅ 2,969 installed | They alert at the manhole. We explain *upstream* causes and choose where to act before the alert. The two are complementary. |

### 1.6 Pitch line (all claims verified)

> *"Last fiscal year Houston's public sewers overflowed 1,813 times, and 570 of those spills reached or sat next to water. The City inspected grease traps 30,000 times, yet grease overflows went **up**. Bayous like Buffalo and White Oak tested unsafe for E. coli on every day sampled. GreaseTrace connects each overflow to the pipes and grease sources upstream of it, so those 30,000 inspections land where the overflows actually come from."*

---

## 2. CrossingClear: blocked train crossings

### 2.1 Verified facts

| Fact | Status | Source |
|---|---|---|
| ~**1,800** blocked crossings/yr in Houston, **98% in the East End** | ✅ (vendor white paper) | [TRAINFO white paper](https://trainfo.ca/wp-content/uploads/47415-TR-Trainfo-White-Paper-FINAL-Web.pdf) |
| Lawndale St blocked **107 times ≥1 h in 26 days**; 32 of them over 3 h; longest ~15 h. City cameras + LiDAR; a spot audit found 100% were real trains. | ✅ | [Houston Chronicle, May 12 2022](https://www.houstonchronicle.com/news/houston-texas/transportation/article/Cameras-data-on-blocked-train-crossings-shows-17168866.php) |
| HFD logged **3,200 detours** 2019–2022 (Chief Peña) | ✅ | Same |
| HFD averaged **96 delays/reroutes per month**, adding up to 10 min per response; Station 18 has a camera to check for trains before leaving | ✅ | [Houston Landing, Mar 21 2023](https://www.houstonlanding.org/stopped-trains-block-houston-traffic-union-pacific/) |
| Houston had **3,429 FRA reports Feb 2022–Feb 2023, more than all of Ohio**; Leeland and Milby 356 each | ✅ | Same |
| Firefighters can't reach scenes on time **~100 times/month** | ✅ | [Community Impact, Aug 21 2025](https://communityimpact.com/houston/heights-river-oaks-montrose/government/2025/08/21/houston-launches-train-watch-to-provide-real-time-updates-on-blocked-train-crossings/) |
| Train Watch: **$3.4M** USDOT grant (2024), **70 sensors**, covers "key" crossings only; built first for police and fire | ✅ | Community Impact; [Houston Chronicle, Aug 17 2025](https://www.houstonchronicle.com/news/houston-texas/article/train-watch-dashboard-20816310.php) |
| Train Watch **false positives**: crossings shown blocked all day with no train (ABC13 crews checked); a gate down 6+ h with no train | ✅ | [ABC13, Jul 28 2026](https://abc13.com/post/east-houston-groups-cameras-capture-someone-crossing-slow-moving-train/19587157/); [Hoodline, Jul 23 2026](https://hoodline.com/2026/07/ghost-train-warnings-snarl-east-end-streets-for-hours/) |
| **Sergio Rodriguez**, 15, Milby High student, killed by a train walking to school, Dec 2024. Union Pacific quietly ended the Milby school-hours curfew. Rep. Sylvia Garcia reintroduced the **D-BLOC Act** (10-minute limit, FRA investigation of repeat violators, civil penalties). | ✅ | [Houston Chronicle, Dec 18 2025](https://www.houstonchronicle.com/news/houston-texas/education/hisd/article/sergio-rodriguez-rail-crossings-21249543.php) |
| D-BLOC Act = **H.R. 6790**, introduced Dec 17 2025, sitting in committee | ✅ | Congress.gov via agent |
| Houston has **700+ at-grade crossings**; **40%+ of HISD campuses** are near rail crossings | ✅ | Chronicle, Dec 2025 |
| TxDOT SB 1555 first awards: $160.4M total; Houston's **Griggs–Long–Mykawa** grade separation gets $40M (of a $165.2M project) | ✅ | [TxDOT commission, Feb 26 2026](https://www.txdot.gov/content/dam/docs/commission/2026/0226/7.pdf) |
| Federal: $36.9M (2023) West Belt underpasses; $2M (Jan 2025) East End Triangle study of 14 crossings | ✅ | agent (federal grant listings) |
| 2019: ambulance rerouted while Jose Carpio, 24, was pinned under his car on Jefferson St; neighbors did CPR and he survived | ✅ | [ABC13, Aug 9 2019](https://abc13.com/post/first-responders-delayed-train-blocks-intersection-east-houston/5453276/) |
| K'Twon Franklin, 11 weeks, Polk County (~80 mi from Houston), Sept 2021: 30+ min delay behind a train, died two days later | ✅ | [ABC13, Oct 6 2023](https://abc13.com/amp/post/union-pacific-railroad-crossings-closed-polk-county-legget-texas/13871299/); [Stars and Stripes / WaPo, May 26 2023](https://stripes.com/theaters/us/2023-05-26/texas-long-trains-delays-first-responders-10246439.html) |
| National: 1,400+ FRA reports in one year of trains blocking first responders; Union Pacific's average train length up ~20% 2019–2023 | ✅ | WaPo via Stars and Stripes |

**Crossing counts conflict:** 700+ (Chronicle), 584 public at-grade (FRA inventory, our query), 403 (TRAINFO). The definitions differ (public vs. private, open vs. closed). Cite the FRA number for our analysis.

### 2.2 Our data checks 🔬

| Check | Result |
|---|---|
| FRA Houston reports | 24,442 (Feb 2020 – Oct 10 2026); 376 distinct crossings |
| First-responder-blocked flag | 11,536 (47%). **2025 mean: 172/month**, comparable to HFD's own ~96–100/month (FRA flags are observer reports, not HFD-confirmed) |
| Trend | 2025 monthly reports 259–657; **May 2026: 944 reports, 729 with the first-responder flag** (the peak month) |
| Possible duplicates | 5,684 reports share a crossing and hour with another report. Deduplicate before modelling. |
| July 2025 | FRA 549 vs. City's "530 reports". The City likely uses the same FRA data. |
| Our Train Watch recorder | Since Sat 2:50 PM: **Leeland St reported "blocked" for ~7 minutes**. Given the July false positives, treat it as unconfirmed. |

### 2.2b Satori Defense: a second commercial competitor, checked against FRA data

[Satori Defense, "Houston Rail Blockages Hit 3-Year High in March 2026"](https://satoridefense.com/blog/houston-rail-blockages-march-2026) (Mar 24 2026; no named author; marketing post with a consultation form, no pricing).

Satori lists customer segments that include **emergency management and fire**, plus drayage, insurance, petrochemical safety and defense. That is CrossingClear's target buyer.

| Satori claim | Our check against FRA reports 🔬 | Verdict |
|---|---|---|
| "57 TRAINFO-monitored crossings" in Houston | Train Watch's live feed has **56** crossings | ❓ Suggests Train Watch and TRAINFO's Houston sensors are the same or overlapping network, and that Satori resells it. Unconfirmed. |
| Blockages hit a "3-year high" in March 2026 | FRA reports in March: 2024 **1,078**, 2025 564, 2026 **704** (deduplicated: 780 / 426 / 526). Q1: 2024 2,159 > 2026 1,495. | ⚠️ **Not a 3-year high in FRA data.** March 2024 was higher. Satori uses different (sensor) data and publishes no numbers, so the claim can't be verified. |
| Average blockage over 25 min | FRA Q1 2026: most reports 31–60 min (394) or 1–2 h (344) | ✅ Consistent. FRA skews longer because people report long blocks. |
| Union Pacific accounts for the majority | FRA: UP **18,467** of ~18.8k deduplicated reports (98%) | ✅ Consistent |
| Peaks at 7–9 AM and 2–4 PM | FRA deduplicated 2025+: 7–9 AM is **7.4%** of reports and 2–4 PM is 8.0%. The actual peaks are **4–7 PM** (17:00 = highest hour) and **1–3 AM**. | ⚠️ Disagrees. Could be sensor vs. crowd-report bias; report it as such. |
| "200+ motor carriers" in Houston | — | ❓ Implausibly low for the Houston metro; marketing figure |

**What this means for CrossingClear:**
- **Originality drops further.** At least two companies (TRAINFO, Satori) sell real-time Houston crossing intelligence, and one of them names fire and emergency management as customers.
- **The business case strengthens.** Paying commercial demand exists in Houston (logistics, petrochemical, emergency services).
- **The differentiation is narrower.** It must be: open and public, measuring coverage loss per address, using federal history plus live sensors, and auditable, unlike vendor marketing that publishes no numbers. Our FRA cross-check above is a demo of that auditability: "they claim X; the public record shows Y."

### 2.3 Counter-arguments and rebuttals

| Judge says | Evidence | Rebuttal |
|---|---|---|
| "Satori Defense already sells this to fire and emergency management." | ✅ Marketing page lists those segments; publishes no numbers | Vendors sell live alerts from closed data. We publish an open, auditable coverage analysis, and their March 2026 "3-year high" doesn't hold up against the FRA record. |
| "TRAINFO already does this for Houston." | ✅ TRAINFO ran sensors in the City's 2022–23 pilot and sells dispatch integration | Their white paper is vendor marketing. There is no evidence TRAINFO powers Train Watch today or that HFD dispatch uses it in production. We are not a sensor company; we answer *who loses coverage* and *which crossing to fix first*. |
| "Train Watch exists." | ✅ But it covers key crossings only, gives no routing or coverage, and showed false positives in Jul 2026 | We combine Train Watch (live) with FRA history (probabilistic), so one bad sensor doesn't break routing. |
| "FRA reports are crowd-sourced noise." | ✅ Self-reported, no federal definition, duplicates | Validated in aggregate: FRA July 2025 matches the City's count, and the Lawndale sensor audit confirmed real blockages. We deduplicate and show uncertainty. |
| "Grade separations are the real fix." | ✅ Griggs–Long–Mykawa costs $165M, and others "might be decades in the making" | Agreed. We rank which crossings to separate first by homes regaining coverage, and handle routing until then. |
| "No Houston EMS death documented." | ✅ True | Don't claim one. Use HFD's own delay counts and the Carpio incident. Sergio Rodriguez's death is a pedestrian story; use it for "why this matters", not as an EMS case. |

### 2.4 Pitch line

> *"Houston's Fire Department says about a hundred times a month a train keeps firefighters from reaching a call. Last May, residents filed 729 federal reports of first responders stuck at crossings in one month. The City spent $3.4M on sensors to see where trains are. CrossingClear answers the next question: which homes are out of reach right now, and which crossing to fix first."*

---

## 3. Shutoff: water mains and valves

### 3.1 Verified facts

| Fact | Status | Source |
|---|---|---|
| ~**31.8B gallons** lost in 2023. Leaks: 9,143 (2020) → 11,831 → 12,128 → **13,911 (2023)**. | ✅ | [ABC13, Sep 3 2024](https://abc13.com/post/houston-public-works-testify-citys-water-issues-inquire-financial-compensation-fix-infrastructure-issues/15260907/) |
| **850 miles replaced in a decade (~6%)** vs. 2,800 miles (20%) ideal | ⚠️ This is in the **Sep 2024** ABC13 article above, not the 2023 "13 Investigates" piece (fixed in `03-shutoff`) | Same |
| Water-line replacement **0.3% in FY25** vs. 3% target; average leak repair **41 days** | ✅ | [Bayou City Waterkeeper, Jun 15 2026](https://bayoucitywaterkeeper.org/what-houstons-fy27-budget-means-for-our-water-infrastructure/) (citing an HPW presentation) |
| Leaks were the **#1 311 complaint for the 6th straight year** (2024). ~$15B needed (Water Director Greg Eyerly). $25M across eight repair contracts. ~36B gal lost "since 2023". $480M ask to the Legislature. | ✅ | [Houston Chronicle, Jan 19 2025](https://www.houstonchronicle.com/politics/houston/article/water-leaks-311-complaint-20022932.php) |
| **2022, Councilmember Kamin:** more main breaks *"because of aging valves"*; council sought $22–25M; ~$17.3M approved for repairs and $4.1M for inspections | ✅ | [ABC13, Nov 30 2022](https://abc13.com/post/houston-water-lines-main-break-report-outage-city-council-meeting/12510774/) |
| One 16-inch break at Tidwell & Antoine: **2,000 homes and businesses** without water or with a trickle (~20 h); two schools closed. The leak wasn't found for ~a day; **valves not mentioned**. | ✅ | [Houston Chronicle, Feb 7 2023](https://www.houstonchronicle.com/news/houston-texas/article/houston-water-outage-hundreds-lose-service-17769053.php) |
| West Houston leaks ran 2+ weeks despite several 311 reports; fixed only after KPRC called. Quote: *"This is usable water, literally going down the drain."* | ✅ | [KPRC, Oct 1 2026](https://www.click2houston.com/news/local/2026/10/02/west-houston-residents-watched-water-pour-into-streets-for-weeks-before-pipe-repairs/) |
| **Counterpoint:** leak complaints falling, 44k (2023) → ~36k (2024) → ~35k (2025); 510 tagged leaks awaiting repair | ✅ | [ABC13, Jan 6 2026](https://abc13.com/amp/post/311-data-shows-water-leak-complaints-declining-despite-neighbors-are-waiting-repairs/18363304/) |
| Houston has bid valve work (2024 valve replacement contract; 2026 bids that include valves) but **no public valve-exercising program found** | ✅ | [Council agenda Mar 6 2024](https://houstontx.gov/citysec/ABForms/2024/030624.pdf) |
| The 2025 Texas water fund is **Prop 4** ($1B/yr for 20 years from 2027), not Prop 2 | ⚠️ | [TWDB](https://www.twdb.texas.gov/financial/programs/twf/index.asp) |

### 3.2 Valve failures elsewhere (proof that the mechanism is real)

| City | What happened | Source |
|---|---|---|
| **Atlanta, June 2024** | The valve directly under the rupture couldn't be operated, so crews plugged pipes by hand and the outage lasted ~2 days. The commissioner later said failed shutoff valves caused widespread outages; ~66,000 valves; the City hired outside valve testers. | [Civic Atlanta, Oct 2024](https://civicatlanta.org/blog/2024-10-20-water-supply-valves-update); [Atlanta News First](https://www.atlantanewsfirst.com/2024/06/01/live-updates-everything-we-know-about-atlantas-water-main-breaks/) |
| **Jackson, MS, Dec 2022** | Interim manager Ted Henifin: *"We don't know where the valves are, we don't know what position they're in."* | [NPR](https://www.npr.org/2022/12/31/1145966097/water-problems-jackson-mississippi-explanation) |
| Benchmarks | No AWWA "typical %". Ohio EPA: exercise every valve every ≤5 years. Xylem (vendor): ~40% inoperable or unlocatable. Riverside, IL: ~30%. | [Ohio EPA guidance](https://dam.assets.ohio.gov/image/upload/epa.ohio.gov/Portals/28/documents/pws/valve-exercising-program-guidance.pdf) |

### 3.3 Our data checks 🔬

| Check | Result |
|---|---|
| Valve records | 166,362 total; **21,574 INOP** (13%); 15,781 "cannot locate"; **17,509 INOP are in-line/main valves** (not hydrant leads) |
| **Freshness** | Valve layer last edited **2023-06-05**; mains 2023-05-30. The entire `UtilityAnalysis_gx` service and the separate `Houston_WaterMain` copy (edited 2023-03-06) are **2023 snapshots**. |
| Inspection activity in the public record | 2018: 6,249 · 2019: 3,610 · **2020: 32,862** · 2021: 16,473 · 2022: 12,282 · 2023: 735 · 2024–26: **0** |
| Inoperable rate among recently inspected valves | **20%** of valves inspected 2022–23 (2,634 / 13,017) |
| Benchmark comparison | Houston's recorded 13% is **below** industry anecdotes (30–40%). Frame it as a floor: only inspected valves can be flagged. |

### 3.3b Deep-dive tests (2026-10-10) 🔬

| Test | Result | Meaning |
|---|---|---|
| **Is there a fresher copy anywhere?** Searched every water/valve service in the City's ArcGIS org and all public ArcGIS Online items | Every copy (`UtilityAnalysis_gx`, `Houston_Water_Main`, `wHydrant`, `sGravityMain`, the hydrant view) traces to the **same ~June 2023 extract** | Staleness can't be fixed with public data |
| **Right denominator.** In-line (main-isolation) valves only | **79,247** in-line valves; **79% inspected**; **17,401 (28%) of inspected recorded inoperable** | Use this stat. It matches industry anecdotes (30–40%), so Houston isn't an outlier, just large. |
| What are the 96,732 "never inspected" valves? | 98% of subtype 33 and 100% of VALVE_USE=NULL were never inspected, mostly hydrant-lead and service valves; only **21%** of in-line valves were never inspected | Drop the "58% never inspected" framing; it's mostly non-critical valves |
| **Age gradient** (inspected valves, all uses) | Inoperable: pre-1950 **48%** · 1960s 40% · 1970s 35% · 1980s–90s 30% · 2000s 27% · 2010+ **19%** | Strong, explainable pattern; supports the "aging valves" narrative (Kamin, 2022) |
| Diameter | 4–7″: 40% · 8″: 27% · 10–12″: 33% | Small valves worse |
| **Winter Storm Uri validation**: are the 3,420 "Water Main Valve" 311 requests (Feb 2021) concentrated near INOP valves? | **No.** Within 150 m: INOP flagged before Uri 19.4% vs GOOD 22.6%; same null for leak and service requests | No outside validation of the INOP flags. Post-Uri inspections *did* go to complaint areas (27% vs 20%), so inspections were reactive. |
| **Predict inoperable valves** (train on inspections ≤2020, test on 2021–23) | Naive model AUC 0.79, but `TURNSTOOPEN` **leaks the label** (it's recorded only when crews operate a valve). Leak-free (age, diameter, location, zone): **AUC 0.58**; top-20% precision 36% vs 26% base. | Weak discrimination. An "find the dead valves before the break" product would be honest but unimpressive. |

### 3.4 Counter-arguments and rebuttals

| Judge says | Evidence | Rebuttal |
|---|---|---|
| "Your data is three years old." | 🔬 True: 2023 snapshot. But the pipe network changes ~0.3%/yr, so ~1% has changed since. Valve flags drift toward *more* inoperable over time. **78% of in-line valves were last inspected ≥5 years ago**, past the 5-year exercise cycle in AWWA/Ohio EPA guidance. | **Rebuttable (revised).** (1) The network topology is still valid. (2) The 2023 flags are a *floor*: dead valves don't fix themselves, and working ones age. (3) The age of the records *is* the finding: by the industry's own 5-year standard, most of Houston's valve knowledge is overdue. Shutoff ranks which overdue valves to re-check first, by outage impact. |
| "Bentley WaterGEMS already does this." | ✅ It simulates segment shutdowns and needs complete valve and customer data | We run on the City's open GIS with its own inoperable flags, in a browser, with no license or hydraulic model. Bentley is a desktop product for modelers. |
| "Leaks are going down." | ✅ 311 leak complaints 44k → 35k | Repair is still 41 days on average and replacement is 0.3%/yr. Fewer complaints doesn't mean faster shutoffs. |
| "Houston already replaces valves." | ✅ Bundled with line contracts | Reactive, and bundled with line repairs. There's no public exercising program to say which valves matter most. |
| "No Houston outage has been tied to a bad valve." | ✅ None found | The Atlanta 2024 outage was exactly this mechanism. In Houston it's undocumented, which is part of the story, but it also means we can't prove local harm. |

### 3.5 Pitch line

> *"In June 2024, Atlanta lost water for two days because the valve under a broken main wouldn't turn. Houston's own records, last published in 2023, flag 21,574 valves as inoperable or lost. One in five of the valves the City inspected in 2022–23 didn't work. Shutoff shows what that does to your street when your main breaks, and which valves to fix first."*

---

## 4. What this means for the ranking

| | GreaseTrace | CrossingClear | Shutoff |
|---|---|---|---|
| Primary-source strength | **Strong**: the City's own FY25 annual report, data through Apr 2026 | Strong: City sensor data, HFD statements, FRA data through today | Moderate: 2023 snapshot; the network is still valid, the valve flags are a floor |
| News recency | E. coli report Aug 2026; spills Jan 2026 | Train Watch false positives Jul 2026; record report month May 2026 | West Houston leaks Oct 2026 |
| Best counter-argument | "The FOG program exists" (rebuttal is strong: grease SSOs rose anyway) | "TRAINFO and Satori exist" (rebuttal is moderate) | "Nothing validates the inoperable flags" (rebuttal is weak; the Uri test came back null) |
| Real weakest point | Least dramatic demo | Two commercial competitors in Houston | **No validation** and a weak predictive model (AUC 0.58), **not** data age |
| Verdict change | **Stronger** than before | Weaker (Satori) | Recovered to roughly tie with CrossingClear |

Revised 2026-10-10: data age was over-weighted earlier. GreaseTrace stays first; CrossingClear and Shutoff are close for second.
