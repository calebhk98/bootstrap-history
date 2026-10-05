# The engine port reaches past the economy surface

**Status:** open - narrowed: the port files import only `sim.economy.api` and read no record field (`test_economy_imports`); only the folded-in items below remain.

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
