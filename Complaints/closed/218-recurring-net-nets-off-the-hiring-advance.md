# `recurring` net includes the one-time hiring-advance credit, so it is not a next-year figure

**Status:** closed - pinned by sim/tests/test_spending_previews.py

After `hire carpenter 1` the ledger prints wages 355,925 "of which already paid as hiring advances 355,922" and
"Net/yr before the work in hand: 5,220 (recurring)". Revenue 438,185 minus living 432,962 is 5,223, so the wage is
netted out entirely. Next year, with the same employee, the wage is due again and the real recurring figure is about minus 350 thousand.
`state` and `money` both print the 5,220 as "recurring - this is the one to watch".

    printf 'start hom_toys_dolls\nstep\nhire carpenter 1\nmoney\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

The tester planned a year on the +226,658 they saw and was short; later a departing employee's whole wage disappeared
from the settlement (617,171 + 89,852 - 1,042,556 predicted minus 335,533, actual plus 323,182, a difference of exactly the annual wage),
which is consistent but was not explained anywhere.

What it would take: show the recurring net before any advance credit, and the advance as a separate one-off line for this year (complaint 93
already asks the funding UI to separate four concepts); state on hire and on a departure what happens to the paid-in-advance wage.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 17, 18, 43). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
