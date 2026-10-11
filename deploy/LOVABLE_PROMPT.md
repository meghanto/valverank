# Lovable prompt: landing page

Paste the block below into Lovable. Replace `ValveRank` (product name, still undecided) and `{APP_URL}` (the map app). Only the numbers below are verified; don't let Lovable invent others.

---

Build a one-page landing site for **ValveRank**, a tool that shows what really happens when a Houston water main breaks. Dark theme: background #111318, text #f5f3ee. Accent colors: blue #4fb3ff ("if every valve worked"), red #ff4f32 ("with the City's valve records"), amber #ffb000 (low pressure). Font: Inter. No stock photos, no emoji, no testimonials, no pricing table.

Sections:
1. **Hero.** Headline: "When a water main breaks, the valves decide who loses water." Subhead: "Houston's own records mark 17,413 valves on water mains as inoperable. ValveRank simulates every break on the City's full network, pressure included." Primary button: "Break a pipe" → {APP_URL}.
2. **The problem**, three cards:
   - "17,413 inoperable valves": stuck, buried, or 'cannot locate', in City GIS records.
   - "2.4× bigger outages": average customers out per break, 16.3 if every valve worked vs 38.6 with the City's records.
   - "78% overdue": share of main valves last inspected 5+ years ago; industry practice is every 5 years.
3. **How it works**, four steps with simple line icons:
   - (1) 290,959 City water mains, 92,763 shut-off valves, 544,011 customer accounts.
   - (2) Isolation segments: the smallest area crews can shut off.
   - (3) EPANET pressure physics on the whole network; it reproduces the 2020 Clinton Drive citywide pressure loss.
   - (4) A repair planner that picks the valves whose repair saves the most customer-hours.
4. **Proved, not just tested.** "Core guarantees are machine-checked in Bend 2: a dead valve can never make an outage smaller." Small monospace badge: `ALL PROOFS CHECK`.
5. **Honest limits**, a short list:
   - City data snapshot June 2023.
   - Pressure model uncalibrated.
   - Accounts are not people.
   - Validated against public reports where they exist.
6. **Footer.** "Built at CodeRED: Orion 2026, University of Houston." Links: GitHub repo, the app.

Responsive down to 360 px wide. Accessible contrast. No cookie banner.
