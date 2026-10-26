# Module `diffusion`

How knowledge spreads: literacy, schooling, diffusion indices, disclosure and licensing, tech effects on society.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 5 / 4 |
| Old methods and properties owned (after regrouping) | 48 |
| Of those, referenced from another module's mixin code | 13 (5 classed read-only or pure by Appendix B, 8 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 28 (13 from mixins, 15 only from outside) |
| Views per used name | 0.18 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 5 |
| Views of other modules it reads | 23, from 12 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 4 |

**Existing surface and files.** Existing: `sim/agents/literacy.py` (`CountryLiteracy`), `sim/agents/adoption.py`, `awareness.py`, `imitation.py`, `licence.py`. Engine: `AdoptionMixin`, `DiffusionMixin`, `DisclosureMixin`, the literacy accessors of `ActorsMixin`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `AdoptionMixin` | `sim/engine/society_adoption.py` | 15 | 3 |
| `DiffusionMixin` | `sim/engine/society_diffusion.py` | 22 | 7 |
| `ActorsMixin` | `sim/engine/society_actors.py` | 4 | 2 |
| `DisclosureMixin` | `sim/engine/society_disclosure.py` | 7 | 1 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_advance_literacy`, `_advance_trade_absorption`, `_category_diffusion_index`, `_diffusion_category`, `_diffusion_half_life_years`, `_diffusion_pace`, `_disclosure_record`, `_grow_endemic_trade`, `_is_foreign_institution`, `_license`, `_school_literacy`, `_trade_absorption_years`, `diffusion_share`, `food_diffusion_index`, `literacy_ceiling_common`, `medical_compliance`, `medical_diffusion_index`, `set_literacy`, `staff_hire_advice`, `state_military_weapons_held`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `DiffusionSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.projects.disclosures` | seat | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `literacy` | keyed | no | Literacy by field (general, common, elite) and country; ceilings; next year's value; effective schooling flow; research productivity. | `literacy`, `country_literacy`, `research_productivity`, `literacy_ceiling_common`, `literacy_ceiling_general`, `literacy_ceiling_elite`, `literacy_next_year`, `effective_schooling_flow`, `_schooling_flow`, `_school_literacy` | - | `knowledge.techniques_held`, `demography.population`, `workforce.staff` | `literacy` | 11 |
| `diffusion_index` | keyed | no | How widely a category of knowledge has spread (food, medical, information, military), half-life, cost factor, foreign-only status, report. | `diffusion_index`, `diffusion_share`, `knowledge_half_life_years`, `food_diffusion_index`, `medical_diffusion_index`, `information_diffusion_index`, `state_military_diffusion`, `medical_compliance`, `civ_diffusion`, `_diffusible_ids`, `world_diffusion_report`, `civ_cost_factor`, `_is_foreign_only`, `_is_foreign_institution`, `needs_first` | - | `knowledge.techniques_held`, `production.running`, `mechanics.corpus`, `actors.cast` | `diffusion` | 7 |
| `diffusion_relief` | quote | no | What diffusion relieves of medical and military hazards. | `medical_diffusion_relief`, `_state_military_diffusion_relief`, `state_military_weapons_held` | - | `diffusion_index`, `disease.coverage` | - | 1 |
| `disclosure` | keyed | yes | What the seat has disclosed of a node, copy difficulty, licensable actors, the listing. | `disclosure_of`, `copy_difficulty`, `disclosure_listing`, `licensable_actor_ids` | `projects.disclosures` | `knowledge.techniques_held` | `disclosure` | 3 |
| `staff_advice` | quote | no | Where to hire a trade from (STAFF_SOURCES) and the hire advice. | `staff_hire_advice`, `STAFF_SOURCES` | - | `workforce.staff` | - | 1 |

**Coverage.** 13 methods are referenced from other modules' mixin code: 11 are replaced by a view here, 2 by a command. 15 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 28 used names, 28 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `needs_first`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `ApplyTechEffects` | seat, node | `apply_tech_effects`: a finished technique changes value weights, endemic trades and staff. Methods: `apply_tech_effects` | `sim/engine/society_adoption.py:433`, `sim/engine/projects_completion.py` | none: always applies | - |
| `AdvanceSociety` | year | `advance_society`, `_advance_literacy`, `_advance_trade_absorption`, `_grow_endemic_trade`. Methods: `advance_society` | `sim/engine/society_adoption.py` | none: always applies | - |
| `Disclose` | seat, node, to_actor, terms | `disclose`, `_license`. Methods: `disclose` | `sim/engine/society_disclosure.py` | `not_known`, `not_licensable` | `projects.disclosures` |
| `SetLiteracy` | country, field, value | `set_literacy`. | `sim/engine/society_actors.py` | none: always applies | - |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.get, actors.of_kind, actors.state ...)
- `demography`: `demography.population` (input of diffusion.literacy)
- `disease`: `disease.coverage` (coverage_nodes, input of diffusion.diffusion_relief); `disease.disease_burden` (_disease_burden, disease_burden_held)
- `knowledge`: `knowledge.techniques_held` (done_year, input of diffusion.diffusion_index, input of diffusion.disclosure, input of diffusion.literacy ...)
- `living_stock`: `living_stock.stock_status` (stock_holds_met)
- `mechanics`: `mechanics.capability_sets` (DISEASE_BURDEN_TECH_IDS); `mechanics.corpus` (corpus_diffusion_pace, input of diffusion.diffusion_index); `mechanics.effect` (effect_values); `mechanics.mechanic` (_effect_terms, mechanic); `mechanics.patronage` (school_node)
- `polity`: `polity.standing` (household.reputation); `polity.state_reach` (state_reach); `polity.state_treasury` (state_treasury)
- `production`: `production.running` (input of diffusion.diffusion_index, projects.operating, running)
- `projects`: `projects.outcome_quote` (reputation_gain_of)
- `reporting`: `reporting.event_log` (household.log)
- `seats`: `seats.seat_list` (playing_seats); `seats.seat_party` (seat_party)
- `workforce`: `workforce.hours_available` (labour.farm_share_of_hours, labour.resync_pools); `workforce.literacy_capacity` (labour.LITERACY_FACTOR_CAP, labour.LITERACY_REFERENCE_ELITE, labour.LITERACY_REFERENCE_GENERAL, labour.literate_capacity); `workforce.staff` (household.employees, input of diffusion.literacy, input of diffusion.staff_advice, labour); `workforce.trade_spread` (household.trade_introduced_year, household.trades_created, household.trades_endemic)

Sends (commands of other modules):

- `polity`: `ChangeStanding`
- `reporting`: `RecordEvent`
- `workforce`: `Hire`, `NoteTradeSpread`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `money_world`: `advance_society` (`step_phase_money.py:187`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 47 | `literacy`, `literacy_ceiling_general`, `literacy_ceiling_elite`, `effective_schooling_flow`, `world_diffusion_report`, `literacy_next_year`, `disclosure_listing`, `civ_cost_factor` |
| engine/agents_port* | 10 | `copy_difficulty`, `literacy`, `research_productivity`, `state_military_diffusion`, `_diffusible_ids`, `knowledge_half_life_years`, `disclosure_of` |
| engine/(function modules) | 6 | `literacy`, `_is_foreign_only` |
| labour | 2 | `literacy` |
| agents | 2 | `research_productivity`, `knowledge_half_life_years` |
| engine/economy_port* | 1 | `literacy` |
| engine/ui* | 1 | `_schooling_flow` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `literacy` 21, `literacy_ceiling_general` 6, `literacy_ceiling_elite` 5, `effective_schooling_flow` 4, `world_diffusion_report` 2, `disclosure_listing` 2; agents_port: `copy_difficulty` 4, `research_productivity`, `knowledge_half_life_years`; sim/labour: `literacy` 2.

## (h) Hard spots and caches

- `advance_society` writes into workforce (`labour.set_employed` at `society_adoption.py:433`) and into `value_weights` (a Sim field); both become commands and a view (`value_weights`).
- Literacy lives in `ActorsState` country objects; diffusion owns them and actors read through the view.
- `needs_first` and `_is_foreign_only` are read by project starting; their inputs are the foreign economies (foreign_trade).

Caches and version counters held today (feed for task 1.2):

- `_diffusible_ids_cache` (`society_diffusion.py:273`), `_foreign_institution_cache`, `_foreign_only_cache` (`society_diffusion.py:465,479`)

Detected by the cache scan in this module's mixin files: `engine/society_diffusion.py:465 __dict__[_foreign_institution_cache]`, `engine/society_diffusion.py:479 __dict__[_foreign_only_cache]`, `engine/society_diffusion.py:273 _diffusible_ids_cache`.
