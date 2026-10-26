# Module `foreign_trade`

Trade with partner countries: their economies as markets, what they can supply, how trade is paid in coin and lifted by carriers, and the traders' books with them.

**Status:** moved (branch `mr/foreign-trade`). The package is `sim/foreign_trade/`; this file now describes what shipped, not the draft proposal. Counts come from the module spec
(`python3 -c "import sys; sys.path.insert(0,'.'); import sim.engine.core; from sim.foreign_trade.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads))"`).

## What changed from the draft

- **Views:** 30 instead of 4, and none of the draft's four names survives as written. The draft's `partners`, `foreign_supply`, `lift` and `actor_trade` each stood for many old methods with different argument lists (a partner id, a route, a material, a commodity); a caller asks one of those questions, so the views are the questions, under the names the migration had already bridged (`partners`, `partner`, `partner_refusal`, `partner_gate`, `partner_landed_price`, `partner_carry`, `foreign_economies`, `partner_coin_standard`, `partner_opening_facts`, `partner_market_book`, `partner_route`, `route_lift_years_per_tonne`, `route_capital_per_lift_tonne`, `lift_capacity_tonnes`, `opening_carriers_per_route`, `foreign_coin_home_units`, `foreign_coin_partner_units`) plus the ones the engine's callers needed: `partners_in_agent_economy`, `partner_facts`, `commodity_materials`, `foreign_supply_tonnes`, `partner_book_entry`, `lift_left_tonnes`, `trade_value_in_year`, `actor_home_trade`, `actors_carry`, `landed_cost`, `partner_price_per_unit`, `partner_price_response`, `cargo_legs`.
- **Commands:** 8 instead of 5. `SettleFlow`, `RecordStockTaken` and `CloseMarketsTo` already lived here (living stock sends them); `NoteActorTrade`, `NoteActorHomeTrade`, `NoteCargoLeg`, `SettleTraderCargo` and `ClosePartnerBooks` are new. The draft's `NoteActorTrade` stood for two methods (`note_actor_trade`, `note_actor_home_trade`) and `SettleTraderCargo` for two (`settle_trader_cargo`, `note_cargo_leg`); each is its own command. `ClosePartnerBooks` takes no year: the books close on the year that is running. `RecordStockTaken` and `CloseMarketsTo` write a partner's state (an actor of the cast); they stay here because they are what a partner suffers from the buyer, and they reach the actor through the `legacy_actor_registry` debt until the actors module moves.
- **`ChangeCapacityPool` is not foreign trade's.** `state.economy.capacity_pool` holds the hours-denominated entries (`scholar_hours` and the like) the founder's tonnes ledger sweeps out of itself (`economy_materials.py`); nothing reads it and nothing about it concerns a partner. The draft attributed it by the word "capacity". It stays in `EconomyState` for the materials or ledger module.
- **`_foreign_ledger` does not create state on first read.** The draft's hard spot is wrong: `create=False` returns a blank ledger that is not stored, and only the settlement and the lift record store one (`create=True`). The read became `ledger_of(partner)` and the two writers create it inside the module's own commands. A partner's ledger cannot be made at load time instead: partners come and go with the year and a ledger made for each would change the saved game.
- **`_foreign_entry` still opens a book entry on first use**, from the partner's own demand (`partner_entry`). Opening them all when the partner is loaded would add entries for goods the game never asks about, which changes the saved book; so the opening stays lazy, inside the module, behind `partner_book_entry` and `partner_price_response` (both are quotes that write the module's own state; `cached=False`).
- **The gate is a refusal built here from a knowledge fact.** `partner_gate` is the module's; the question under it (does the acting seat hold the action whose results return this partner) is a view of its own, `partner_reached`, bridged to `partner_gate_refusal` until knowledge moves.
- **State:** one world dataclass, `ForeignTradeWorld`, holding five of the draft's six fields: `market_book` (was `foreign_market_book`), `actor_trade` (`foreign_actor_trade`), `home_actor_trade`, `ledgers` (`foreign_ledger`) and `trade_by_year` (`foreign_trade_by_year`). The trader cargo legs (`economy.agent_economy["cargo"]`) stay in the agent economy's record, read and written through the `legacy_agent_economy` view: moving them would add an always-present empty field to the save where the base has an absent key, which the equivalence check reports. They go with the markets module.
- **Not a single owner of the partner's files.** The economies file with mods applied (`foreign_economy_records`), a civilisation file by id (`civilisation_record`), what a partner makes and charges at its own opening technologies (`partner_own_economy`) and what its households buy (`partner_household_demand`) are data loaded by engine functions that read mods and the price solver. The module reads them as bridged views; `foreign_economies.py`, `foreign_capacity.py` and `foreign_payments.py` are gone, and the two plain data functions that remain are `sim/engine/foreign_economy_data.py` and `sim/engine/partner_demand.py`.
- **Plain modules moved:** `country_trade_years.py` -> `sim/foreign_trade/country_trade_years.py` (pure; the agent economy still keeps the book it counts in, `stored["country_trade_by_year"]`, and calls these functions).
- **Cycles in the view graph:** coin reads `foreign_coin_*`, `partner_coin_standard`, `partner_opening_facts` and `foreign_economies` from here; here the settlement reads coin's `home_coin_stock`, `partner_coin_opening` and `coin_carriage_units`. Freight reads `partner_route`, `partner_market_book`, `lift_capacity_tonnes`, the `route_*lift*` views and `opening_carriers_per_route`; here the lift reads freight's `carrier_models` and the landed price reads freight's trader quotes. Per view the graph is acyclic (`coin_carriage_units` reads `partner_route_cost`, not the ledger).

