# Every seat shared the goal closure of whichever seat asked first

**Status:** fixed (the seats module keeps one goal closure per seat: `sim/seats/goals.py`, `RememberGoalClosure`)

`Sim.on_road_to_goal` (`sim/engine/fog.py` at the base) worked out what the goal needs once, from the acting seat's goal at the
time of the first call, and kept it on the game as `_goal_closure`. Every later call answered from that set, whichever seat was
acting. In a game with two seats, a second player with no goal of its own was treated as needing everything the founder's goal
needs: `never_abandon` protected those nodes, so a loss-making concern on the founder's road was never seized from the second
seat by its creditors, however deep its debt. Which seat's goal won depended on which seat asked first, so the answer depended on
the order of play.

Found by the stress equivalence tier: in `rome_100ad/seed1/12y/events+stress+2seats`, from year 1 the second seat (no goal, in
debt past its credit line) now has its `identity_cover` concern seized; at the base it was spared by the founder's goal.

Regression test: `sim/tests/test_seats_facts.py` (each seat keeps its own closure). The stress baseline's two-seat scenario is
re-recorded from the fixed build (`docs/architecture/baseline/README.md`).
