# Producers do not choose what to offer, and do not idle or exit when the price is below their cost

**Status:** closed - the agent economy is the default: producers offer held stock at their own reservation, set output from expected price against their own cost, idle and mothball rather than sell below cost, and new makers enter where demand goes unmet (sim/economy/producers*.py, entry.py; tests test_economy_producers.py, test_economy_entry.py)

Since Complaint 375 a producer's offer has a reservation price, its own unit cost, and a producer whose cost is above the clearing price sells nothing that year. What the producer does about it is not modelled: a firm's concern keeps its declared output and its staff, its sale is simply not taken, and the unsold tonnes carry as stock. An operating concern facing a price below its cost should cut output, idle or exit, not keep paying staff for goods the market does not take.

The offered quantity is also fixed. A producer large enough to move the price should pick quantity and price to maximise its own profit against the demand curve it faces (the elasticity is `DEFAULT_DEMAND_PRICE_ELASTICITY` in `sim/world/market.py`), which would give markups from market power instead of price-taking at cost. Not built.

Evidence: `python3 sim/test_regressions.py --jobs 1 --only per_producer_supply` shows a cost-above-price offer sitting out; no test covers a firm closing a concern for it.

What it would take: a producer decision step through the one goods market (any actor, not only firms), reading last year's clearing price against the producer's cost; waste by-products keep their negative value (Complaint 309).

Related: 375, 309, 329.
