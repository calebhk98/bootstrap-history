# Large merchant ships are free to learn, free to open and free to run, and became the tester's largest income by a wide margin

**Status:** open

`sea_merchant_ships_large` has no prerequisite, zero cost, zero upkeep and a revenue of about 15 million a year (Han, 100 AD), against a starting
cash of about 750 thousand. `available` lists it at the start with cost 0 and earnings 16 to 27 million; `ventures` says TO OPEN 0. The only gate is supervision:
5.33 craft FTE (five smiths, about 1.8 million of advances), which a player can afford within a few years of the pharmacy/button income. The tester opened it in 138 AD
and cash went from 1.3 million to 9.7 million in one step; by 150 it was 27.5 million of 31.5 million revenue, by 200 a 71 million line, at zero upkeep for the whole run.

    printf 'start sea_merchant_ships_large\nventures\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

The node's note is about Rome's Alexandria grain fleet; no hull, cargo capital, crew wages beyond supervision, port, route or loss is modelled. Knowing a design can be free;
owning hulls and cargo cannot be (rule 4.1 of CLAUDE.md: costs fall out of physical inputs).

The tester judged the game "financially easy" from the moment it was found; other late-game money (seizures of 10 to 100 billion, fires) still mattered.
Related: 184 (money that stops mattering), 194 (what a rich founder can spend on), 113 (international economy).

What it would take: make a hull a purchased or built asset (timber, labour, yard time) with upkeep and loss risk; make revenue depend on cargo, route and ports; keep
the design knowledge free. The tester's sketch (a fleet with working capital, crews, maintenance, insurance, freight margin rather than gross sales) is in the tester notes, "Shipping proposal".

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 53, 62, 138). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
