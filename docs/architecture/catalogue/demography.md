# Module `demography`

Population: counts by age, by tile, urban share, food eaten, recovery after shocks.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 4 / 4 |
| Old methods and properties owned (after regrouping) | 19 |
| Of those, referenced from another module's mixin code | 5 (3 classed read-only or pure by Appendix B, 2 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 8 (5 from mixins, 3 only from outside) |
| Views per used name | 0.50 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 4 |
| Views of other modules it reads | 10, from 6 modules |
| Commands of other modules it sends | 5 |

**Existing surface and files.** Existing standalone model: `sim/world/demography.py`. Engine: `FoodEatenMixin`, `DemographicRecoveryMixin`, `RegionalPeopleMixin`, `UrbanShareMixin`, and `Sim.pop_scale/_adult_equivalent_population/_apply_population_mortality_shock/_refresh_demographic_indexes` (`core.py`).

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `Sim` | `sim/engine/core.py` | 4 | 3 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 6 | 0 |
| `FoodEatenMixin` | `sim/engine/food_eaten.py` | 2 | 1 |
| `DemographicRecoveryMixin` | `sim/engine/demographic_recovery.py` | 1 | 1 |
| `RegionalPeopleMixin` | `sim/engine/regional_people.py` | 4 | 0 |
| `UrbanShareMixin` | `sim/engine/urban_share.py` | 5 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_computed_urban_ceilings`, `_people_for_urban_share`, `household_food_kcal_per_day`, `pop_children`, `pop_elderly`, `pop_working_age`, `regional_kcal_per_day`, `regions_of_people`, `step_regions_of_people`, `urban_ceilings`, `urban_people_by_tile`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `DemographyWorld`, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.population.food_eaten_over_need` | world | - | - |
| `state.population.pop_children` | world | core 2 | core 1, <engine-functions> 1 |
| `state.population.pop_elderly` | world | core 2 | core 1, <engine-functions> 1 |
| `state.population.pop_working_age` | world | core 2 | core 1, <engine-functions> 1 |
| `state.population.population_change_last_year` | world | <ui> 3 | <ui> 1 |
| `state.population.regional_eaten_over_need` | world | campaigns 2 | - |
| `state.population.regions` | world | - | - |
| `state.population.urban_share_of_people` | world | - | - |
| `state.population.yearly_record` | world | <ui> 3 | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `population` | table | no | People in total and by age band; adult equivalents; the scale against the opening population. | `pop_scale`, `_adult_equivalent_population` | `population.pop_children`, `population.pop_working_age`, `population.pop_elderly`, `population.population_change_last_year` | - | `people` | 12 |
| `people_by_tile` | keyed | no | People on each tile, and the urban share of them. | `regions_of_people`, `people_by_tile`, `urban_people_by_tile`, `urban_fraction`, `urban_ceilings` | `population.regions`, `population.urban_share_of_people` | `land.tiles_owned_by` | `people` | 3 |
| `food_eaten` | table | no | Food eaten over need, nationally and by region; the kcal per day a region eats. | `regional_kcal_per_day`, `household_food_kcal_per_day` | `population.food_eaten_over_need`, `population.regional_eaten_over_need` | - | `people`, `food` | 1 |
| `yearly_record` | table | no | The year's demographic record (births, deaths, causes). | - | `population.yearly_record` | - | `people` | 1 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `food_eaten`, `yearly_record`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 5 methods are referenced from other modules' mixin code: 1 are replaced by a view here, 4 by a command. 3 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 8 used names, 8 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `urban_fraction`, `urban_people_by_tile`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `KillPeople` | tile or national, cohort shares, cause | `_apply_population_mortality_shock`, `epidemic_year` deaths, disasters. Methods: `_apply_population_mortality_shock`, `_refresh_demographic_indexes` | `sim/engine/core.py (_apply_population_mortality_shock)`, `sim/engine/disease_port.py (epidemic_year)`, `sim/engine/mod_effects.py` | `no_such_tile` | `population.pop_children`, `population.pop_working_age`, `population.pop_elderly` |
| `MovePeople` | from_tile, to_tile, count | Migration and settlement. | `sim/engine/mod_effects.py`, `sim/engine/colonies.py:75,100` | `tile_not_held` | `population.regions` |
| `StepPopulation` | year | `_demographic_recovery`: the yearly recovery after shocks, fed by the farm year. Methods: `_demographic_recovery` | `sim/engine/demographic_recovery.py:155-166` | none: always applies | `population.yearly_record` |
| `RecordFood` | tile, eaten, needed | `record_food_eaten`. Methods: `record_food_eaten` | `sim/engine/food_eaten.py` | none: always applies | `population.food_eaten_over_need`, `population.regional_eaten_over_need` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `population.pop_children`: 3 sites: `sim/engine/core_properties.py:807`, `sim/engine/saveload.py:36`, `sim/engine/core.py:575`
- `population.pop_elderly`: 3 sites: `sim/engine/core_properties.py:829`, `sim/engine/saveload.py:38`, `sim/engine/core.py:577`
- `population.pop_working_age`: 3 sites: `sim/engine/core_properties.py:818`, `sim/engine/saveload.py:37`, `sim/engine/core.py:576`
- `population.population_change_last_year`: 1 site: `sim/ui/proto/dispatch.py:236`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `agriculture`: `agriculture.farm_holdings` (farm_stock_kg, holdings.farm_stock_kg); `agriculture.farm_weather` (_farm_year_weather_seed, _pooled_farm_weather_multiplier)
- `disease`: `disease.epidemic_forecast` (epidemic_deaths_by_tile)
- `land`: `land.tile_facts` (geography, geography.borders_among); `land.tiles_owned_by` (home_tiles_held, input of demography.people_by_tile); `land.transport` (economy.improvements)
- `living_stock`: `living_stock.relief` (relief_kcal_per_day)
- `reporting`: `reporting.event_log` (household.log)
- `workforce`: `workforce.labour_market` (labour._farming_technique, labour.town_mortality_premium_by_tile); `workforce.staff` (labour, labour.held_technologies)

