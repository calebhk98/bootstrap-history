# Foreign trade has no balance of payments and no fleet

**Status:** closed - merged into 326: the coin ledger and per-route fleet (built) and the fleet heuristics still open; its price-level remainder stays with 135 (was 338)

A partner's demand for a good it cannot make is not bounded by what it earns
from its own exports, and sea tonnage is not bounded by any hulls. Goods with
a high value per tonne therefore flow until the exporter's capacity is
exhausted, and the exporter's capacity then grows each year while the price
stays at its ceiling.

## Evidence

`python3 sim/foreign_trade_report.py --years 100` shows Rome exporting gold to
Han in far more tonnes than the Roman gold output the book opens with, and iron
in a shortage year at a tonnage that would need a very large fleet. This is why
`enabled` stays false in `data/world/foreign_economies.json`.

## What it would take

A per-partner yearly value ledger (imports paid for by exports plus coin
metal), and hulls, pack strings and carts as capital with a build cost, so a
route's yearly tonnage is what its carriers can lift
(`sim/world/sea_freight.py` already gives the physical inputs per hull).
