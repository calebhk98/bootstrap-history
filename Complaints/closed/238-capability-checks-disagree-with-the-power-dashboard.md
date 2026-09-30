# The capacity dashboard shows generation that the capability checks ignore, and a "grid" capability is satisfied with zero grid generation

**Status:** closed

Tester evidence: at 244 AD the dashboard showed 300 kW of local generation from an alternator while the local-electric-power capability was unmet until a dynamo was built (the next start needed it, and completing it raised generation only 10 kW).
At 300 AD the requirement list ticked "grid electric power, MW scale (central generation)" with 0 kW of grid generation and only 3,000 kW of transmission capacity; the hydro station (3 MW) came later and was opened by hand.
In the data, `cap_power_grid` has `pre: ['cap_power_electric', 'power_grid']`: a knowledge flag, with no generation test, while its label says central generation.

What it would take: decide whether capability flags are knowledge or installed capacity and label them so; where a recipe needs power, test the installed kW on the dashboard (a recipe that needs 10 kW should not wait for a named node when 300 kW is running),
or say why the named node is needed (AC versus DC, stability). Related: 125, 228.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 117, 141, 156). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
