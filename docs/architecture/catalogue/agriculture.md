# Module `agriculture`

Farming: farmland, farm weather, soil nitrogen, wild stock and food potential.

**Status:** moved in part (branch `mr/agriculture`). The package is `sim/agriculture/`; this file describes what shipped, not
the draft proposal. The farm holding itself (hectares, granary, last harvest) is still the engine's `state.holdings`, which
demography and the farm workforce write; "Not moved" says what waits for them. Counts come from the module spec
(`python3 -c "import sys; sys.path.insert(0,'.'); from sim.agriculture.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads))"`).

## What changed from the draft

- **Views:** 10 instead of 5. The draft folded the geography handle's food members (`crop_sites`, `food_kcal_by_source`,
  `huntable_kcal`, `take_hunt`, `regrow_wild_stock`, `soil_nitrogen_factors`, `step_soil_nitrogen`) into agriculture's
  `farm_sites` and `wild_stock` as methods it would "replace". They stay geography's (the land module's): agriculture
  reads each as a view of the walled handle and hands it the society's rotation, crop and herd. Published: `farm_weather`
  (keyed by year), `harvest_weather` (a quote, the pooled multiplier), `weather_seed` (a quote), `farm_weather_cells`,
  `farm_sites`, `farm_territory`, `food_potential`, `wild_stock`, `farm_holdings`, `farm_land_price`.
- **Weather is not a phase.** The draft said the first read of `farm_weather` consumes randomness, so it should be a phase
  that fills it. It does not: every cell is drawn from a fresh generator seeded by (civilisation, cell, year, salt), so the
  weather is a pure function of those. The only draw from the game's dice is the salt, once, at the first seed asked for.
  That lazy draw has to stay lazy (drawing it at setup would move it in the random sequence), so `weather_seed` is a quote
  that writes the module's own `weather_salt` the first time. The salt moved from `scenario.weather_salt` to
  `AgricultureWorld.weather_salt`.
- **`farm_land_quote` became `farm_land_price`, a table.** The coin module already reads that name (bridged since coin
  moved); the price of a hectare takes no argument. It is derived: the hours constant, the money per labour hour and the
  price index.
- **Commands:** `InvestFarm` and `SellFarm`, as drafted. `RecordFarmYear` is not built (see "Not moved"). Both answer a
  value or a `Refusal` (`not_positive`, `cannot_afford`, `not_owned`); the engine forwarders turn them into the replies the
  screens read, so the wording and the unit text stay in the presentation layer.
- **`society_food_potential` is a view, `food_potential`,** though nothing outside tests reads it: it is the module's own
  headline answer (what the held land can feed), and it was already a method with a test. Under the three-caller floor,
  with `wild_stock` (one reader, living stock) and `farm_territory` (one reader, the engine's farm refresh).
- **State:** `AgricultureWorld` holds `wild_stock`, `soil_nitrogen` (from `state.economy`) and `weather_salt` (from
  `state.scenario`), relocated in `sim/tests/equiv_fields.py`. No seat state yet. The weather cells, their Cholesky factor
  and the tiles' arable shares are never-saved caches on the module, built from the held tiles at `Sim.__init__` (the same
  moment as before) by one read of `farm_weather_cells`.
- **Constants:** `FARM_WEATHER_POOLED_CELL_CAP` and `FARM_LABOUR_HOURS_PER_HA` moved to `sim/agriculture/constants.py`
  (same names, values and kinds). `Sim.FARM_COST_PER_HA` is gone; the price is `farm_land_price`.

## At a glance

| Measure | Value |
|---|---|
| Views / commands | 10 / 2 (+ the phases `wild_stock` and `soil_nitrogen`) |
| Views of other modules it reads | 20, bridged (the geography members, the labour technique and hours, the externalities, the dice) |
| Commands of other modules it sends | 2 (`PayEdge`, `ReceiveFromEdge`) |
| Forwarders left on `Sim` | 8, in `sim/engine/forward_agriculture.py` |
| Old methods removed from `Sim` | `FoodSupplyMixin` and `SoilNitrogenMixin` (both deleted), the farm-weather block of `core.py` (about 540 lines), `farm_price_per_hectare`, `invest_farm`, `sell_farm` |

Existing surface the module sits on: `sim/world/agriculture.py`, `sim/world/farming_technique.py`,
`sim/world/weather_pooling.py` (all pure), and the walled `sim/geography` food functions.

## Files

| File | Holds |
|---|---|
| `sim/agriculture/weather.py` | the cells, the seed, the pooled multiplier and the per-tile multipliers |
| `sim/agriculture/food.py` | farm sites, territory, food potential, the wild stock and its yearly step |
| `sim/agriculture/soil.py` | soil nitrogen factors, the draught herd's manure, the yearly step |
| `sim/agriculture/farm.py` | the holding view, the land price, buying and selling |
| `sim/agriculture/rules.py` | the arithmetic as plain functions (cells, capping, seed, draws, manure, refusals) |
| `sim/engine/bridge_agriculture.py` | what the module reads until its owners move |
| `sim/engine/forward_agriculture.py` | the forwarders |

## State owned

| Path now | Was | Scope | Read by | Written by |
|---|---|---|---|---|
| `modules.agriculture.wild_stock` | `economy.wild_stock` | world | living stock (through `wild_stock`) | the module |
| `modules.agriculture.soil_nitrogen` | `economy.soil_nitrogen` | world | the module | the module |
| `modules.agriculture.weather_salt` | `scenario.weather_salt` | world | the module | the module |

## Views

