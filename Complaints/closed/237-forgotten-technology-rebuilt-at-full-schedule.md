# A forgotten technology is rebuilt at its full original cost and payment schedule, ignoring surviving equipment and dispersed copies

**Status:** closed

Request, from the tester's 317 AD sacking: 37 technologies were forgotten, 14 on the route, although the corpus had been dispersed. Restarting the power grid quoted the original 25 nominal years (12.4 displayed), the rebuild of
dynamo, motors and grid took until 368 AD, and two transistor branches were blocked on it. The surviving 3 MW hydro station, local generation and documented knowledge did not shorten anything, and a retained capability flag did not let `arc_furnace_ferroalloys` start without the lost node.

The harshness of undefended knowledge loss is an intended design (closed 170: "that is what the hedges are for"), and the tester agrees the losses make wealth non-trivial. The ask is narrower: a rebuild should be cheaper than a first introduction
when a dispersed copy, surviving equipment or living practitioners exist, and the UI should say which part was lost (premises, crew, specimens, practice) rather than one undifferentiated "forgotten".

Not reproduced (needs a played-forward game). What it would take: a retained fraction of the original work and payment schedule for a forgotten node, scaled by the corpus hedge and surviving capability; a `why` line for a lost node that says what a rebuild costs and why.
Related: 169 (wealth exposure), 184, 55 (closed).

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 168, 169, 179, 183, 186, 187). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Fixed: a rebuild of a forgotten node now redoes only what has not survived (`rebuild_retained_share`, `sim/engine/projects_rebuild.py`). The share is derived from state: a held corpus copy (from the same hedge table a sack reads), the share of the node's trades still worked by people on the books, and the share of what was built on it that still stands, combined and capped by one labelled heuristic ceiling. It scales the money bill, the founder hours, the hired hours, the calendar floor and the payment schedule, and is frozen when the project starts. `why` carries a REBUILD line saying what survives and what it saves; with nothing surviving a rebuild costs what a first build does.
