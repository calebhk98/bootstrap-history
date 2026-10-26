# Module `freight`

Carriage of goods at home and abroad: carriers and their costs, the cheapest route over the map's tiles, what merchants add on a foreign route, and the dues of a haul.

**Status:** moved (branch `mr/freight`). The package is `sim/freight/`; this file now describes what shipped, not the draft
proposal. Where the draft differed, "What changed from the draft" says how. Counts below come from the module spec
(`python3 -c "import sys; sys.path.insert(0,'.'); from sim.freight.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads))"`).

## What changed from the draft

- **Views:** 15 instead of 4, and no `route_cost`, `trader_economics` or `route_dues`. The draft's `route_cost` was one
  quote over twelve old methods that take five different argument lists (a partner record, two tiles, a material, an
  imbalance, a cargo class); a caller asks one of those questions, so the views are the questions: `foreign_route`,
  `route_freight_per_tonne`, `material_route`, `tile_haul_cost`, `partner_route_cost`, `freight_mode_costs`,
  `freight_handling_costs`, `material_carriage_per_tonne`, `material_freight_factor`. `trader_economics` (a keyed view
  over six methods) is four quotes plus the composite `trader_cost_share`: the merchants' margin, cycle, agent cost
  and cargo loss take different arguments (some a demand, some a price flexibility) and a caller reads two or three of
  them, so one record would compute terms nobody asked for, and a route of no legs makes some of them undefined that
  the old callers never evaluated. `route_dues` had no reader at all (the draft's own floor flag): the dues are paid by
  the command `PayRouteDues`, and the per-holder sums are the module's own methods.
- **`carrier_models` stays a view** (draft: under the three-caller floor). Its readers are the module's own rules and
  foreign trade's lift arithmetic (`_route_lift_years_per_tonne`, `_route_capital_per_lift_tonne`), which reads each
  leg's carrier by mode; foreign trade reads it through the forwarder until it moves.
- **Three views already existed under bridge names and are now freight's:** `tile_haul_cost` (coin's carriage
  surcharge), `partner_route_cost` (coin's keeping of coin held abroad) and, for living stock's landed price and carry,
  the trader quotes. `partner_route_cost` reads the route the partner's facts hold (`partner_route`, bridged to
  foreign trade's `_foreign_economy_facts`) rather than searching again: the facts remember the route for the year and a
  fresh search could answer differently after the market's flows changed.
- **Dropped as dead code:** `land_freight_money_per_tonne_km`, `material_freight_cost_per_kg`,
  `domestic_haul_money_per_tonne` and `domestic_haul_dues_per_tonne` had no caller outside the tests.
- **`route_dues_treasury` is not a method.** The account a holder's dues go into is the view `holder_treasury` (an id);
  the payment is the ledger command `PayActor(payer, payee, amount, purpose)` (new, in `sim/ledger/commands.py`, applied
  by the bridge). A government the cast does not hold yet is opened by that command, as `treasury_of` opened it.
- **Not freight's:** `trader_cargo.py` (`TraderCargoMixin`) settles trader cargo legs into the agent economy and the
  partners' coin; it stays for `foreign_trade`. The merchant-house arithmetic is `sim/world/merchant_house.py` and
  `merchant_terms.py`, already plain.
- **Cycles in the view graph** (draft: `freight` and `foreign_trade` read each other): `freight` reads foreign trade's
  `route_lift_years_per_tonne`, `route_capital_per_lift_tonne`, `lift_capacity_tonnes` and
  `opening_carriers_per_route`; foreign trade's lift arithmetic reads freight's `carrier_models`. Per view the graph is
  acyclic (`carrier_models` -> the lift views -> the trader quotes).

## At a glance

| Measure | Value |
|---|---|
| Views / commands | 15 / 1 (+ the ledger's new `PayActor`, sent) |
| Views of other modules it reads | 27, none cached (see the spec's `READS_BY_OWNER`) |
| Commands of other modules it sends | `PayActor` (the ledger's) |
| `legacy_*` reads (debts) | `legacy_world_map` (the handle the geography package's searches take) |
| State | none; the module remembers a carrier table, the routes of hauled materials and the year's tile-to-tile cost, all rebuilt on demand and never saved |
| Log lines written | none |
| Plain modules moved | `haul_route.py` -> `sim/freight/route.py`; `foreign_route_choice.py` -> `route_choice.py`; `freight_markup` -> `rules.freight_markup`; `dues_money_per_tonne`, `handling_money_per_tonne` -> `rules.py` |

## Mixin classes absorbed

| Class | File | Where it went |
|---|---|---|
| `ForeignRoutesMixin` | `foreign_routes.py` (deleted) | `sim/freight/models.py` (carriers, mode costs), `routes.py` (the route search), `rules.py` |
| `DomesticHaulMixin` | `domestic_haul.py` (deleted) | `sim/freight/haul.py` |
| `ForeignTradersMixin` | `foreign_traders.py` (deleted) | `sim/freight/traders.py` |
| `RouteDuesMixin` | `route_dues.py` (deleted) | `sim/freight/dues.py` |
| `FreightMixin` | `economy_freight.py` | its freight half (the cart's physical inputs, the source tiles, the distance, the markup, the carriage per tonne, the team size and the feed and wage constants) moved to `haul.py` and `constants.py`; the price factor, the demand grouping, the nitre and shortage methods stay for `materials` and `resources` |
| `scarcity_factor` | `freight_markup.py` (renamed) | `sim/engine/material_scarcity.py`, for `materials` |

## Views

| View | Kind | Answers | Old name |
|---|---|---|---|
| `carrier_models` | table | `{mode: (physical inputs, carrier prices, working days a year, hull loss per 1000 km)}`, kept while the price table, the sea crew's wage, the map and the team size hold. | `_carrier_models` |
| `freight_mode_costs` | quote (imbalance, modes, cargo) | Home money per tonne-km by mode: feed and crew, the carrier's capital at the market rate, hull losses, the return leg. | `_freight_mode_costs` |
| `freight_handling_costs` | table | Money per tonne charged once per leg of a mode: port handling and the geography's dues at the carriers' wage. | `_freight_handling_costs` |
| `foreign_route` | quote (partner record, imbalance, cargo) | The cheapest `Route` from a partner's tiles to this society's, or None. | `_foreign_route` |
| `route_freight_per_tonne` | quote (partner record, imbalance) | Its cost per tonne; infinite when no route joins. | `_route_freight_per_tonne` |
| `material_route` | quote (partner record, material, goods route) | The route a partner's material travels: the goods route, or the stock route for animals. | `_material_route` |
| `tile_haul_cost` | quote (origin, destination) | Home money per tonne over the cheapest route between two tiles, zero where none joins them; remembered for the year. | `tile_haul_cost` (was bridged) |
| `partner_route_cost` | keyed | Home money per tonne over the route the partner's facts hold; None when none. | `partner_route_cost` (was bridged) |
| `material_carriage_per_tonne` | quote (material, price per tonne) | Money per tonne to carry a hauled material, on top of its price where sold. | `material_carriage_per_tonne` |
| `material_freight_factor` | keyed | Markup on a material's book price for its haul. | `material_freight_factor` |
| `trader_margin_share`, `trader_cycle_years`, `trader_agent_cost`, `cargo_lost_share`, `trader_cost_share` | quote | What merchants add to a route: markup, years money is tied up, agents' pay per tonne, share lost, and the merchants' cost over freight. | `_trader_margin_share`, `_trader_cycle_years`, `_agent_cost_per_tonne`, `_cargo_lost_share`, `_trader_cost_share` |

None is cached: the prices, wages, ways and ledgers they are worked from are still written outside their owners'
commands. The route searches are the hot part; the module keeps the same caches the mixins kept (the carrier table,
the hauled materials' routes by everything they were priced from, the year's tile-to-tile cost).

## Commands

| Command | Does |
|---|---|
| `PayRouteDues(payer, route, tonnes, limit)` | The payer (a cast actor, by id) pays each holder of the tiles the dues are levied at, scaled down so the total stays within `limit`; sends the ledger's `PayActor` per holder in sorted order. Answers the money paid. |

## Reads it needs, by the owner that will publish them

Bridged in `sim/engine/bridge_freight.py` under the name the owner will publish: `techniques_with_results`, `wage`,
`trade_population`, `market_rate`, `households_loanable_funds`, `material_prices`, `material_price`, `held_techniques`,
`built_ways`, `material_source_tiles`, `route_km_to`, `goods_carried_last_year`, `working_age`, `partner_market_book`,
`partner_route`, `route_lift_years_per_tonne`, `route_capital_per_lift_tonne`, `lift_capacity_tonnes`,
`opening_carriers_per_route`, `holder_treasury`, and the debt `legacy_world_map`. Reused: `civilisation`, `year`,
`hour_wage`, `hours_per_person_year`, `foreign_economies`, `tile_owner`. The ledger's `PayActor` is applied there too.

`wage` is the wage schedule's money for an hour of a trade (`labour.wage_per_hour`); the labour market's quote is the
existing `hour_wage`. They differ, and the freight rates read the first.

## Year phases

None of its own.

## Callers outside the module that still use a forwarder

`_foreign_route`, `_route_freight_per_tonne` (foreign economies' facts, goods market offers), `_freight_mode_costs`
(economy port setup), `_carrier_models` (foreign payments), `material_carriage_per_tonne` (goods market pricing),
`_trader_margin_share`, `_cargo_lost_share`, `_trader_cycle_years`, `_agent_cost_per_tonne` (goods market offers),
`_domestic_flow_ledger` (disease port), `pay_route_dues` (the agents' trade view) and the two constants
`FREIGHT_DRIVER_WAGE_TRADE`, `FREIGHT_FEED_PRICE_MATERIAL` (economy port setup). All in `sim/engine/forward_freight.py`.
`FreightMixin.material_price_factor` reads `material_freight_factor` as a view.

## Hard spots that remain

- The route a partner's facts hold (`partner_route`) is foreign trade's cache; freight's `partner_route_cost` can go
  only when the facts do.
- `foreign_economies._foreign_economy_facts` searches the same route twice (`_foreign_route`, then
  `_route_freight_per_tonne`); kept, since removing it is not a move.
- A partner is passed to `foreign_route` as its civilisation record (the old method also took an id and loaded it;
  no caller did).
- Route choice reads the domestic flow ledger of the economy and the foreign market book, both still written by their
  owners' unmoved code.