| View | Kind | Answers | Replaces | Readers |
|---|---|---|---|---|
| `farm_weather` | keyed by year | the year's multiplier on each weather cell that is a tile | `farm_weather_by_tile` | the economy port |
| `harvest_weather` | quote (year, stdev, harmed) | the pooled harvest multiplier, less what the externalities take | `_pooled_farm_weather_multiplier` | demography, the economy port |
| `weather_seed` | quote (year, region) | the seed of a year's draw; the first call draws the salt | `_farm_year_weather_seed` | demography, hazards, prospecting, disease |
| `farm_weather_cells` | table | the pooled cells and their arable shares | `_compute_farm_weather_cells` | the engine (builds them at start) |
| `farm_sites` | table | the crop site of each held tile under the rotation | `farm_sites` | the economy port, the farm refresh |
| `farm_territory` | table | the ladder and ceiling of the cropland | the body of `refresh_farm_territory` | the engine's farm refresh |
| `food_potential` | table | kcal a year by source, bounded by the gatherers' hours | `society_food_potential` | none yet |
| `wild_stock` | table (cached, channel `wild_stock`) | game left by tile | `economy.wild_stock` | living stock |
| `farm_holdings` | table, seat | hectares and granary stock | the bridged view coin read | coin |
| `farm_land_price` | table | money for one hectare | `farm_price_per_hectare`, `FARM_COST_PER_HA` | coin, the screens |

Only `wild_stock` is cached; the rest read the engine's household state, the held land or the mods' externalities, which are
written outside any command.

## Commands

| Command | Fields | Answers | Refusal causes |
|---|---|---|---|
| `InvestFarm` | hectares | hectares bought | `not_positive`, `cannot_afford` |
| `SellFarm` | hectares | {hectares, price, remaining} | `not_positive`, `not_owned` (facts: owned, hectares) |

Both write `farm_hectares` through `legacy_farm_holdings` and move money by the ledger's `PayEdge` and `ReceiveFromEdge`.

## The farm's own state (`farm_state.py`)

The module owns the cleared ground, the ladder, the cropland ceiling, the opening's farmed area and the year's technique, and publishes `farm_land`, `farm_technique_this_year`, `farm_ladder`, `farm_arable_ceiling`, `farm_food_demand_kg` and `opening_farmed_hectares`. The commands are `SetFarmLand`, `SetFarmTechnique`, `SetFarmTerritory` and `RecordOpeningFarm`. The save carries all but the technique, which a load resets to the default as before; a load re-sizes the cleared ground and refreshes the ladder from the held tiles (`Sim._reconnect_state_hooks`).

## Reads (all bridged unless noted)

- land: `held_tile_geometry`, `crop_sites`, `food_kcal_by_source`, `game_food_sources`, `huntable_kcal`, `take_hunt`,
  `regrow_wild_stock`, `tile_soil_nitrogen_factors`, `soil_nitrogen_after_year` (the old in-place step, now a quote that
  returns the new stock)
- workforce: `farming_technique`, `society_labour_hours`, `trade_registry`, `money_per_labour_hour` (existing, `bridge_projects.py`)
- other: `civilisation` (existing), `society_herds` (living stock), `acting_balance` (ledger), `price_index`,
  `externality_yield_factors` (the mods' externalities)
- the game's random source `game_random` (seats; for the salt) and `provider_game` (the game, handed to the mods' externality providers: their contract); debt: `legacy_farm_holdings` (the acting seat's farm section)

## Year phases

`wild_stock` and `soil_nitrogen` are `PhaseHook`s of the module (`step_wild_stock`, `step_soil_nitrogen`). `begin_world_year`
stays the engine's and calls the forwarder `refresh_farm_territory`.

## Forwarders left on `Sim`

`farm_sites`, `refresh_farm_territory`, `_farm_year_weather_seed`, `_pooled_farm_weather_multiplier`,
`farm_weather_by_tile`, `farm_price_per_hectare`, `invest_farm`, `sell_farm`. `refresh_farm_territory` is more than one
line: it sets `_farm_ladder`, `_farm_arable_ceiling` and the farm area, which are the farm workforce's, from the module's
`farm_territory`.

## Not moved (and why)

- **The farm holding** (`holdings.farm_hectares`, `farm_stock_kg`, `farm_cleared_hectares`, `farm_last_*`,
  `farm_hours_needed`) and **`RecordFarmYear`**. Nine files outside the module write or read them: the demographic step
  (`demographic_recovery.py`), the farm workforce (`sim/labour/labour_allocation.py`), the coin exposure code
  (`holdings_exposure.py`, `bridge_coin.py`'s `TakeGoods`), the household facade in `sim/agents/household.py`, the agent
  ports (`agents_port_budget.py`, `agents_port_revenue.py`), `invariants.py` and `labour_port.py`. They belong to demography,
  workforce, coin and actors; the holding moves with the last of them, and `RecordFarmYear` is the command demography and
  workforce then send. Until then `farm_holdings` is published here over `legacy_farm_holdings`.
- **`_farm_ladder`, `_farm_arable_ceiling`, `farm_land`** stay on `Sim`: the farm workforce reads them through its world
  adapter.
- **`ForwardingPropertiesMixin.farm_hectares` and `farm_stock_kg`** stay with the holding.

## Hard spots

- The salt is the one draw from the game's dice and must stay lazy and in the same place in the random sequence. The
  equivalence tool hashes the random state each year, so a draw out of order shows at once.
- The weather cells are built once at `Sim.__init__` from the civilisation as it opens (the same moment as before); a lazy
  build at the first harvest would read a civilisation that has drifted.
- A real smell kept on purpose: `farm_weather_by_tile` pools only cells that are tiles; a tile merged into a pooled cell
  has no per-tile weather and callers give it the pooled multiplier.

## Caches held

- Never saved, on the module: the weather cells, the correlation factor, the tiles' arable shares.
- Still on `Sim` (the farm workforce's): `_farm_ladder`, `_farm_arable_ceiling`.
