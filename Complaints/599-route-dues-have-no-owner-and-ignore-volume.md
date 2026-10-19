# Route dues are a flat per-mode charge with no owner, no response to volume and no competition between routes

**Status:** open

Part of Complaint 487 (No diplomacy).

Tile ownership is no longer static (483, closed).

**What is wrong.** Dues are a labour-hour charge on a change of mode, so toll revenue cannot shift when a competing overland route opens.

**Evidence.** `dues_hours_per_tonne` in `sim/geography/queries.py` has no tile; consumers are `foreign_routes._freight_handling_costs` and `domestic_haul`.

**Why it matters.** The group models toll revenue that shifts when a competing route opens.

**What it would take.** Dues become a per-edge cost owned by the tile's owner, set by policy and responding to volume, in `routes_compile` and `routes_search`, with the consumers above reading it.

**Test.** A test builds two routes between the same markets: dues go to the owner of the tile, and opening the competing route moves traffic and the first owner's toll revenue.
