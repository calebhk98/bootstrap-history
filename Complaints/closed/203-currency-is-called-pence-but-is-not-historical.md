# The currency is called pence, but wages and prices are not English pence

**Status:** closed

The tester noted that the money scale does not match the record: about 44 thousand pence (roughly 184 pounds at 240 pence to the pound) in 1320, while one carpenter costs about 9,400 pence a year (roughly 39 pounds), against surviving accounts showing paid workers at a few pence a day. The kit text says "4.0 labourer-years of wages, which here is 17030 pence", so a labourer costs roughly four thousand pence a year in the model. They accept that the unit behaves as a normalised gameplay currency and ask only that the game say so, to avoid false precision.

Reproduces on the current branch: the start text and `help money` call the unit "pence" and never say it is normalised or how it relates to the historical penny.

    printf 'help money\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: one sentence in the start text and `help money` stating what the unit is anchored to (the wage of a labourer, not the silver penny). Whether the anchor itself is right is complaint 140 (money constants are still book denarii).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
