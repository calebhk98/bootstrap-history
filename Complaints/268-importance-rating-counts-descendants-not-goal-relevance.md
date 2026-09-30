# `RESTS` and "how much rests on this" count descendants, so narrow but critical prerequisites (manganese, nitre beds, Boolean algebra) read as minor

**Status:** open

Both Rome testers: critical supply nodes that gated the endgame were not flagged as ALL or much in `available`; "a few things" undervalues a prerequisite with few descendants that the chosen goal cannot do without.

Cause: `how_much_rests_on_this` (`sim/engine/proto/techtree.py`) maps the count of downstream nodes to "almost everything / a great deal / a fair amount / a few things", with `_RESTS_SHORT` in `render_screens_big.py` giving the ALL/much/some/few column. It is a whole-tree count, not a statement about the goal. Under fog a goal-aware marker must not reveal the road, which is the tension with complaints 71 and 100.

What it would take: a second, fog-safe marker "on the road to your goal" for visible startable nodes (yes/no, without distance), and a separate mark for supplies and capabilities. Related: 100, 71, 267.


Found in the final blind playtests of this branch (Rome 100 AD and Mexica 1500 fog runs; B annoyances; A section 6). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`, `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
