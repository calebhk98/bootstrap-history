# Module `coin`

Coin as a metal: stock and price level, revaluation, keeping, carriage and theft.

**Status:** moved (branch `mr/coin`). The package is `sim/coin/`; this file now describes what shipped, not the draft
proposal. Where the draft differed, "What changed from the draft" says how. Counts below come from the module spec
(`python3 -c "import sys; sys.path.insert(0,'.'); from sim.coin.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies))"`).

## What changed from the draft

- **Views:** 13 instead of 5, and no `coin_metal`, `price_level`, `exposure` or `coin_carriage` as proposed. The proposal
  merged views by topic (stock, hoard and report under `coin_stock`); a caller wants one question answered, so the views
  are the questions: the home and a partner's price level are two views (a table and a keyed view, as their callers
  read them), the
  hoard and its rounded report are two (the screens round, the rules do not), and the exposure is the household's
  (`household_exposure`), since another holder's exposure is built inside the theft command from the actor registry.
  `coin_metal` (the draft's view under the three-caller floor) is not a view: the ratio by metal is the module's own
  state, read by the module's own price levels and written by its phase.
- **Commands:** `ChargeKeeping` (actors), `ChargeActorsTheft`, `ChargeHouseholdTheft`, `PlunderHousehold`. `Revalue` is
  the phase `coin_revaluation`, not a command: nothing but the year sends it. The draft's `ChargeTheft(holder, share)` is
  three commands because the three callers (the actors' year, the household's money step, a sack or a bandit year) carry
  different facts; a holder is not a field a caller can name, since the module reads who holds what itself.
- **Exposure holds amounts only.** The draft's hard spot (`Exposure` lots carried `take` closures that mutate purse,
  stock and granary) is gone: a lot names its `store` and the theft sends the ledger's `TakeGoods` command (a command
  the ledger lacks, so it lives in `sim/ledger/commands.py` and the bridge applies it) and `PayEdge` / `PayEdgeFrom`.
- **Coin carriage became an answer to a ledger extension point.** `sim/agents/ledger.py` `AFTER_TRANSFER` is a global the
  engine switched on with `coin_carriage_listening()` around the actors' year and `pay_state`. It is now the ledger
  module's: the view `transfer_listening` (a quote returning the context) installs the ledger's `after_transfer`, which
  asks the extension point `transfer_surcharge` (LIST) for `(edge, amount, cause)` answers and posts each one from the
  payer to the edge, inside the same switched-off window as before, so order and amounts are unchanged. Coin
  provides `coin.carriage`; a mod withdraws it by that name. A provider receives the two parties as objects, since the
  hook sits inside a free function; reading what they are (record, location) is the one duck-typed read left.
- **State:** `CoinWorld.metal_ratios` (was `economy.coin_metal_ratios`), relocated in `sim/tests/equiv_fields.py`. The
  society's opening coin (`_opening_coin_value`) and each partner's opening stock are never-saved caches on the module.

## At a glance

