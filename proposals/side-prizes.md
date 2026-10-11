# Side prizes: options for GreaseTrace, CrossingClear and Shutoff

Covers every non-cash prize on the CodeRED Orion Devpost and the MLH prize page (copied 2026-10-10) and how each of the three proposals could compete for it.

**Open question, ask in the event Discord before investing:** can one project win a cash prize *and* MLH/house side prizes? Neither page says. If they don't stack, do only the free items (GoDaddy, DEV).

---

## 1. Prize list

| Prize | Award | What judges want (from the prize text) |
|---|---|---|
| Best Hardware Track | 43" 4K TVs | Hardware shown in a live demo |
| Most Immersive Project | 27" 1440p monitors | No criteria text given; assume visual and interactive depth |
| [MLH] Best Use of Tiger Data | Stream Deck Mini | "Most innovative, impactful, and performance-driven use" of Tiger Data (Postgres plus time-series hypertables and continuous aggregates) |
| [MLH] Best Use of Gemini API | MLH swag kits | AI-powered app built on Gemini |
| [MLH] Best Use of Vultr | M5Stack Tab5 | Deploy on Vultr cloud compute or GPUs |
| [MLH] Best Domain Name from GoDaddy Registry | Digital gift card | Register a domain through GoDaddy Registry (MLH claim code) |
| [MLH] DEV Writing Challenge | $100 | Publish the project story on DEV; judged on technical substance, originality, storytelling, popularity. Selected monthly. |
| [MLH] Best Use of ElevenLabs | Wireless earbuds | Autonomous audio, giving the project a voice |
| [MLH] Best Use of Solana | Ledger wallets | High-frequency transactions, DeFi, supply chain or identity |
| [MLH] Best Use of Backboard | Tile Essentials Pack | Persistent AI memory and state across sessions |

---

## 2. Fit by idea

Legend: **Strong** = the integration improves the core product · **Moderate** = defensible but optional · **Weak** = it would read as bolted on · **None** = skip

| Prize | GreaseTrace | CrossingClear | Shutoff |
|---|---|---|---|
| GoDaddy domain | Strong (free) | Strong (free) | Strong (free) |
| DEV Writing | Strong (free, after the event) | Strong | Strong |
| Tiger Data | **Strong** | **Strong** | Weak |
| Vultr | Moderate (only with a backend) | Moderate | Weak |
| Gemini | Moderate | Moderate | Weak |
| Most Immersive | **Strong** | Weak | Moderate |
| ElevenLabs | Weak | Weak | Weak |
| Solana | None | None | None |
| Backboard | None | None | None |
| Best Hardware | None | None | None |

---

## 3. Per-idea plans

### 3.1 GreaseTrace (sewer overflows)

| Prize | Integration | Why it's real, not bolted on | Effort |
|---|---|---|---|
| **Tiger Data** | Load ~570k timestamped events into hypertables: SSOs (66k), stoppages (235k), odor 311 (33k), sewer 311 requests (244k). Continuous aggregates compute rolling 30/90/365-day upstream counts per pipe segment, which are the risk model's input features. Add a live query panel: "events upstream of this manhole, last 90 days". | The risk model needs windowed time-series aggregation over hundreds of thousands of events. That is the stated use case for continuous aggregates. Show query latency on screen to address "performance-driven". | 2–3 h |
| **Vultr** | Host the API (FastAPI) that serves Tiger Data queries and upstream traces | Needed anyway if we go beyond a static site | ~1 h |
| **Gemini** | Pull structured labels from free text: crew `ACTION` notes (*"Spread 8 ounces of chlorine… Repaired line"*) and 311 `DETAILS` → {grease mentioned, wipes, root intrusion, private lateral, repair type}. Run as a batch offline and store the labels. | Turns unstructured City records into model features. Gemini produces labels, never displayed metrics. | ~2 h |
| **Most Immersive** | 3D view (deck.gl): pipes drawn at real depth using invert elevations under a translucent city surface; flow animates upstream from the clicked overflow. | It is also the strongest version of the main demo. | 3–4 h |
| ElevenLabs | (Skip.) A spoken overflow briefing would be decoration. | — | — |

