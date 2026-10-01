# Foreign trade has no balance of payments and no fleet

**Status:** partly - goods in and out are paid in coin that moves between a per-partner ledger and a coin stock (`sim/world/balance_of_payments.py`, `sim/engine/foreign_payments.py`): a persistent deficit drains the stock, never below zero, and lowers the traded-price level so imports get dearer and exports cheaper; each route has a fleet whose yearly lift caps the tonnes that cross, and which grows from what it could not carry within what yards can build; still open: the price level touches only traded prices (590), partners stay off by default because flows are not yet credible (591), the opening fleet and yard growth are labelled heuristics

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
