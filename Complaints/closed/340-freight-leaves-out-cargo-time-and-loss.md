# Freight leaves out the cargo's own time and loss

**Status:** closed - the fleet follows the carriage asked of it against its lift, growing within what yards build and shrinking when idle (`sim/tests/test_fleet_follows_margin.py`); cargo interest, spoilage and loss are in the trade clearing (`sim/geography/cargo_cost.py`)

Foreign route freight prices the carrier (`Complaints/326`) but not the cargo:
interest on its value while it travels months, spoilage, and the share lost with
a hull. Those depend on the good's value, so they cannot be a per-tonne-km rate
over the route and need a per-good charge in the trade clearing. The opening fleet
and the yards' yearly growth limit are labelled heuristics, and the fleet grows
whether or not carrying pays. Domestic freight (`economy_freight.py`) still omits the
cart's capital.

## Done

Fleet growth from the freight margin over the carrier's cost of capital: the rate pays the carrier's capital at the market rate over a full working year, so carriage asked beyond the lift earns more than capital costs and idle lift earns less. `foreign_fleet_year_end` (`sim/engine/foreign_payments.py`) closes part of that gap each year, labelled `FLEET_MARGIN_ADJUSTMENT_SHARE_PER_YEAR`.

Related: 323, 326.

Owner decision (2026-10-02): somewhat important, lower priority.
