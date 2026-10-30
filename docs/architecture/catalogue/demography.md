# Module `demography`

The nation's people: counts by age, by region and tile, the town share, the food they ate, the yearly step that feeds and steps them
after shocks, and each seat's farm holding the farm year works on.

**Status:** moved, on branch `mr/demography` (package `sim/demography/`, bridge `sim/engine/bridge_demography.py`, forwarders
`sim/engine/forward_demography.py`). The draft of task 1.5 (a read-only analysis of `e8b004c`) is replaced by what the move found; "What
the move changed in this draft" lists each correction. Re-measure counts with `python3 -c "import sys; sys.path.insert(0,'.'); from
sim.demography import module_spec as m; s=m.MODULE_SPECS[0]; print(len(s.publishes), len(s.applies), len(s.reads), len(s.sends))"`.

## What the move changed in this draft

- **The nation's `Population` object is gone; its three bands are the module's state.** The draft kept `Sim.population` (a
  `sim/world/demography.py` `Population`) and mirrored it into `state.population.pop_*` at a save and back at a load (the "population
  sync" in `_reconnect_state_hooks`). The module owns the three floats (`DemographyWorld.pop_children`, `pop_working_age`,
  `pop_elderly`) as the one copy; there is no mirror, no sync and no `hasattr(self, "population")` guard. A reading of the bands is
  `People` (`sim/demography/people.py`), a `Population` with no random stream of its own: `total`, `nutrition_ratio(food)`,
  `adult_equivalents`. Changing a reading changes nothing. The nation's `Population` never drew from its own stream (nothing passes
  `jitter=True`), so dropping the object and its seed loses nothing.
