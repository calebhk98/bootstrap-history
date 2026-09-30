# Artillery needs no gunpowder and the bastion-and-wall-gun defence needs almost no materials, yet a repelled attack is credited to guns on walls

**Status:** open

`mil_artillery_piece` has `pre: ['cap_heat_1300', 'mat_bronze']` and a bronze bill; gunpowder (`gunpowder`, behind nitre beds, sulphur and charcoal) is not a prerequisite. `mil_trace_italienne` has `pre: ['mil_artillery_piece']`, no material bill, 120 engineer hours and a very small cost (55,862 cash for the tester);
`mil_bastion` needs 5 tonnes of stone. The sack-chance counters count these as walls and guns that blunt an attack, and several attacks were reported defeated citing "angled bastions, wall guns" and state-army diffusion of the same technology.
The tester notes a cannon can be cast without powder, but a usable defence needs propellant, crew, ammunition and deployment, and a trace italienne is a construction, not a design. Labelled a scope question: design knowledge versus built fortification.

    python3 -c "import json;d={n['id']:n for n in json.load(open('data/tech_tree.json'))['nodes']};print(d['mil_artillery_piece']['pre'],d['mil_trace_italienne']['pre'],d['mil_trace_italienne'].get('mat'))"

What it would take: make the defence benefit depend on the powder supply and on a built fortification (a concern with a material and labour bill), and add gunpowder as a prerequisite (or a `req_any` group) of the piece that uses it. Same class as 226 and closed 23 and 24.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 91). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Also reported (final playtests, C; `Complaints/reports/final-playtests-triage.md`): in the Mexica runs the sack chance reached 66% a year at best however much was built; walls, powder and rifles 'barely mattered'. Consistent with the defence being credited without the materials (this complaint) and with a fixed dice stream (254).
