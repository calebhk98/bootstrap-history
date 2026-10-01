# The dynamo's commutator needs high-pressure steam, and industrial zinc needs the power grid, although water power and coal-fired retorts are the described processes

**Status:** closed

Data (`data/tech_tree.json`):

- `en_commutator` has `pre: ['cap_tol_100um', 'cap_power_steam']`, and `cap_power_steam` has `pre: ['cap_power_water', 'steam_high_pressure']`. The dynamo needs the commutator
  and also lists `water_power_scale`. A water-powered civilisation with no high-pressure steam cannot build a dynamo.
- `zinc_industry_scale` has `pre: ['high_temp_furnace', 'power_grid', 'zinc_metal']`, while its own note describes coal-fired Belgian horizontal retorts with coke substituting for charcoal.
  The tester reached the grid only to unlock a coal-fired process and then found the grid's own chain (25 nominal years, steam, bulk steel, transformers, substations, switchgear) was the critical path.
- Complaint 121 records the same shape for electropolishing; this is the same class on two more nodes on the transistor route (germanium comes from zinc).

    python3 -c "import json;d={n['id']:n for n in json.load(open('data/tech_tree.json'))['nodes']};print(d['zinc_industry_scale']['pre'], d['en_commutator']['pre'])"

What it would take: for each node, name the physical need (a prime mover, a current source, a heat source) as a `req_any` group with its real alternatives (water turbine
or steam for the commutator's drive; coal or electric heat for zinc), keep the grid as one option where it is physically the answer, run `validate`, add a test that the node is startable without the grid.
Tester items 115, 130, 145, 146 and 160 are the neighbouring question: a finished synthetic-ammonia process that does not satisfy the separate ammonia material, a broad alternator and dynamo that do not satisfy the rotating-field alternator and shunt dynamo, a telescope that does not satisfy the semaphore (whose real prerequisite is `patron_senatorial`). Explain in `why` when a broader capability does not satisfy a narrower one.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 103, 104, 115, 130, 145, 146, 160, 183). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
