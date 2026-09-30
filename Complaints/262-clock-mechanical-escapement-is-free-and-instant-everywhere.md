# `clock_mechanical_escapement` costs nothing and takes no time, and is startable in Rome 100 AD and in every civilisation that does not already hold it

**Status:** open

Two testers: "Weight-driven mechanical clock with verge escapement" shows cost 0, 0 hours, 0 years, 0% risk; one started and completed it without advancing time; the other saw that its own note calls it an "inherited medieval mechanism" from about 1300.

Data: `data/tech_tree.json`, `clock_mechanical_escapement`: `cap 0, ph 0, lab {}, mat {}, risk 0, yrs 0`, `pre ['cap_tol_1mm']`, and `cap_tol_1mm` is itself a free capability ("already reached by any tradition with serious carpentry"). Only `england_1300` lists it in `starting_techs`; in `rome_100ad`, `mexica_1500` (and Han and Norse) it appears in `available all` at cost 0 with 62 in its `RESTS` column. Reproduced for Mexica: `available all`; Rome: `available all`.

Why it matters: a 1300 AD mechanism, with the tree's own note saying it has unmet requirements, is a free grant to every earlier civilisation and unlocks the clockwork chain (the tester counts it among suspicious "free/instant" nodes). Whether free nodes are intended grants ("represented explicitly") or data errors is undecided: 144 nodes have no cost (see 260, 226, 227).

What it would take: give the node a real bill (gears, iron, a machinist) or mark it inherited and list it in `starting_techs` for England only; add a validator rule that a zero-cost node must be in some civilisation's start, and that a civilisation without it cannot start it free. Related: 260, 226, 227.


Found in the final blind playtests of this branch (Rome 100 AD and Mexica 1500 fog runs; A bug 2 and B tree section). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`, `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
