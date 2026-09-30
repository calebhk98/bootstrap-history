# The integrated circuit is startable, and completes, with only photolithography and solid-state theory behind it

**Status:** closed

`com_integrated_circuit` has `pre: ['com_photolithography', 'quantum_solidstate_theory']` and a materials bill of quartz sand, two acids, brass and copper
(`data/tech_tree.json`, source `data/branches/24_comms_computing.json`). No semiconductor-grade silicon, crystal growth, doping, transistor or
clean-room node stands behind it, although its note describes a silicon chip with thousands of transistors. The tester started it at 313 AD for about 94 million
while the point-contact and junction transistors, and single-crystal growth, were still unbuilt, and it completed at 316 AD on the first attempt.

    python3 -c "import json;print([n for n in json.load(open('data/tech_tree.json'))['nodes'] if n['id']=='com_integrated_circuit'][0]['pre'])"

Not severe for the score (the goal is the transistor; the completion did not win the run), but it is the kind of under-prerequisited node
closed complaints 23 and 24 fixed for high-pressure steam and the Brayton turbine, and it breaks the premise that the chain to the goal is physical.

What it would take: add the transistor (or planar-process) and semiconductor-grade silicon prerequisites it implies; or rename and re-describe the node as
design knowledge and add a separate fabrication capability. A test that no node in the `com_` branch is startable before its named material chain would catch the class.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 162, 165). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Also reported (final playtests, B; `Complaints/reports/final-playtests-triage.md`): `en_two_stroke_cycle` needs only `cap_tol_1mm` (itself a free inherited capability) and is startable around 109 AD, earning 2,900 to 10,500 a year for a cost of 2,005; not used in B's run. Checked in data: `pre ['cap_tol_1mm']`, cost about 70 capital and 90 hours, risk 11%, revenue 800 book units. Same class as the integrated circuit.