| Measure | Value |
|---|---|
| Views / commands | 13 / 4 (+ the phase `coin_revaluation`, one provision to `transfer_surcharge`) |
| Views of other modules it reads | 30, none cached (see the spec's `READS_BY_OWNER`) |
| Commands of other modules it sends | `PayEdge`, `PayEdgeFrom`, `TakeGoods` (all the ledger's) |
| `legacy_*` reads (debts) | `legacy_acting_household`, `legacy_actor_registry`, `legacy_agent_world` |
| Log lines written | none (the draft's mixins wrote none; nothing converted to `RecordEvent`) |

## Mixin classes absorbed

| Class | File | Where it went |
|---|---|---|
| `CoinRevaluationMixin` | `coin_revaluation.py` (deleted) | `sim/coin/prices.py` |
| `CoinHoardMixin` | `coin_hoard.py` (deleted) | `sim/coin/keeping.py` |
| `CoinCarriageMixin` | `coin_carriage.py` (deleted) | `sim/coin/carriage.py` |
| `TheftChargeMixin`, `HoldingsExposureMixin` | `theft_charge.py`, `holdings_exposure.py` (deleted) | `sim/coin/theft.py`, `sim/coin/exposure.py` |
| `ForeignPaymentsMixin` | `foreign_payments.py` | its coin half moved to `prices.py`; the ledger of partners, `_settle_flow` and the lift stay for `foreign_trade` |
| `theft_exposure.py`, `coin_guard_rule.py` | engine | `sim/coin/theft_exposure.py`, `sim/coin/rules.py` |

## Views

| View | Kind | Seat | Answers | Old name |
|---|---|---|---|---|
| `home_coin_metal` | table | no | The home society's coin metal. | `home_coin_metal` |
| `home_coin_stock` | table | no | Coin units the society holds: its opening stock plus what trade brought in. | `home_coin_stock_units` |
| `home_price_level` | table | no | The one price level the engine reads. | `home_price_level` |
| `partner_price_level` | keyed | no | A partner's price level. | `partner_price_level` |
| `partner_coin_opening` | keyed | no | Coin a partner opened with. | `_partner_coin_opening_units` |
| `coin_kg_per_unit` | table | no | Metal in one coin of the home standard. | `coin_kg_per_unit` |
| `coin_keeping_cost` | quote | no | Yearly cost of keeping an amount of money as coin. | `coin_keeping_cost_per_year` |
| `coin_keeping_due` | quote | yes | What keeping the household's coin costs this year and what its purse and credit can pay. | `coin_keeping_due` |
| `coin_hoard`, `coin_hoard_report` | table | yes | The household's money as coin: metal, mass, keeping cost; and the rounded form for screens. | `coin_hoard`, `coin_hoard_report` |
| `coin_carriage_units` | quote | no | Partner coin units the carriers take to move an amount over the route to a partner. | `coin_carriage_units` |
| `household_exposure` | table | yes | What the household keeps by kind, for theft, sack and banditry. | `founder_exposure` |
| `household_visible_scale` | table | yes | How visible the household is to thieves and the state. | `founder_visible_scale` |

None is cached: each reads the foreign ledgers, the purse or the stock, all still written outside their owners' commands.

## Commands

| Command | Does |
|---|---|
| `ChargeKeeping` | Every cast actor in business that holds money pays its guards (a foreign actor at its own country's pay). |
| `ChargeActorsTheft` | Every home-country cast actor loses its expected theft. |
| `ChargeHouseholdTheft(keeping_paid, keeping_owed)` | The acting household loses its expected theft; its guard counts for the share of keeping its purse paid. Answers the money taken. |
| `PlunderHousehold(strength, cause, order_holds)` | A sack or a bandit year, by the same exposure. Answers the money taken. |

## Reads it needs, by the owner that will publish them

Published by their owners, except the ledger's `held_goods`
(published by the ledger module): `opening_money_per_labour_hour`, `headcount`, `opening_population`, `goods_quote`,
`foreign_economies`, `foreign_coin_home_units`, `foreign_coin_partner_units`, `partner_coin_standard`,
`partner_opening_facts`, `partner_route_cost`, `coin_value_ratio`, `lent_share`, `visible_scale`, `order_reach`,
`eminence`, `farm_holdings`, `farm_land_price`, `forest_holding`, `home_country`, `tile_known`, `tile_haul_cost`,
`legacy_agent_world`. Reused: `civilisation`, `money_per_labour_hour`, `credit_limit`, `standing`, `acting_balance`,
`legacy_acting_household`, `legacy_actor_registry`.

## Year phases

- `coin_revaluation` (world), after `market`: records the market ratio of the home coin metal and of each partner's.
  The market phase ended with this and `record_wage_market_ratios`; the latter is now the phase `wage_market_ratios`
  right after, so the order is unchanged.
- The household's keeping due (a quote) and `ChargeHouseholdTheft` are called from the money step, the actors'
  `ChargeKeeping` and `ChargeActorsTheft` from the actors' year, `PlunderHousehold` from the sack and banditry
  hazards. Each sits between steps that belong to other modules, so none is a phase of its own: the due must be read
  before the year's payments and the theft after the guards are paid.

## Callers outside the module that still use a forwarder

`home_coin_metal` (real price ratios), `home_price_level` (techniques in use, production, labour port),
`partner_price_level` (foreign actor trade, goods market offers, the living-stock bridge), `home_coin_stock_units`
(economy port), `_partner_coin_opening_units` (economy port year), `coin_carriage_units` (`_settle_flow`),
`coin_hoard_report` (the screens). All in `sim/engine/forward_coin.py`.

## Hard spots that remain

- `home_coin_stock` is a second tally of the society's coin beside the book (`STATE_OWNERSHIP_MAP.md`): the opening
  stock plus the sum of the partners' ledgers (`foreign_coin_home_units`), the latter foreign trade's.
- The carriage provider reads a party's `record.country` and `location()` off the objects the hook hands it.
- `tile_haul_cost` keeps its per-year route cache in the bridge (`sim.__dict__`), as the mixin did.