- **Views: sixteen, not four.** The draft's `population`, `people_by_tile`, `food_eaten` and `yearly_record` stand, but the callers
  ask narrower questions than the draft's grouping: `population` (the bands), `population_total`, `working_age`, `pop_scale`,
  `default_population`, `population_change_last_year`, `yearly_record`, `people_by_tile`, `regional_people_by_band` (the regions by band as a copy, for the disease module), `people_by_band`, `nutrition_ratio` (a quote), `urban_people_by_tile`, `urban_ceilings`, `urban_fraction`, `food_eaten`, `demographic_flows` and
  `regional_flows_last_year` (the last yearly step's flows, kept in memory, never saved), `farm_holdings`. Four of the names were already
  published by the bridge for other modules (`food_eaten` by campaigns, `working_age` by freight, `population_total` by reporting, `pop_scale`
  and `default_population` by materials) and the module publishes them under the same names and shapes; the bridge entries are deleted.
  `household_food_kcal_per_day` and its rule `food_kcal_per_day` had no caller outside tests and are gone.
- **The draft's `StepPopulation` is a command, and the rest of the draft's commands are named for what they do.** Applied: the four
  other modules already sent (`AddCaptives`, `CutPopulation`, `RefreshDemographicIndexes`, `KillPeople`: the bridge entries are
  deleted), `OpenPopulation` (the opening), `StepPopulation` (the yearly step, sent from `_step_money_world`), `RecordFoodEaten`
  (from the economy's outcome, with the numbers built by the engine forwarder: a command carries no object), `SendSettlers`
  (the colonies' settlers leave the working age; was `MovePeople`), `NotePopulationChange` (the protocol's year report), and the farm
  holding's four: `ChangeFarmland`, `SetClearedFarmland`, `SetFarmHoursNeeded`, `TakeFromGranary`. `MovePeople` as drafted is not built:
  `mod_effects.move_people` moves people between two strata (actors' state), not between tiles.
- **`RecordFarmYear` is not a command.** The farm year and the holding are one module now, so the step writes the holding directly. What
  the draft needed it for was the holding being agriculture's; it moved here instead (below).
- **The farm holding moved here, completely.** The draft's agriculture catalogue left `state.holdings.farm_*` (seven fields) for
  "demography and workforce". They are `DemographySeat` now (a seat slot, so a handover carries them). Their outside readers and writers
  became the view `farm_holdings` (agriculture's name, with a superset shape: hectares and granary as before, plus the area cleared,
  the last year's shortfall, harvest and marginal product, and the hours the farm needs) and the four commands. Agriculture lost its own
  `farm_holdings` publication and `legacy_farm_holdings`; `InvestFarm` and `SellFarm` send `ChangeFarmland` and read the view. The farm
  workforce (`sim/labour/labour_allocation.py`) sends `SetClearedFarmland` and `SetFarmHoursNeeded` and reads the view through the
  labour world's `farm_holdings()`; the household facade, `core_properties.py` and `state_holdings.py` lost the fields.
- **The yearly step reads the farm workforce's work as commands to workforce.** `AllocateFarmWorkforce`, `ApplyLandClearing` and
  `UpdateWages` (new, in `sim/workforce/commands.py`, applied by the bridge) replace `self.labour.allocate_farm_workforce`,
  `apply_land_clearing` and `update_wages`. The colonies' yearly step is `AdvanceColonies` (land's, `sim/land/commands.py`), the
  epidemic year `RunEpidemicYear` then `HitSeatsWithEpidemic` (disease's; the mods' externalities add their deaths between them through the
  bridged quote `externality_deaths`, and the burden, the endemic rates and the deaths by tile are read as disease's views afterwards: the
  order `forward_disease.epidemic_year` keeps), the migrants' contact `RecordMigrantContact` and a partner's strata `ScaleStrata`
  (actors'). The order inside the step is the old one.
- **`wage_index` and `_disease_burden` are not demography's.** `wage_index` is workforce's (the catalogue's own `workforce.wage_index`); it
  stays on `Sim` and reads `pop_scale`. The module reads it as the view `wage_index` hazards already used, plus a new bridged
  `wage_index_terms` (the base index and the scarcity elasticity, the two numbers the wage-cascade note needs). `_disease_burden`,
  `disease_burden.py` and `DISEASE_BURDEN_TECH_IDS` are disease's and stay. `mortality_shock.py`'s `cut_cohorts` is a rule of this
  module (`rules.py`).
- **`urban_people_by_tile` still writes.** It seeds the stored opening shares at the first read of a tile set, from the civilisation's typed
  figure and the ceilings of that moment; moving the seeding to a command would move the moment, and the shares with it. The write is the
  module's own state, so the rule "write only inside your module" holds; the view is uncached. It is the draft's "published as a view but
  still a writer".
- **`mod_effects.kill_people` sends `KillPeople`.** It keeps the mod-facing checks (a cause, a share between zero and one, the mod's
  namespaced kind) and sends; the module cuts the home cohorts or sends `ScaleStrata` for a partner and writes the event with how many died
  (`RecordWorldEvent`). `mod_effects.people_of` (also read by the yearly invariants) is a second copy of the module's `_people_of`; it
  goes with the invariants.
- **State relocations** are in `sim/tests/equiv_fields.py`. `ScenarioState._said_wage_cascade` moved to `DemographyWorld.said_wage_cascade`.
  `PopulationState` and `SimulationState.population` are gone; the save's required sections name `modules` instead of `population`.

## Files

| File | Holds |
|---|---|
| `sim/demography/counts.py` | the bands, the opening, the shock, the settlers, the deaths, the wage-cascade note |
| `sim/demography/regions.py` | the regions, the food eaten, the regions' step with migration and the epidemic year |
| `sim/demography/urban.py` | the towns' ceilings, the town shares, the urban fraction |
| `sim/demography/recovery.py` | the yearly step: the farm year, the regions' feeding, the record, the colonies |
| `sim/demography/farm.py` | the seat's farm holding and its four commands |
| `sim/demography/rules.py` | the arithmetic as plain functions (cut, scale, seed, food, wage cascade, the record's row) |
| `sim/demography/people.py` | `People`, a reading of the bands |
| `sim/demography/constants.py` | `DEFAULT_POPULATION_100AD`, `POP_SCALE_FLOOR` (moved from `core.py`, same names and kinds), the record's length |
| `sim/engine/bridge_demography.py` | what the module reads and sends until the owners move |
| `sim/engine/forward_demography.py` | the forwarders |

## State owned

| Path now | Was | Scope |
|---|---|---|
| `modules.demography.pop_children`, `pop_working_age`, `pop_elderly` | `population.pop_*` (mirrors of `Sim.population`) | world |
| `modules.demography.population_change_last_year`, `food_eaten_over_need`, `regional_eaten_over_need`, `regions`, `urban_share_of_people`, `yearly_record` | `population.*` | world |
| `modules.demography.said_wage_cascade` | `scenario._said_wage_cascade` | world |
| `seats.*.modules.demography.farm_hectares`, `farm_stock_kg`, `farm_cleared_hectares`, `farm_last_shortfall_kg`, `farm_last_harvest_kg`, `farm_last_marginal_product`, `farm_hours_needed` | `holdings.farm_*` | seat |

## Views

All are uncached except `default_population`: the people's are three floats, and the rest read the held land, the labour market and the
built ways, which are written outside any command of this module.

| View | Answers | Readers |
|---|---|---|
| `population` | the bands as a `People` (`total`, `adult_equivalents`, `nutrition_ratio(food)`) | the engine's forwarder `Sim.population`, the labour world, the screens, the disease step |
| `population_total`, `working_age`, `pop_scale`, `default_population` | the figures others read as numbers | reporting, freight, materials |
| `population_change_last_year`, `yearly_record` | what the demography screen and the year report print | the screens |
| `people_by_tile` | people per tile once the regions cover the tiles held, else `None` | labour, the agent ports |
| `regional_people_by_band`, `people_by_band`, `nutrition_ratio` | the regions as `[children, working_age, elderly]`, the nation's bands, the food against need | the disease module |
| `urban_people_by_tile`, `urban_ceilings`, `urban_fraction` | the town share and what each town can feed | labour, the agent ports, the disease step |
| `food_eaten` | each tile's food eaten over its need, as the economy booked it | campaigns |
| `demographic_flows`, `regional_flows_last_year` | the last yearly step's flows (births, deaths, nutrition ratio), `None` before the first | the budget view, the event causes, the screens, the disease step |
| `farm_holdings` (seat) | hectares, granary, area cleared, the last farm year's shortfall, harvest and marginal product, the hours the farm needs | coin, agriculture, labour, the price code, the agent ports |

## Commands

| Command | Fields | Answers | Sent from |
|---|---|---|---|
| `OpenPopulation` | | | `Sim.__init__` |
| `StepPopulation` | year | | the money phase |
| `RecordFoodEaten` | national, by_tile | | the market phase (the forwarder builds it) |
| `CutPopulation` | share | | hazards |
| `KillPeople` | country, share, cause, kind, tiles, facts | the world event, or a `Refusal` (`bad_share`) | hazards, `mod_effects` |
| `RefreshDemographicIndexes` | year | | hazards |
| `AddCaptives` | winner, people | the people added | campaigns |
| `SendSettlers` | people | | the colonies |
| `NotePopulationChange` | change | | the protocol's year step |
| `ChangeFarmland` | hectares | the hectares held | agriculture |
| `SetClearedFarmland`, `SetFarmHoursNeeded` | hectares, hours | | the farm workforce |
| `TakeFromGranary` | kilograms | | the ledger's `TakeGoods` (bridged) |

## Reads and sends

Reads, all bridged or published by a module that moved (`sim/engine/bridge_demography.py` unless noted): land `home_tiles_held`,
`borders_among`, `built_ways` (`bridge_freight.py`), `held_techniques` (`bridge_freight.py`); workforce `farming_technique`
(`bridge_agriculture.py`), `town_mortality_premium_by_tile`, `wage_index` (`bridge_hazards.py`), `wage_index_terms`; defence stores
`relief_kcal_per_day`; agriculture `weather_seed`, `harvest_weather`, and the farm workforce's `farm_land` and
`farm_technique_this_year`; hazards `country_strata`; core `civilisation`, `year`, `cast` (for
`AddCaptives`). The `externality` point is asked with the year only: a mod's provider is handed its own `ModAccess` (`sim/assembly/mod_access.py`).

Sends: workforce `AllocateFarmWorkforce`, `ApplyLandClearing`, `UpdateWages`; land `AdvanceColonies`; disease `RunEpidemicYear`, `HitSeatsWithEpidemic`; actors
`RecordMigrantContact`, `ScaleStrata`; hazards `RecordWorldEvent`; reporting `RecordEvent`.

## Year phases

None of its own. The yearly step is the command `StepPopulation`, sent from the middle of `_step_money_world` (after the output recovery,
before literacy and the actors); the booking of the food eaten is `RecordFoodEaten`, sent from `_step_market`. Neither phase splits.

## Forwarders left on `Sim`

`population`, `pop_scale`, `_adult_equivalent_population`, `people_by_tile`, `urban_fraction`, `_last_demographic_step`,
`farm_stock_kg` (all reads), `record_food_eaten`, and the two constants `DEFAULT_POPULATION_100AD` and
`POP_SCALE_FLOOR`. Their callers are the engine's mixins, the agent ports, the screens and the mods that read `sim.population.total`.

## Not moved

- `wage_index`, `WAGE_SCARCITY_ELASTICITY`, `_wage_index_base` (workforce's).
- `_disease_burden`, `disease_burden.py` (disease's).
- `advance_colonies`, `found_colony` and the colonies' state `holdings.colonies` (land's).
- `farm_land`, `_farm_ladder`, `_farm_arable_ceiling`, `_farm_technique_this_year` (the farm workforce's and agriculture's, on `Sim`).

## Hard spots

- The step is order-critical and kept as it was: the workforce allocation, the weather seed (the first call draws the game's salt), the
  farm year, the land clearing, the harvest figures, the wage update, the regions, the colonies, the wage note.
- Float sums keep their order: the regions' sum per band, the nation's food, the adult equivalents.
- The regions are rebuilt from the stored bands every step and kept to the nation by `keep_to_nation`; a change to the nation outside the
  step (a shock, settlers) is shared among the regions by their people.

## Caches held

Never saved, on the module: the towns' ceilings for the year (`_urban_ceilings_cache`), the last yearly step's flows and the last
regional step's flows. The write-only diagnostics `_last_farm_year` and `_last_farm_workers_fte` were dropped.
