# `bounty` has no quote: price multiplier, eligible categories and judging are unstated until it refuses or posts

**Status:** open

`help bounty` reads "bounty <id>: pay someone else to solve it" and nothing more. The tester's experience: a bounty on the research institute posted for 28.968 million, 2.5 times the ordinary quote of 11.587 million, finished two years later with no founder hours;
a bounty on `power_grid` was refused for a missing prerequisite; one on the motors node was refused with "category electrical ... local craftspeople cannot recognise success without theory" although a 3 MW station and electricians existed; a bounty on an active project said to stop the project first and lose sunk work.
`sim/engine/project_materials.py` has `bounty_price` (a multiplier on the whole bill) that no screen shows beforehand. Closed 157 fixed the save corruption; this is the missing preview.

    printf 'help bounty\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: `quote bounty <id>` with the multiplier, the eligibility result (prerequisites, category, active-project rule), when it pays out, and what a failure costs; explain the category rule in `why` for the node.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 114, 182). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
