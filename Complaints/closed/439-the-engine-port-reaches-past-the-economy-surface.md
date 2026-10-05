# The engine port reaches past the economy surface

**Status:** closed - the port files import only `sim.economy.api` and read no record field (`test_economy_imports`); the folded-in items are done: the trade registry keeps and passes every field (`trades.json` states literacy, teacher, tools, staffing resource and a sourced fatality risk, which the port passes to the economy's `TradeSpec`), and `data/world/service_lives.json` gives durable goods their service lives (`test_port_trade_and_goods_data`). Open remainder: `difficulty` and `fallback` of a trade are still derived in code, and carts and ships are not goods in the production data yet.

Done: `sim/engine/economy_port*.py` (setup, year, health) import the economy only through `sim/economy/api.py`,
and `sim/tests/test_economy_imports.py` fails on any other `sim.economy.*` import there or on any `.record`
read. The write side of the record that the port used to reach into is now named functions on the surface:
`economy_from_record`, `blank_economy`, `export_record`, `finish_spin_up`, `move_goods`,
`settle_founder_takings`, `shown_prices_of`, plus the earlier read accessors. `test_economy_api` checks that
everything the engine imports is published.

## Folded in (what remains)

Overlapping issues closed into this one; each closed file keeps its full text.

- 443 (`closed/443-goods-service-lives-never-reach-the-economy.md`): goods service lives never reach the economy (port passes empty service lives; no service life in data).
- 444 (`closed/444-danger-pay-is-always-zero.md`): danger pay is always zero: trades.json has no fatality field and the port passes only training years.
- 429 (`closed/429-the-trade-registry-drops-fields-labour-needs.md`): the trade registry drops fields labour needs.
