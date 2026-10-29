# The goal road memo is one per game, not one per seat

**Status:** closed - the seats module keeps the goal road and the critical floor per seat (Complaint 921; tests `sim/tests/test_goals_several.py`, the road is the acting seat's own). The last copy, the hazards module's own memo of the goal road in a sack's report, now asks the seats module's `on_road_to_goal` (`sim/tests/test_sack_goal_road.py`).

What the acting seat's goal needs (`Sim._goal_closure`, read by `on_road_to_goal`, the labour package's training advice
`sim/labour/labour_training.py` and the score screen `sim/ui/proto/score.py`) is one set held on the game. It is dropped
only when the goal is set (`Sim.goal` setter -> `forget_goal_caches`, `SetGoal` -> `ForgetGoalCaches`). A seat switch
(`Sim._switch_seat`, which `act_as` calls) drops the economic caches (`_reset_economic_caches`) but not this memo, and each
seat has its own goal (`SimulationState._goal` reads `seats[acting_seat].goal`). In a game with two seats whose goals differ,
the first seat to ask leaves its road in the memo and the next seat to ask, inside `act_as`, is answered with the first
seat's road: `on_road_to_goal` (and so `never_abandon`, which decides what a sack or a closure may take), the training advice
and the score read the wrong goal. Not run: found by reading the switch path against the memo's writers.

What it would take: key the memo by seat (the seats module can hold it in `SeatsSeat` once the labour package and the score
screen read it through a view and the screen's writer sends `RememberGoalClosure`), or drop it in `_switch_seat`. A regression
test is two seats with different goals asking `on_road_to_goal` for one node.
