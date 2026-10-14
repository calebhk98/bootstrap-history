# The number of firms does not grow with the market

**Status:** closed

A concern's hands are derived from its takings, so a firm in a bigger market is itself bigger, and the
firm count stays flat or falls as the market grows. `test_firm_count_whole_game.py` now pins the small
game's hands so "a bigger market holds more firms" compares equal-sized firms. Owner decision: should firm
size have a technical optimum (so a bigger market holds more firms) rather than scale with takings?
Measure: the same topic with the pin removed, over several market sizes.

**Resolution:** a firm's crew is the crew of one plant (`sim/engine/plant_crew.py`), taken in order from the hours
a concern's production lines ask of staff (`_labour_hours_per_year`, bounded by the entry's plant
`annual_output_at_basis`), from a stated `plant_crew_people` on the node, or, for a concern with neither, from the
founder's takings-based rule (`VENTURE_HANDS_PER_REVENUE`, a labelled temporary heuristic). `SimWorld.concern_staff`
reads it, so every firm of a kind is the same size and a bigger market is held by more firms. The hands pin is gone
from `test_firm_count_whole_game.py`, which now compares several market sizes. Expansion keeps its limits: capacity
is bought in plant-crews and the wage bill carries the span-of-control exponent, so growth stops where the added
margin no longer pays; demand beyond that is met by entry.
