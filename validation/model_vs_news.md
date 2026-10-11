# Model vs. news-reported main breaks

Customers = City utility accounts within 120 m of the segment's mains, plus accounts in segments cut off from every plant/pump station/tank by closing it (pipeline/supply.py). Candidates = mains within 150 m of the geocoded point (filtered to the reported diameter when one matches).

| ID | Date | Location | Reported | Diam | Candidates | Closest pipe: paper → real customers | Range paper | Range real |
|---|---|---|---|---|---|---|---|---|
| NB01 | 2015-08-13 | 1100 block of Pembridge Dr at Albin St,  | — | 8 | 17 (diam match) | 35 → 35 (8″, 5 m) | 8–63 | 22–93 |
| NB02 | 2016-08-30 | Beltway 8 (W Sam Houston Pkwy S) and Bel | 80 | 12 | 7 (diam match) | 22 → 38 (12″, 12 m) | 4–22 | 38–38 |
| NB03 | 2018-06-26 | Memorial Dr near Aura Memorial Apartment | 1 | — | 27 | 7 → 7 (24″, 40 m) | 1–57 | 1–310 |
| NB04 | 2020-02-27 | Clinton Dr and 610 East Loop, east Houst | — | 96 | 3 (diam match) | 11 → 11 (96″, 33 m) | 11–11 | 11–11 |
| NB06 | 2022-12-08 | 3700 block of Timmons Ln, Greenway/Upper | — | 16 | 17 (diam match) | 1 → 1 (16″, 15 m) | 1–8 | 1–8 |
| NB07 | 2023-02-06 | W Tidwell Rd and Antoine Dr (5700 block  | 2000 | 16 | 6 (diam match) | 5 → 5 (16″, 9 m) | 0–5 | 0–5 |
| NB08 | 2023-09-08 | 6622 Keller St near Keller and Flowers,  | 9 | — | 37 | 62 → 62 (24″, 5 m) | 0–62 | 2–62 |
| NB09 | 2024-09-25 | Hwy 3 (Old Galveston Rd) and El Dorado B | — | 42 | 4 (diam match) | 16 → 16 (42″, 24 m) | 0–16 | 0–16 |
| NB10 | 2025-01-26 | Sabine St near townhomes, First Ward (cr | — | 8 | 10 (diam match) | 9 → 9 (8″, 14 m) | 7–21 | 7–21 |
| NB11 | 2025-08-24 | 12434 Wellington Park Dr, ZIP 77072 (Ali | — | — | 2 | 178 → 208 (8″, 10 m) | 178–178 | 208–208 |
| NB12 | 2026-07-24 | Richmond Ave near Southwest Fwy, west of | — | — | 18 | 3 → 3 (12″, 4 m) | 0–26 | 0–26 |
| NB13 | 2014-10-14 | Leaky valve on a transmission line, 2300 | — | — | 65 | 50 → 197 (8″, 4 m) | 0–61 | 0–197 |
| NB14 | 2015-09-17 | S Braeswood Blvd at Stella Link Rd, Meye | — | — | 25 | 6 → 8 (12″, 20 m) | 1–12 | 6–18 |
| NB15 | 2016-02-19 | Allen Pkwy near Taft St, Fourth Ward/Mon | — | 8 or 12 | 17 (diam match) | 1 → 1 (12″, 6 m) | 0–12 | 0–12 |
| NB16 | 2024-02-08 | PLANNED overnight outage, Memorial Heigh | — | — | 26 | 50 → 174 (8″, 22 m) | 2–97 | 2–174 |
