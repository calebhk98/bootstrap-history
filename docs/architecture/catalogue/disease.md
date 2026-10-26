# Module `disease`

Epidemics and endemic disease: the disease package, burden, forecasts and medical coverage.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 3 / 2 |
| Old methods and properties owned (after regrouping) | 17 |
| Of those, referenced from another module's mixin code | 9 (8 classed read-only or pure by Appendix B, 1 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 12 (9 from mixins, 3 only from outside) |
| Views per used name | 0.25 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 3 |
| Views of other modules it reads | 11, from 8 modules |
| Commands of other modules it sends | 5 |

**Existing surface and files.** Existing: `sim/disease/` (14 files; `api.py` 23 lines; `WALL = two-way`; draws only from its own seeded generators, never `Sim.rng`). Engine: `DiseasePortMixin` (8), `CoverageMixin` (8), `Sim._disease_burden`, `disease_burden.py`, `mortality_shock.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `Sim` | `sim/engine/core.py` | 1 | 1 |
| `DiseasePortMixin` | `sim/engine/disease_port.py` | 8 | 4 |
| `CoverageMixin` | `sim/engine/coverage.py` | 8 | 4 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `disease_year`, `endemic_death_rates`, `epidemic_hits_seats`, `people_per_unit`, `people_who_can_use`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `DiseaseWorld`, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.disease.deaths` | world | - | - |
| `state.disease.introduced` | world | - | - |
| `state.disease.records` | world | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `disease_burden` | keyed | no | Endemic burden and death rates by tile; the burden held by techniques. | `_disease_burden`, `disease_burden_held`, `endemic_death_rates` | `disease.records`, `disease.introduced`, `disease.deaths` | `demography.people_by_tile`, `land.tile_facts` | `disease` | 3 |
| `epidemic_forecast` | keyed | no | Forecast and deaths by tile; regional and frontier loss. | `epidemic_forecast`, `epidemic_deaths_by_tile`, `regional_disease_loss`, `frontier_disease_loss` | - | `demography.people_by_tile`, `disease_burden` | `disease` | 5 |
| `coverage` | keyed | no | Who can use a technique, the share covered, units for coverage, the row for a node. | `coverage_nodes`, `coverage_share`, `coverage_row`, `units_for_coverage`, `people_per_unit`, `people_who_can_use` | - | `demography.population`, `production.institution_units`, `mechanics.capability_sets` | `coverage` | 4 |

**Coverage.** 9 methods are referenced from other modules' mixin code: 8 are replaced by a view here, 1 by a command. 3 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 12 used names, 12 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `RunEpidemicYear` | year | `epidemic_year`, `disease_year`: advances the package and sends deaths. Methods: `epidemic_year`, `disease_year`, `epidemic_hits_seats` | `sim/engine/disease_port.py`, `sim/engine/shock_year.py` | none: always applies | `disease.records`, `disease.introduced`, `disease.deaths` |
| `RollOut` | seat, node, units | `roll_out`: put coverage units into use. Methods: `roll_out` | `sim/ui/proto/ (roll_out)`, `sim/engine/coverage.py` | `no_units`, `not_known` | - |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `demography`: `demography.people_by_tile` (input of disease.disease_burden, input of disease.epidemic_forecast); `demography.population` (input of disease.coverage)
- `knowledge`: `knowledge.techniques_held` (has, projects.done)
- `land`: `land.tile_facts` (input of disease.disease_burden, world_map)
- `mechanics`: `mechanics.capability_sets` (DISEASE_BURDEN_TECH_IDS, input of disease.coverage); `mechanics.mechanic` (mechanic, nodes_with_mechanic)
- `production`: `production.institution_units` (input of disease.coverage, institution_unit_ceiling, institution_units); `production.running` (running)
- `reporting`: `reporting.event_log` (household.log)
- `seats`: `seats.seat_list` (playing_seats)
- `workforce`: `workforce.staff` (household.artisans, household.employees, household.scholars, labour ...)

Sends (commands of other modules):

- `hazards`: `RunRandomEvents`
- `reporting`: `RecordEvent`
- `ventures`: `OpenVenture`
- `workforce`: `Fire`, `Hire`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- inside `_refresh_demographic_indexes`/`step_regions_of_people` (`regional_people.py:46` calls `epidemic_year`); the package steps at sub-year resolution inside one call

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 4 | `coverage_row`, `coverage_nodes`, `roll_out`, `coverage_share` |
| engine/ui* | 2 | `_disease_burden`, `epidemic_forecast` |
| engine/agents_port* | 1 | `frontier_disease_loss` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `coverage_row`, `coverage_nodes`, `roll_out`, `coverage_share`; engine ui: `_disease_burden`, `epidemic_forecast`; agents_port: `frontier_disease_loss`.

## (h) Hard spots and caches

- `epidemic_year` writes deaths by directly mutating population, directors_extra, artisans and the log: it becomes KillPeople, LoseStaff and RecordEvent.
- `disease_port` caches entries, deaths by tile, forecast and names in `Sim.__dict__` (`disease_port.py:107,194,208,253`), keyed by year; they are view caches.
- `_disease_burden` (in `Sim`) is called by diffusion and land: reads of a computation that depends on techniques held (`coverage`).

Caches and version counters held today (feed for task 1.2):

- `__dict__['_disease_entry']`, `_epidemic_deaths_by_tile`, `_epidemic_names`, `_epidemic_forecast` (`disease_port.py`)

Detected by the cache scan in this module's mixin files: `engine/disease_port.py:107 __dict__[_disease_entry]`, `engine/disease_port.py:194 __dict__[_epidemic_deaths_by_tile]`, `engine/disease_port.py:253 __dict__[_epidemic_forecast]`, `engine/disease_port.py:208 __dict__[_epidemic_names]`.