Sends (commands of other modules):

- `agriculture`: `RecordFarmYear`
- `disease`: `RunEpidemicYear`
- `land`: `FoundColony`
- `reporting`: `RecordEvent`
- `workforce`: `NotePay`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `money_world`: `_demographic_recovery` (`step_phase_money.py:180`), which calls `step_regions_of_people` and `advance_colonies` (`demographic_recovery.py:181-188`)
- `market`: `record_food_eaten`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| engine/agents_port* | 3 | `urban_fraction`, `_adult_equivalent_population`, `people_by_tile` |
| labour | 1 | `pop_scale` |
| ui | 1 | `pop_scale` |
| engine/mod* | 1 | `_apply_population_mortality_shock` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `pop_scale` 1; agents_port: `urban_fraction`, `people_by_tile`; labour: `pop_scale`.

## (h) Hard spots and caches

- `_demographic_recovery` is fed by farm results (`farm_last_harvest_kg`, `farm_last_marginal_product`, `farm_last_shortfall_kg`) and writes them back (`demographic_recovery.py:155-166`): a read-and-write loop with agriculture within one function; give agriculture a `FarmYear` result view and demography a command to apply.
- Tiles are keyed by the land module's ids; `regions_of_people` rebuilds from `population.regions` plus land membership.
- `pop_*` fields are aliased through the forwarding properties in `core_properties.py`; they are written by Sim itself (`core.py`) and by an engine function module.

Caches and version counters held today (feed for task 1.2):

- `_urban_ceilings_cache` (`urban_share.py:33`)
- `_last_demographic_step`, `_last_regional_step`, `_last_farm_year`, `_last_farm_workers_fte` lazy fields (`demographic_recovery.py`, `regional_people.py`)

Detected by the cache scan in this module's mixin files: `engine/urban_share.py:33 __dict__[_urban_ceilings_cache]`.
