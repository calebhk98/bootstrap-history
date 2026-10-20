# Route dues are a flat per-mode charge with no owner, no response to volume and no competition between routes

**Status:** closed - dues are owed to the current holder of the tile they are levied at, per tonne carried, paid to its treasury

Part of Complaint 487 (No diplomacy).

Tile ownership is no longer static (483, closed).

**What is wrong.** Dues are a labour-hour charge on a change of mode, so toll revenue cannot shift when a competing overland route opens.

**Evidence.** `dues_hours_per_tonne` in `sim/geography/queries.py` has no tile; consumers are `foreign_routes._freight_handling_costs` and `domestic_haul`.

**Why it matters.** The group models toll revenue that shifts when a competing route opens.

**What it would take.** Dues become a per-edge cost owned by the tile's owner, set by policy and responding to volume, in `routes_compile` and `routes_search`, with the consumers above reading it.

**Test.** A test builds two routes between the same markets: dues go to the owner of the tile, and opening the competing route moves traffic and the first owner's toll revenue.

## Resolution

- `sim/geography/route_dues.py` (`route_dues_levied`, `route_dues_by_holder`, via the api): a found route's dues, one per change of mode, each owed to whoever holds the leg's starting tile now.
- `sim/engine/route_dues.py` (`pay_route_dues`): the payer pays each holder's treasury (a country's government, or a seat) per tonne carried. A trader's cargo (`World.pay_route_dues`) pays the dues out of its freight, so money is conserved. A tile with no owner levies nothing; its dues stay in the carriers' freight.
- The route search still prices dues per tonne in each mode's handling and is unchanged, so a competing way moves traffic through the normal route choice and the toll revenue follows the legs the traffic takes; because holders are read when cargo is carried, a transfer of a tile moves the revenue with no new search.
- The per-tonne rate is still the labelled mode datum (`dues_hours_per_tonne`); an owner-set rate belongs with the policy and treaty work of 487.
- Held by `sim/tests/test_route_dues_owner.py`.
