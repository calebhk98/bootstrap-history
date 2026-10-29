# Module `disease`

Epidemics and endemic disease in the nation: the infection records, the yearly step that kills by band and tile, the forecast the
risk screens print, the disease burden the technologies leave, and what an epidemic does to each playing seat.

**Status:** moved, on branch `mr/disease` (package `sim/disease/`, bridge `sim/engine/bridge_disease.py`, forwarders
`sim/engine/forward_disease.py`). The draft of task 1.5 (a read-only analysis of `e8b004c`) is replaced by what the move found;
"What the move changed in this draft" lists each correction. Re-measure counts with `python3 -c "import sys; sys.path.insert(0,'.');
from sim.disease import module_spec as m; s=m.MODULE_SPECS[0]; print(len(s.publishes), len(s.applies), len(s.reads), len(s.sends))"`.

## What the move changed in this draft

- **Coverage is not here.** The draft put `CoverageMixin` (`coverage_nodes`, `coverage_share`, `coverage_row`, `units_for_coverage`,
  `roll_out`) in this module. Only `disease_burden_held` is a disease rule (what share of a technology's weight counts); the rest is
  how many people a repeated work serves, which production's institution units and the UI read. It stays in `coverage.py` and the
  module reads the `coverage` and `coverage_share` views the engine bridge publishes (`bridge_diffusion.py`, `bridge_disease.py`). `RollOut`
  and the `coverage` view go to whoever takes `coverage.py`.
- **`contact_events.py` is not disease.** It tells the agents' awareness model that a conquest or a migration put people in touch
  (`awareness.record_contact`); the name is the only link. It stays in the engine for the agents' owner.
- **Views: eight, not three.** `disease_burden`, `disease_burden_held` (keyed by node), `disease_burden_weights` (were published by the
  diffusion bridge), `endemic_death_rates`, `epidemic_deaths_by_tile`, `epidemic_forecast` and `regional_disease_loss` (quotes: they take a
  food figure or a tile), `frontier_disease_loss`. The draft's `coverage` view is not published here.
- **Commands applied: two, with another shape.** `RunEpidemicYear(food_kcal_per_day, year)` answers the deaths by band, and
  `HitSeatsWithEpidemic(deaths_by_band, year)` cuts each playing seat's staff, deputies and takings and answers the share. They are
  two because the engine adds the externality providers' deaths (`externalities.add_deaths`, a mod door that is handed the whole
  game) between them, and the seats are cut by the sum. `RollOut` is not here (see above).
- **The yearly step stays inside demography's year.** `epidemic_year` is called from `step_regions_of_people`, which reads the deaths,
  the burden and the endemic rates straight away, so it is not a phase: `forward_disease.py` keeps `epidemic_year` (run the year,
  add the externalities, hit the seats, read the burden and the rates) until demography sends the commands itself.
- **Caches are the module's, not views.** The entry-days table (`_disease_entry`), the deaths by tile, the names of the killers and
  the forecast were kept in `Sim.__dict__`; they are attributes of the module, empty after a load as before. The deaths by tile
  are a cached view on the `epidemics` channel (written only by `RunEpidemicYear`); the forecast is a quote that keeps its last
  answer until the next disease year, as it did.
- **State: `DiseaseWorld` (records, introduced, deaths), world scope**, in `state.modules["disease"]`; the engine's `DiseaseState` and
  `state.disease` are gone. Relocations are in `sim/tests/equiv_fields.py`.

## At a glance

| Measure | Value |
|---|---|
| Views published | 8 (see (c)) |
| Commands applied / sent | 2 / 5 |
| Views read | 25, from 11 owners (see (e)); 9 are bridged for demography, land and coverage |
| Forwarders left in the engine | 6 (`forward_disease.py`) |

## (a) Mixin classes and files absorbed

