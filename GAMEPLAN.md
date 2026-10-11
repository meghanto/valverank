# Gameplan: solo, top-down

Written Sat 22:30. Deadline Sun 13:00 (Devpost). Judging Sun 13:30, in person.
Assumption: no teammate delivers anything. Anything a teammate does deliver is a bonus and gets merged only if it lands in `web/` before 07:00.

Roles: **You (M)** decide, test, learn the model, pitch. **Claude (C)** writes code, runs the pipeline, drafts text.

---

## Level 0: what must be true at 13:30

A judge stands at the table for 3–5 minutes. Four things decide the score:

1. **Demo runs** on the hosted URL, on your laptop, with a video as fallback.
2. **The judge clicks** a pipe, sees the outage spread, then drags a slider and sees it shrink. That is the build principle: trigger the problem, apply the fix, see a measured result.
3. **You answer "how does it work" and "how do you know it's right"** without looking at notes. This is the "deep understanding" part of the Demo criterion.
4. **The Devpost page is complete:** URL, public repo, story, AI disclosure.

## Level 1: deliverables

| Deliverable | Status | Owner |
|---|---|---|
| Hosted URL | Deploy at 09:00 freeze (your call). Tonight: production build tested locally with `vite preview` | C builds, M approves |
| Public repo | Local commits tonight; public push at 09:00 | M approves |
| Product name | Undecided. 10-min brainstorm at 07:30; rename is a find-replace | M decides |
| Devpost writeup | Not started | C drafts, M edits |
| 2-min fallback video | Not started | M records |
| 90 s pitch + Q&A answers | Script exists (`proposals/03-shutoff.txt` §3) | M rehearses |

## Level 2: demo beats → features

| Beat | Feature needed | Status |
|---|---|---|
| 0–15 s: map of dead valves | Inoperable valves visible at **city zoom** | **Partial.** They only show at zoom ≥12, inside the demo area. Need a light citywide layer (~17.5k points). |
| 15–40 s: judge breaks a pipe | Click → paper outage → real outage | **Done** |
| 40–60 s: side panel | Customers, hydrants, valves to close, gallons | **Done** |
| — big-main credibility | Downstream supply loss (Tidwell: 2,000 reported, model says 5) | **Not done** |
| 60–80 s: repair slider | Valves ranked by outage reduction; slider; citywide number falls; chosen valves light up | **Not done. Biggest gap.** |
| 80–90 s: close | One line plus the one number | Script exists |
| Q&A | Validation table, limitations, how-it-works sheet | Table exists; sheet not written |

## Level 3: schedule

| Time | C (code) | M (you) | Done when / kill rule |
|---|---|---|---|
| **22:30–23:00** | Local commit; `HOW-IT-WORKS.md` | Read it | — |
| **23:00–01:30** | **Repair planner:** greedy ranking of inoperable valves by drop in expected customers per break; export the curve; slider + highlighted valves in UI | Read `HOW-IT-WORKS.md` (C writes it first, 15 min); click 10 pipes and log anything wrong | Slider moves the citywide number. **Fallback at 01:30:** static "top 50 valves" list, no slider |
| **01:30–02:30** | **Supply loss**, time-boxed: closing a segment also cuts off pipes that lose their path to large (≥24″) mains; re-run validation | Spot-check Tidwell and Beltway 8 on the map | **Kill at 02:30:** ship as a stated limitation |
| **02:30–03:00** | Citywide inoperable-valve layer; rebuild | Smoke test on local preview | — |
| **03:00–07:30** | Overnight queue (you hand it off before sleeping): test checklist, bug fixes, data-quality notes, Devpost draft. **No pushes while you sleep.** | **Sleep 4+ h.** Not optional: you pitch at 13:30. | — |
| **07:30–09:00** | Fix bugs you find | Name brainstorm (10 min); run the test checklist locally; review C's overnight diff | **Feature freeze 09:00** |
| **09:00–09:30** | Create public repo, push, Pages deploy | Approve push; open URL on laptop + phone | URL returns 200, map loads in < 5 s. If Pages fails: Netlify drop of `web/dist` |
| **09:30–10:30** | Devpost text, screenshots, README final | Edit the Devpost text so it sounds like you | — |
| **10:30–11:15** | — | Record the 2-min fallback video (screen + voice) | Video saved locally and uploaded |
| **11:15–12:30** | Q&A drill: C asks, you answer | Rehearse the 90 s pitch ×5; answer the Q&A list cold | You can explain an isolation segment in 1 sentence |
| **12:30** | — | **Submit Devpost** | — |
| **12:45** | — | Open every link in a private window | URL, repo, video all load |

## Cut order (if behind, cut from the top)

1. Care facilities / fire-station proximity
2. Supply loss → becomes a limitation slide
3. Payload optimization (22.8 MB; gzip on Pages helps)
4. Slides (the app is the deck)
5. Slider → static ranked list

**Never cut:** deployed URL, click-to-break, some form of the repair fix, validation table, video.

## Things we are not doing

- **Gemini / LLM features.** Every number comes from one deterministic path. An LLM summary adds risk and no score.
- **Backend / database.** Static files cover everything.
- **Sponsor swag prizes**, except a GoDaddy domain if it's free and takes under 10 min, after 09:00.
- **Separate frontend** by a teammate. One codebase.

## Q&A you must answer cold

| Question | Answer source |
|---|---|
| What's an isolation segment? | `HOW-IT-WORKS.md` |
| The data is from 2023. Is that a problem? | README Limitations; `proposals/news.md` §3.4 |
| How do you know it's right? | `validation/model_vs_news.md` (be honest about the Tidwell miss) |
| How is this different from Bentley WaterGEMS? | `proposals/03-shutoff.txt` §5 |
| Who pays for it? | §5: Houston Public Works, valve-exercising contractors |
| Why only part of the city on the map? | File size. Citywide stats are computed over all 290k pipes. |
| What would you do next? | Work-order history to validate; any city that publishes valve condition |
