# The shortage remedy text sizes a new mine against the market shortfall and ignores mines already being sunk

**Status:** closed

Tester (213 to 217 AD): bulk steel warned "coal 20,754 t short" and kept recommending another 20,754 t mine after coal 21,000 t/yr and iron 14,000 t/yr mines had already been commissioned and were three years from producing.
Code reading: `sim/engine/economy_freight.py`, `material_shortfall_t` is demand minus own supply minus market, where own supply comes from `_own_material_supply`, which counts producing capacity, and `shortage_remedy_plan` sizes
`quote mine`/`buy mine` from that shortfall. Closed complaint 65 fixed the same blindness in `auto_mine`; this is the manual text path. Not replayed live (needs a late game).

What it would take: subtract tonnage in the pipeline (and say "mine of N t/yr commissioned, ready in YYYY"), and print the year the shortage ends. Closed 11 and 193 fixed the size of the nitre and mine suggestions.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 101, 102). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