| Class or file | Became |
|---|---|
| `DiseasePortMixin` and `DiseaseWorld` (`sim/engine/disease_port.py`) | `sim/disease/module.py` (`Disease`) over `people.py` (the nation's people and the traffic between tiles), `contact.py` (sources, routes, arrivals, technology scales), `epidemics.py` (the yearly step), `forecast.py`, `seats_hit.py`, `burden.py`; rules in `rules.py` |
| `Sim._disease_burden` (`core.py`) | `Disease.disease_burden` |
| `CoverageMixin.disease_burden_held` | `Disease.disease_burden_held` |
| `sim/engine/disease_burden.py` | `sim/disease/burden_rules.py` (`burden_from_holdings`, exported by `api.py`) |

`validate_disease_data.py` stays an engine validator: it checks the data files, not a running game.

## (b) State owned

| Field | Scope | Was |
|---|---|---|
| `records` | world | `state.disease.records` |
| `introduced` | world | `state.disease.introduced` |
| `deaths` | world | `state.disease.deaths` |

## (c) Views

| View | Kind | Answers | Cached |
|---|---|---|---|
| `disease_burden` | table | 1.0 is the full pre-industrial infectious environment, 0.0 every disease technology fully held | no: reads what is held and what coverage serves, written outside any command |
| `disease_burden_held` | keyed | The share of a node's weight that counts | no, likewise |
| `disease_burden_weights` | table | {node: weight} of the technologies that make up the burden, in tree order | no |
| `endemic_death_rates` | table | {band: excess deaths per head per year} from the endemic diseases of the land held | no |
| `epidemic_deaths_by_tile` | table | {tile: {band: deaths}} the last disease year killed | yes, channel `epidemics` |
| `epidemic_forecast` | quote | Expected deaths, infected and arrival chances for the coming year | no: the module keeps its last answer until the next disease year |
| `regional_disease_loss` | quote | The share of a working-age person on a tile the diseases take in a year | no |
| `frontier_disease_loss` | table | The mean of it over the tiles held that border one not held | no |

## (d) Commands

| Command | Fields | Answers | Sent by |
|---|---|---|---|
| `RunEpidemicYear` | food_kcal_per_day, year | {band: deaths} | `forward_disease.epidemic_year` |
| `HitSeatsWithEpidemic` | deaths_by_band, year | the working-age share killed (zero below the share a seat notices) | `forward_disease.epidemic_year` |

Sent to others: workforce `SurviveStaff`, `ScaleDeputies`, `ReportStaffReduction`; hazards `LoseCapital`; reporting `RecordEvent`.
Deaths go to demography as the answer of `RunEpidemicYear`, which the population step takes; no `KillPeople` is sent, because the
deaths enter the step by band and tile, not as a share (a change to that is demography's).

## (e) Reads

- core: `year`, `civilisation`, `legacy_world_map`, `acting_as`, `money_text`
- agriculture: `weather_seed`
- demography (bridged in `bridge_disease.py` until it moves, named as its catalogue names them where one exists): `people_by_band`,
  `nutrition_ratio`, `working_age`, `regional_people_by_band`, `urban_fraction`, `regional_flows_last_year`
- land (bridged): `home_tiles_held`
- freight: `goods_carried_last_year`
- knowledge: `techniques_held`, `held_techniques`
- mechanics: `effect_terms`, `mechanic`
- diffusion: `civ_diffusion`, `tech_effects`
- coverage (bridged): `coverage`, `coverage_share`
- seats: `seat_list`; workforce: `staff`, `staff_snapshot`

## (f) Year phases

None. The step runs inside the population step (see above).

## (g) Callers outside the module

`sim/ui` and `sim/engine/ui_port.py` (`epidemic_forecast`, `disease_burden`), `fog.py` (`epidemic_forecast`), `colonies.py`
(`regional_disease_loss`, `_disease_burden`), `agents_port_budget.py` (`frontier_disease_loss`), the diffusion module (`disease_burden`,
`disease_burden_held`, `disease_burden_weights`, through the views), `regional_people.py` (`epidemic_year`, `epidemic_deaths_by_tile`).
`sim/agents/country_disease.py` and `budget_works.py` use `disease.nation` through the package's `api.py` and are unchanged.

## (h) Hard spots

- `endemic_death_rates` reads the civilisation's own tiles (`tiles_held(civ, map)`), while the step reads the tiles the owner map gives
  the home country (`home_tiles_held`). They differ after a conquest. Kept as it was; whether the endemic rate should follow
  the owner map is a question for the land owner.
