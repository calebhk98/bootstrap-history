# There is no `map`, `country` or geography overview, and `move` lists tiles only by id

**Status:** open

`map` and `country` answer "no command called ...". `help map` finds nothing. Bare `move` lists tiles such as `china_10`, `china_11`, `taiwan_01` with population, travel days, hours lost and wages, but no names, regions, adjacency or
what is at each place, so a player cannot choose where to base. `population` describes the country and one town but does not name the town. The tester asks for a `map`/`geography` alias, readable place names and a coordinate or region view
showing the current base, resources, markets and reach. Replay:

    printf 'map\ncountry\nmove\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: aliases for `map`, `geography`, `country` (to `population` or a new overview); place names in `move`; a one-screen summary of the current base's region. Related: 140 (regions and tiles are two maps), 111.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 123, 125). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