### 3.2 CrossingClear (train-blocked crossings)

| Prize | Integration | Why it's real | Effort |
|---|---|---|---|
| **Tiger Data** | Hypertable of the Train Watch feed we have recorded every minute since Sat 2:50 PM (56 crossings), plus 24k FRA reports. Continuous aggregates give blockage probability by crossing × hour-of-week. Live ingest keeps running during judging. | Real-time sensor stream plus historical events is exactly Tiger Data's pitch ("real-time IoT monitoring") | 2–3 h |
| **Vultr** | Host the ingest worker and API | The live poller needs an always-on server; a static host can't do it | ~1 h |
| **Gemini** | Classify the FRA `otherImpact` free text ("ambulance couldn't pass", "school bus", "stuck 2 hours") into severity and affected-service categories | Adds a severity weight that the structured fields lack | ~2 h |
| Most Immersive | Weak. A 2D route animation is the natural view; 3D adds nothing. | — | — |
| ElevenLabs | Weak. Voice dispatch alerts ("Leeland St blocked, reroute via…") are plausible but gimmicky in a judged demo. | — | 1–2 h |

### 3.3 Shutoff (water valves)

| Prize | Integration | Why it's weak or strong | Effort |
|---|---|---|---|
| Tiger Data | Only the Winter Storm Uri 311 time series (11k requests in 11 days). Thin. | No meaningful time-series workload | — |
| Vultr | Only if a backend is added; the core can be fully static | Not needed | — |
| Gemini | Plain-language break summary from computed values | Narration only; low value | ~1 h |
| **Most Immersive** | 3D network with the outage spreading segment by segment from the clicked break | Strengthens the main demo | 3–4 h |

---

## 4. Rules for all side-prize work

1. **Core first.** No side-prize work starts until the core demo works end to end on the deployed site.
2. **Hard cutoff Sat 11:00 PM** for starting any side-prize integration; anything unfinished at the Sun 9:00 AM freeze gets cut.
3. **Static fallback.** If we add a backend (Tiger Data/Vultr), the frontend must still work from precomputed static files when the API is down.
4. **No LLM-generated numbers.** Gemini output is text-to-labels or narration of values we computed. Every displayed metric comes from deterministic code.
5. **Disclose every AI tool** in the README (rule requirement), including Gemini and any coding assistants.
6. **One owner per side prize**, so the core team isn't interrupted.

---

## 5. Recommended bundle per idea

| Idea | Do regardless | Do if the core is done by Sat 11 PM | Skip |
|---|---|---|---|
| GreaseTrace | GoDaddy, DEV | Most Immersive (3D) → Tiger Data + Vultr → Gemini labels | ElevenLabs, Solana, Backboard, Hardware |
| CrossingClear | GoDaddy, DEV | Tiger Data + Vultr (live ingest) → Gemini severity | Immersive, ElevenLabs, Solana, Backboard, Hardware |
| Shutoff | GoDaddy, DEV | Most Immersive (3D) | Tiger Data, Vultr, Gemini, ElevenLabs, Solana, Backboard, Hardware |

**Count of side prizes each idea can credibly compete for** (not counting the free GoDaddy/DEV): GreaseTrace 4, CrossingClear 3, Shutoff 1.

---

## 6. Logistics checklist

- [ ] Ask in Discord: do MLH/house side prizes stack with Best Overall, Pitch and Environment?
- [ ] Claim the GoDaddy Registry domain code (MLH page → "Claim Code")
- [ ] Claim Vultr credits (MLH page → "Claim Code") if a backend is planned
- [ ] Create a Tiger Data (Timescale Cloud) free instance; check the free-tier storage limit against ~570k rows
- [ ] Get a Gemini API key (Google AI Studio). The MLH workshop "Intro to Google AI Studio" is Sat 5:00–5:50 PM, Heights room.
- [ ] Tick each targeted side prize on the Devpost submission form
- [ ] After submission: publish the DEV post and link it on Devpost
