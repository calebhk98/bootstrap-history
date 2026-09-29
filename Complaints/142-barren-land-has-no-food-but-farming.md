# Land that cannot be farmed leaves a society no other food source

**Status:** open - waiting on hunting, herding and fishing existing as food sources

Found by pushing the farm model to its edges (`sim/tests/test_farm_edges.py`).
When ground yields nothing, or a farmer nets less than one person-year of
food, population falls toward zero and every hand ends up farming. That is
right for a grain-only economy, but no real people on desert, steppe or coast
starve on land that cannot grow grain: they hunt, herd and fish.

Until those food sources exist the model cannot represent a society living
off such land; the test file pins only the grain-only behaviour (decline,
no negative numbers, no crash).

Related, not caused by the missing sources: the labour allocator reads the
gross marginal product of an hour of farm work, so it keeps sowing land whose
harvest per hectare is below the seed it takes. The granary can no longer go
negative from this, but the workforce is still pulled onto ground that
destroys food. Fix belongs where the marginal product is computed
(`sim/engine/labour_allocation.py`, `farm_workers_needed`): net it of seed.
