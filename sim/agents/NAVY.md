# Naval purchases

The state's navy line staffs the operating trades of a vessel and bids for
the hulls it lacks. Coast length sets the desired fleet through the existing
sea-control heuristic. Shipwrights work for the producers that supply the
market, rather than appearing on the state's standing payroll.

A production entry's `naval_crew` maps trade ids to people per vessel. The
state considers vessels its country can produce and chooses the lowest
annual hull replacement cost plus crew pay. Merchant hulls have no naval
crew declaration and are available for later carrier-capital work.

`capital_asset: true` identifies a complete asset an actor retains after a
market purchase. Its service life comes from `data/world/service_lives.json`.
Material inputs bought for immediate use keep their existing consumption
behavior. The market port holds delivered assets in the buyer's asset
account; save/load carries those inventories through the economy book.
Only actual market fills become assets. Unfilled bids return their budget.

The economy wears asset accounts supplied in `YearInputs.durable_users`,
using its ordinary durable-wear mechanism. Next year's replacement bid
accounts for the surviving stock. Wear is recorded in the year's physical
accounts. Replacement stands for repair and refit consumption until the
carrier-capital work separates individual components and maintenance.

The ship recipes cite reconstruction evidence, distinguish lightship mass
from loaded displacement, and label estimated material allocations and
work rates. Their confidence labels are part of the data, not promises of
archaeological precision. Measure the value chain with
`python3 -m sim.tests --only ship_purchases`.
