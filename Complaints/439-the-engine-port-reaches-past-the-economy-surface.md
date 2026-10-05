# The engine port reaches past the economy surface

**Status:** open - draft; `sim/economy/api.py` exists, the port still imports submodules

`sim/economy/api.py` now publishes every name the port takes from `sim.economy`, plus read accessors for the
record fields the port reads. The three port files (`sim/engine/economy_port_setup.py`,
`economy_port_year.py`, and nothing in `economy_port.py` itself) still import submodules and read
`economy.record.*` directly, so the economy cannot be reimplemented behind its surface. Inventory:
`grep -rnE "sim\.economy" --include=*.py sim | grep -v "^sim/economy/\|^sim/tests/"`.

Point 1: move the port onto the surface. Proposed patch (not applied; the port is outside the economy
folder):

```diff
--- a/sim/engine/economy_port_setup.py
+++ b/sim/engine/economy_port_setup.py
-from sim.economy import households, taxes, tile_costs
-from sim.economy.currency import currency_from_coin_standard
-from sim.economy.setup import EconomySetup, TradeSpec, goods_specs
+from sim.economy.api import (EconomySetup, TradeSpec, currency_from_coin_standard, goods_specs, households,
+                             taxes, tile_costs)
@@
-    from sim.economy.recipes import recipes_from_production_data
+    from sim.economy.api import recipes_from_production_data
--- a/sim/engine/economy_port_year.py
+++ b/sim/engine/economy_port_year.py
-from sim.economy.economy import Economy
-from sim.economy.producers import Producer, expected_output_prices, live_input_prices, live_wages
-from sim.economy.protocols import AgentOrders, YearInputs
-from sim.economy.foreign import external_orders
-from sim.economy.types import EDGE_EXTERNAL, EDGE_LEGACY, GoodsMove, Offer, Transfer
-from sim.economy.record import EconomyRecord
-from sim.economy.unit_cost import variable_cost_per_run
-from sim.economy.notional import shown_prices
-from sim.economy.year_close import rebase_price_level
-from sim.economy.year_labour import trade_premium
+from sim.economy import api as economy_api
+from sim.economy.api import (EDGE_EXTERNAL, EDGE_LEGACY, AgentOrders, Economy, EconomyRecord, GoodsMove, Offer,
+                             Producer, Transfer, YearInputs, expected_output_prices, external_orders,
+                             live_input_prices, live_wages, rebase_price_level, shown_prices, trade_premium,
+                             variable_cost_per_run)
@@ _foreign volumes (around line 186)
-        volumes = {}
-        for key, volume in economy.record.volumes.items():
-            good = key.split("|", 1)[0]
-            volumes[good] = volumes.get(good, 0.0) + volume
+        volumes = economy_api.traded_volumes(economy)
+        opening = economy_api.opening_quantities(economy)
@@
-            market = max(volumes.get(good, 0.0), economy.record.opening_basket.get(good, 0.0))
+            market = max(volumes.get(good, 0.0), opening.get(good, 0.0))
@@ _settle_foreign (around line 238)
-        book, money = economy.record.book, economy.setup.currency_id
         coin = economy.setup.coin_per_unit
-        paid_in = book.edge_net(EDGE_EXTERNAL, money)            # exports less imports
-        volume = book.edge_volume(EDGE_EXTERNAL, money)
+        paid_in = economy_api.external_trade_net(economy)            # exports less imports
+        volume = economy_api.external_trade_volume(economy)
@@ _inputs (around line 274)
-        yields = {producer_id: weather for producer_id, producer in economy.record.producers.items()
+        yields = {producer_id: weather for producer_id, producer in economy_api.producers_of(economy).items()
@@ _spin_up (around line 285)
-        basket = record.opening_basket
+        basket = economy_api.opening_quantities(economy)
@@
-            now = ([outcome.price_level, record.memory.rates.get(economy.setup.currency_id, 0.0)]
+            now = ([outcome.price_level, economy_api.interest_rate(economy) or 0.0]
@@ answers (around line 310)
-            wages = {}
-            for key, wage in record.memory.wages.items():
-                trade = key.split("|", 1)[0]
-                wages.setdefault(trade, []).append(wage)
+            wages = economy_api.wages_by_trade(economy)
@@
-                             record.memory.rates.get(self._economy.setup.currency_id))
+                             economy_api.interest_rate(self._economy))
```

What the patch leaves, because it needs write-side surface functions rather than reads:
`economy.record.book` moves in `_founder_orders` and `_settle_founder` (`move_many`, `transfer`,
`balance`, `holdings`; `account_balance` and `account_holdings` cover the reads), `record.memory.year = 0`
and `rebase_price_level(setup, record)` in `_spin_up`, and `record.to_record()` /
`EconomyRecord.from_record` for saving. Each wants a named function on the surface (for example
`settle_account_to_edge`, `reset_clock`, `export_record`) before the port stops touching the record.

Point 2: once the patch is in, `sim/tests/test_economy_imports.py` should require the three port files to
import only `sim.economy.api` (and fail on any other `sim.economy.*` module), the way the labour and
geography walls are held, and `sim/tests/test_economy_api.py` already checks that everything outside
imports is published there.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 443 (`closed/443-goods-service-lives-never-reach-the-economy.md`): goods service lives never reach the economy (port passes empty service lives; no service life in data).
- 444 (`closed/444-danger-pay-is-always-zero.md`): danger pay is always zero: trades.json has no fatality field and the port passes only training years.
- 429 (`closed/429-the-trade-registry-drops-fields-labour-needs.md`): the trade registry drops fields labour needs.
