# A sack reuses the goal closure of the first seat that asked

**Status:** closed - already fixed under Complaint 765 (the sack asks the seats module's `on_road_to_goal`, which keeps one closure per seat and drops it on `set_goal`; `sim/tests/test_sack_goal_road.py`); no `_goal_closure` cache is left in `sim/hazards/`

When a sack takes technologies, `Hazards.log_corpus_loss` (`sim/hazards/sack.py`) counts how many stood on the road to the goal. It
keeps what the goal needs in `self._goal_closure` the first time it asks and never again: the old `Sim` kept it in
`_goal_closure` the same way (`getattr(self, "_goal_closure", None)` in `society_hazards.py`). The closure is of the goal that seat
had at that moment, so a second seat with another goal, or a goal changed by hand, is told how many of its losses stood on the
road to the first goal. The module keeps this on purpose (the equivalence check compares the log's `on_road` fact); fixing it means
asking `tree_closure` for the acting seat's goal each time (the quote is cheap: one walk of the goal's prerequisites).

Reproduce: two seats with different goals, a sack in each (`sim.view("goal")` differs per seat; the second message's `on_road` is
counted against the first goal).
