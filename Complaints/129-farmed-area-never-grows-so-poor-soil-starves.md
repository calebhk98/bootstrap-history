# Farmed area is fixed at the start, so labour cannot answer a food shortfall

**Status:** partly - clearing, best-first ladder and the rent API landed; the price cache still keys on civilisation only

Soil now changes only how much food a hectare yields (Complaints/50). Less food
should make food scarcer and pull workers onto the farm, and it does, but the
response stops at the cleared farm area: `farm_workers_needed`
(`sim/labour/labour_allocation.py`) caps workers at `farm_land.hectares` over
hectares per worker, and `farm_land.hectares` is fixed at construction from the
population alone. On poorer ground the labour cap is reached in the first years and
the shortfall then persists, so the civilisation shrinks.

Measured by year-by-year trace of the labour response (need, hands moved, marginal
product) for England and Norse: the need saturates at the area cap from the first
year; the mobility rate and marginal product do not bind. Setting the farm area to
the arable ground the held tiles contain (a probe, not committed; compare the
two runs of a no-intervention century for each base civilisation) removes most of
the decline, and the remaining shortfall is the first-year starting hit.

This is `sim/world/agriculture.py`'s missing mechanism (b), the extensive margin:
cleared area should grow toward the arable ceiling, paid for with clearing labour,
and `sim/world/land.py` rent should read the same area. Not a number to tune.

Related: `python3 sim/audit_costs.py` style measurement does not exist for this;
the trace was a throwaway script and is not committed.

## What landed

Cleared area grows when hands beyond what the farm can crop exist, paid at a declared labour cost per hectare (agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE, temporary_heuristic), best ground first via land.territory_farmland ladder. land.margin_outcome_for_civilization takes farmed_hectares to read the same ladder. Not done: engine/prices.py caches solved prices per civilisation id, so the live farmed area is not yet passed into the rent solve; keying the cache on it needs a cheaper solve. Tests: sim/tests/test_farm_clearing.py.
