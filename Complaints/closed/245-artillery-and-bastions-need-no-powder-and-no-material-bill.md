# Artillery needs no gunpowder and the bastion-and-wall-gun defence needs almost no materials, yet a repelled attack is credited to guns on walls

**Status:** closed - guns, firearms and fortifications count only for the powder held in the stock ledger (banked by the running powder works, drawn by live threats) and the garrison present (soldiers hired from the labour market, held by the open work, upkeep paid)

`mil_artillery_piece` has `pre: ['cap_heat_1300', 'mat_bronze']` and a bronze bill; gunpowder (`gunpowder`, behind nitre beds, sulphur and charcoal) is not a prerequisite. `mil_trace_italienne` has `pre: ['mil_artillery_piece']`, no material bill, 120 engineer hours and a very small cost (55,862 cash for the tester);
`mil_bastion` needs 5 tonnes of stone. The sack-chance counters count these as walls and guns that blunt an attack, and several attacks were reported defeated citing "angled bastions, wall guns" and state-army diffusion of the same technology.
The tester notes a cannon can be cast without powder, but a usable defence needs propellant, crew, ammunition and deployment, and a trace italienne is a construction, not a design. Labelled a scope question: design knowledge versus built fortification.

    python3 -c "import json;d={n['id']:n for n in json.load(open('data/tech_tree.json'))['nodes']};print(d['mil_artillery_piece']['pre'],d['mil_trace_italienne']['pre'],d['mil_trace_italienne'].get('mat'))"

What it would take: make the defence benefit depend on the powder supply and on a built fortification (a concern with a material and labour bill), and add gunpowder as a prerequisite (or a `req_any` group) of the piece that uses it. Same class as 226 and closed 23 and 24.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 91). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Also reported (final playtests, C; `Complaints/reports/final-playtests-triage.md`): in the Mexica runs the sack chance reached 66% a year at best however much was built; walls, powder and rifles 'barely mattered'. Consistent with the defence being credited without the materials (this complaint) and with a fixed dice stream (250).


**Closed by (final step):**

- Powder is a held material. A node's `banks_output` makes a running work put a material into the existing stock ledger each year from its crew's hours (the powder works banks `gunpowder_kg`); a `hazard_counters` entry's `magazine` is the stock held for the counter to count in full (it counts for the share held) and `draws` is spent from the ledger in each year a threat of its kind is live. A dry magazine shows as `lapsed: its magazine of gunpowder_kg is empty` in `why` and the mitigation table (`sim/engine/defence_stores.py`, `hazard_relief.py`). The guns, the matchlock, the flintlock and the corned powder counters carry magazines.
- Fortifications are garrisoned. A node's `garrison` ({trade: people}) is drawn from the labour market: an open concern holds it like a foreman (`open` refuses without it free, the yearly staffing rule shuts the work when the soldiers are gone, `auto_replace_foreman` rehires), and the counters on the node count for the share present. The trace italienne, bastion and concrete fortification carry a garrison and a yearly repair bill, so they are concerns that must be opened and kept; a shut one lapses through the running gate (`running`), as built in Complaint 133.
- The update note's "hull, route and port model" does not belong to this complaint: no defence counter here has a hull, route or port term. It is the merchant-ship model, tracked in `Complaints/190-late-game-uses-for-money.md` in the words "needs a hull, route and port asset model".
- Sizes (crew, magazine, yearly draw, mill rate per labour hour) are labelled heuristics in each node's `_internal`. Tests: `python3 -m unittest sim.tests.test_defence_stores` (quick); the whole-game checks are in `sim/tests/test_guns_on_walls_need_powder.py` (slow, to run after merge).
