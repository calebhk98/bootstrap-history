# Freight leaves out the cargo's own time and loss

**Status:** closed - merged into 326: the cargo's own interest, wait and sea loss (built in the trade clearing), and the open items: spoilage by good, fleet growth from the freight margin, the capital charge in domestic freight

Foreign route freight prices the carrier (`Complaints/326`) but not the cargo:
interest on its value while it travels months, spoilage, and the share lost with
a hull. Those depend on the good's value, so they cannot be a per-tonne-km rate
over the route and need a per-good charge in the trade clearing. The opening fleet
and the yards' yearly growth limit are labelled heuristics, and the fleet grows
whether or not carrying pays. Domestic freight (`economy_freight.py`) still omits the
cart's capital.

## What it would take

A per-good landed-cost term from the route's travel days (now kept on every leg),
the cargo's value and the market rate; fleet growth from the freight margin over
the carrier's cost of capital; the same capital charge in domestic freight.