## At a glance

| Measure | Value |
|---|---|
| Views / commands | 30 / 8 |
| Views of other modules it reads | 33 (the spec's `READS_BY_OWNER`); none cached |
| Commands of other modules it sends | `PayActorFromEdge` and `PayEdgeFrom` (the ledger's), `NoteTraderMargin` (the actors') |
| `legacy_*` reads (debts) | `legacy_actor_registry` (the cast), `legacy_agent_economy` (the cargo legs), `legacy_world_map` |
| State | `ForeignTradeWorld` (world scope); caches of facts, chains and demand are rebuilt on demand and never saved |
| Log lines written | none |
| New commands in other packages | `PayActorFromEdge` (ledger; applied by the ledger module), `NoteTraderMargin` (actors; applied by the bridge) |

## Mixin classes absorbed

| Class | File | Where it went |
|---|---|---|
| `ForeignEconomiesMixin` | `foreign_economies.py` (deleted) | `economies.py` (who partners are, their facts, refusals), `capacity.py` (book entries) |
| `ForeignCapacityMixin` | `foreign_capacity.py` (renamed) | `capacity.py` (supply, openings, chain); the data functions `household_tonnes_by_material` and `budget_scaled_final_tonnes` stay in `sim/engine/partner_demand.py` |
| `ForeignPaymentsMixin` | `foreign_payments.py` (deleted) | `payments.py` (ledgers, settlement, lift), `rules.py`, `constants.py` |
| `ForeignActorTradeMixin` | `foreign_actor_trade.py` (deleted) | `actor_trade.py` (tallies, price responses, the year's close), `rules.py` |
| `TraderCargoMixin` | `trader_cargo.py` (deleted) | `cargo.py` (legs, settlement, duty, true-up) |

The partner landed price and the carry of a smuggled load (`quotes.py`) came from `bridge_living_stock.py`; the stock-taken and market-closing writes (`governments.py`) from the same file.

## Views

| View | Kind | Answers | Old name |
|---|---|---|---|
| `partners`, `partners_in_agent_economy`, `foreign_economies` | table | Enabled economies for the year; those inside the agent economy; those trading by the books. | `partner_countries`, `partners_in_agent_economy`, `foreign_economies` |
| `partner` | keyed | `{civ, has_government, stock_taken}` for living stock. | bridged `partner` |
| `partner_coin_standard`, `partner_opening_facts` | keyed | A partner's coin metal and weight; the population and wage its opening coin stock is sized from. | bridged |
| `partner_gate`, `partner_refusal` | quote | Why a partner cannot be traded with yet; why it will not sell a material. | `partner_gate_refusal`, `partner_refusal` |
| `partner_facts`, `partner_route` | keyed | Solved materials, population, prices in home money, route and freight of a partner, remembered per seat until the price table, the techniques known or the coin price change; the route alone. | `_foreign_economy_facts` |
| `commodity_materials` | keyed | Material keys that count as a commodity. | `_commodity_materials` |
| `foreign_supply_tonnes` | quote | Tonnes a year a partner can sell of a material. | `foreign_supply_tonnes` |
| `partner_market_book`, `partner_book_entry` | keyed, quote | A partner's book by commodity; one entry, opened on first use. | `foreign_market_book`, `_foreign_entry` |
| `route_lift_years_per_tonne`, `route_capital_per_lift_tonne`, `lift_capacity_tonnes`, `lift_left_tonnes`, `opening_carriers_per_route` | quote, table | Carrier-years and carriers' capital a tonne of yearly lift needs on a route; the route's yearly lift; what is left this year; the carriers a route opens with. | the same private names |
| `foreign_coin_home_units`, `foreign_coin_partner_units` | table, keyed | Coin the home society gained over all partners; a partner's gain. | read of `economy.foreign_ledger` |
| `trade_value_in_year` | quote | Imports and exports in home money in a year the book keeps. | read of `economy.foreign_trade_by_year` |
| `actor_home_trade`, `actors_carry` | keyed, quote | Tonnes actors landed in and took from the home market; whether actors carry a good toward or from a partner. | same |
| `landed_cost`, `partner_price_per_unit`, `partner_price_response` | quote | A cargo's cost on landing; a partner's price in home money; the factor a further cargo puts on it. | same |
| `partner_landed_price`, `partner_carry` | quote | Home money per tonne delivered from a partner; the carrying cost and loss of a load smuggled out. | bridged |
| `cargo_legs` | table | The legs noted since the last settlement. | `cargo_legs` |

## Commands

| Command | Does |
|---|---|
| `SettleFlow(partner, tonnes, value)` | Pays the partner in its coin's metal (nothing while the metal has no home price) and notes the flow in the ledger and the year's trade value. |
| `RecordStockTaken(partner, material, units)`, `CloseMarketsTo(partner, party, until)` | Write the partner's state: stock smugglers took, a shut market. |
| `NoteActorTrade(partner, material, tonnes, to_partner, landed_cost)`, `NoteActorHomeTrade(material, tonnes, landing)` | Tally an actor's cargo for the partner's book and the home market's price response. |
| `NoteCargoLeg(...)` | Keep a trader's shipment as a leg until the year's market has cleared. |
| `SettleTraderCargo(results)` | Settle every leg: pay the partners, count the lift, pay the tariff, true the trader's purse up. |
| `ClosePartnerBooks()` | Clear every partner's book on the year's cargo and reset the tallies. |

`SettleTraderCargo` sends the ledger's `PayActorFromEdge` / `PayEdgeFrom` and the actors' `NoteTraderMargin`; the margin is noted first, and a trader the cast does not hold (a refusal) is neither paid nor charged, as before.

## Reads it needs, by the owner that will publish them

Bridged in `sim/engine/bridge_foreign_trade.py`: `foreign_economy_records`, `civilisation_record`, `partner_own_economy`, `partner_household_demand`, `home_unit_price`, `commodity_record`, `market_floor_ratio`, `national_output`, `tracked_materials`, `mineral_share_of_tiles`, `partner_reached`, and the debt `legacy_agent_economy`; the command `NoteTraderMargin`. Reused: `year`, `civilisation`, `techniques_held`, `acting_seat`, `material_prices`, `household_prices`, `material_commodity`, `market_rate`, `legacy_actor_registry`, `legacy_world_map`, freight's `foreign_route`, `route_freight_per_tonne`, `carrier_models`, `material_route`, `trader_cost_share`, `trader_agent_cost`, `cargo_lost_share`, and coin's `home_coin_stock`, `coin_carriage_units`, `partner_coin_opening`, `partner_price_level`.

## Year phases

None of its own. `ClosePartnerBooks` is sent from the end of the market phase (`market_clearing._step_market`), where `close_partner_books` was called; `SettleTraderCargo` from the economy year (`economy_port_year.run_year`), after the market has cleared.

## Callers outside the module that still use a forwarder

All in `sim/engine/forward_foreign_trade.py`: `partner_countries`, `partners_in_agent_economy`, `foreign_economies` (agents port, economy port setup, goods market offers, tile ownership, world hazards, the UI), `partner_civ` (goods market offers, economy port year), `_foreign_economy_facts` (agents port trade and revenue, economy port partners, goods market offers), `_commodity_materials` (goods market offers), `_foreign_entry` (agents port trade), `foreign_supply_tonnes` (goods market imports and offers, material reach), `foreign_lift_left_tonnes` (goods market imports), `partner_price_per_unit`, `partner_price_response`, `actors_carry`, `actor_home_trade`, `landed_cost`, `note_actor_trade`, `note_actor_home_trade`, `cargo_legs`, `note_cargo_leg`, `settle_trader_cargo` (agents port trade, economy port year) and `close_partner_books` (market clearing). The economy port's two settlements send `SettleFlow` and read `foreign_coin_partner_units` directly.

## Hard spots that remain

- Partner facts are remembered per seat in a dict the module keeps (the old cache lived on the seat's household facade); it is keyed by the price table's identity, so `cached=False` stays until prices are written only through their owner's commands.
- `partner_book_entry` and `partner_price_response` write the module's own book when they open an entry; a read-only version needs the opening done once per partner when the roster is seeded and the saved book to change with it.
- `partner_own_economy` and `partner_household_demand` are `lru_cache`d across games in one process (they were before); the module calls the engine's functions through the bridge and cannot see whether mods changed the data.
- `partner_catch_chance` (living stock's) still sits in `bridge_living_stock.py`: it asks the partner's state for its reach, which is the actors module's world.
- The cargo legs belong in the module's state once the agent economy's record stops being one dict the markets module will own.
- `economy.capacity_pool` is unclaimed (see above).
