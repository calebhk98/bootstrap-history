# Land that cannot be farmed leaves a society no other food source

**Status:** partly - geography now gives each tile hunting, herding, foraging and fishing food (`api.food_potential`); the engine does not read it yet (Complaint 414)

Found by pushing the farm model to its edges (`sim/tests/test_farm_edges.py`).
When ground yields nothing, or a farmer nets less than one person-year of
food, population falls toward zero and every hand ends up farming. That is
right for a grain-only economy, but no real people on desert, steppe or coast
starve on land that cannot grow grain: they hunt, herd and fish.

Until those food sources exist the model cannot represent a society living
off such land; the test file pins only the grain-only behaviour (decline,
no negative numbers, no crash).

Fixed part: the labour allocator used to read the gross marginal product of
an hour of farm work, so it kept sowing land whose harvest per hectare is
below the seed it takes. `farm_workers_needed` now reads the marginal product
net of seed (`net_marginal_product_kg_per_hour` in
`sim/labour/labour_allocation.py`) in the shortfall response, the surplus
response, the food-balance step and the clearing decision. At or below zero,
no extra hands are drawn for food and no ground is cleared. Pinned in
`sim/tests/test_farm_edges.py` (`NetMarginalProductTests`).
