# Module `diffusion`

How knowledge spreads: literacy and schooling, what a finished technique does to the society, how far each category of knowledge has
spread, which techniques concerns have had time to copy, and what a seat does with an invention (secret, licence, publication).

**Status:** moved, on branch `mr/diffusion` (package `sim/diffusion/`, bridge `sim/engine/bridge_diffusion.py`, forwarders
`sim/engine/forward_diffusion.py`). The draft of task 1.5 (a read-only analysis of `e8b004c`) is kept below as corrected by the move;
"What the move changed in this draft" lists each correction.

## What the move changed in this draft

- **More views than the draft's five** (count them with the command under "Views published"). The draft folded every reader of a number into one view per topic; the readers ask different questions with
  different arguments, so they are separate views (table below). Several old methods stand behind one view where they are one question
  (`diffusion_index` is keyed by kind and answers the venture index, the three category averages and the military share; the three
  ceilings are `literacy_ceiling[field]`). The three views the project-starting bridge had published for this topic (`needs_first`,
  `foreign_only`, `civ_cost_factor`) moved here with their names and shapes unchanged, and their entries left `bridge_projects.py`.
- **Five commands, not four.** `AdvanceSociety` (sent from the middle of the `money_world` phase, which is not wholly this module's),
  `ApplyTechEffects`, `Disclose` (the old `disclose`, which runs `_license` inside), `NoteFirstRuns` (new: the write split out of
  `techniques_spread`) and `RekeyDisclosures` (new: a seat handover renames seat ids inside another seat's licences). `SetLiteracy` is
  gone: nothing called `set_literacy`, so it was dropped.
- **State: more than the one field.** `projects.disclosures` is `DiffusionSeat.disclosures`. `economy.technique_first_run`,
  `economy.technique_record_started` and `scenario._literacy_said` are `DiffusionWorld`; relocations are in
  `sim/tests/equiv_fields.py`. Literacy itself is not a field of this module: the reading shares live in the strata of the actors'
  cast (`CountryLiteracy`), which actors still owns, so the module mutates them through the `legacy_country_literacy` bridge view.
- **`techniques_spread` was the read that wrote.** It stamped the year each technique was first seen running on the first read after a
  change. It is now a command (`NoteFirstRuns(in_use)`, which stamps) and a view (`techniques_spread`, which does not). The one
  engine reader (`Sim.techniques_spread`, a forwarder) sends the command and then reads, so the order is the old one; the old method
  left `techniques_in_use.py`. A module that reads the view alone gets the record as stamped so far.
- **Staff advice moved with `AdoptionMixin`.** `staff_hire_advice` and `STAFF_SOURCES` are in this file's mixin; they are
  `staff_hire_advice` and `staff_sources`. They are not `staff_advice`: that name is workforce's (the hire advice sized to a shortfall,
  published by `bridge_projects.py`).
- **Dead code dropped:** `_is_foreign_institution` and its cache (nothing called it), `medical_compliance` on the game (only the rule
  function of the same name is used), `set_literacy`, `literacy_ceiling_common` as a method (it is `literacy_ceiling["common"]`).
- **`value_weights` and `reputation` stay with their owners.** A tech effect shifts a society value weight and publishing raises the
  seat's reputation; both are commands to the owner (`ShiftValueWeight`, `GainReputation`, in `sim/polity/`) applied by the bridge.
  Nobody owns `value_weights` yet (the draft assigned it to no module); `polity` is the nearest, and the bridge holds the floor and
  ceiling constants (`sim/engine/value_weight.py`) with the shift.
- **A seat handover moves the module's seat state with the seat.** Seat slots live in `seat.modules`, so a handover that moved
  `household`, `projects` and the rest left a leaver's disclosures (and, since the reporting move, its log) behind. `modules` is now one
  of the moved seat fields (`sim/engine/seat_handover.py`), and the modules' seat binding is redone after a move.
- **Reads are counted by view, not by module**, so there are many more names than the draft's; most are one-line bridge entries.

## Mixin classes and files absorbed

| Old class | Old file | Now |
|---|---|---|
| `AdoptionMixin` | `sim/engine/society_adoption.py` | `sim/diffusion/literacy.py` (`Literacy`), `tech_effects.py` (`TechEffects`), `trades.py` (`TradeAbsorption`), `module.py` (staff advice, `advance_society`) |
| `DiffusionMixin` | `sim/engine/society_diffusion.py` | `sim/diffusion/spread.py` (`Spread`), `relief.py` (`Relief`), `foreign.py` (`Foreign`) |
| `DisclosureMixin` | `sim/engine/society_disclosure.py` | `sim/diffusion/disclosure.py` (`Disclosure`) |
| `ActorsMixin` (4 literacy methods) | `sim/engine/society_actors.py` | `Literacy`; the strata lookup is `legacy_country_literacy` in the bridge |
| `TechniquesInUseMixin.techniques_spread` | `sim/engine/techniques_in_use.py` | `sim/diffusion/techniques.py` (`Techniques`) |

The plain modules moved into `sim/diffusion/`: `adoption_share`, `civ_cost`, `diffusion_curve`, `diffusion_rules`,
`institution_societies`, `technique_spread`, `trade_absorption`, and `literacy_rules` (which absorbed `literacy_effect`,
`literacy_census_phrase` and the schooling-flow functions of `public_works_rules`). The rules written for the move are `rules.py`
(staff advice, categories and their pace, the report, tech-effect texts, disclosure); the declared numbers are `constants.py`.
`copy_difficulty_of` left `visibility.py`. `category_traits.py` is knowledge's (fog, staffing and production read it too) and
reaches the module as the `diffusion_traits` view. `knowledge_warning.py` is knowledge's, not this module's.

## State owned

`DiffusionWorld`: `technique_first_run` (node to the year some producer was first seen running it), `technique_record_started`
(whether the opening's techniques have been stamped), `literacy_said` (the last year a census line was logged).
`DiffusionSeat`: `disclosures` (node to `{mode, published_year, licensees}`).

## Views published

Count them with `python3 -c "import sys; sys.path.insert(0,'.'); from sim.diffusion.module_spec import MODULE_SPECS as m; print(len(m[0].publishes), len(m[0].applies))"`.

None is cached: they read the legacy strata, the tree's live mechanics, the held techniques and the government's knowledge, which code
outside the module still writes. The disclosure views hand out the live record.

| View | Kind | Answers |
|---|---|---|
| `literacy` | quote (field, country) | a reading share of a country (home when none) |
| `research_productivity` | quote (country) | the lettered share over its reference, capped |
| `literacy_ceiling` | keyed (`literacy_general`, `literacy_elite`, `common`) | what the share can reach |
| `schooling_flow`, `effective_schooling_flow` | quote (field) | the open schools' flow, and with diffused printing counted |
| `literacy_next_year` | table | the next schooling year's shares, no stratum changed |
| `diffusion_share` | keyed (node) | how much of a running venture's edge has leaked |
| `knowledge_half_life_years` | quote (country) | years for half of those who could copy a technique to have done so |
| `diffusion_index` | keyed (`venture`, `food`, `medical`, `information`, `military`) | how widely it has spread |
| `civ_diffusion` | keyed (node) | the share of the society that has adopted a built node |
| `diffusible_ids` | keyed (category) | the nodes of a diffusing category |
| `diffusion_report` | table | None until something spreads, then the figures the `state` screen shows |
| `diffusion_relief` | quote (`medical`, or `military` and per-weapon share) | what diffusion takes off a harm |
| `foreign_only`, `needs_first`, `civ_cost_factor` | quotes | what is another society's, what a society needs first, what it finds dear |
| `disclosure` | keyed (node), seat | the seat's choice for an invention |
| `disclosures` | keyed (seat id) | everything a seat chose (any seat, not only the acting one) |
| `disclosure_listing`, `licensable_actor_ids` | tables, seat | the listing the `disclose` screen shows, and who may be licensed |
| `copy_difficulty` | keyed (node) | how hard the know-how is to copy from sight |
| `staff_hire_advice`, `staff_sources` | quote, table | the hire command for a shortfall, and where to hire a trade from |
| `techniques_spread` | table, seat | the techniques in use concerns have had time to copy |

## Commands applied

| Command | Fields | Answer |
|---|---|---|
| `AdvanceSociety` | year | none |
| `ApplyTechEffects` | node_id | none |
| `Disclose` | node_id, mode, licensee, fee, royalty | `{ok, note}` or `{ok: False, error[, cause, facts]}` |
| `NoteFirstRuns` | in_use (a frozenset) | none |
| `RekeyDisclosures` | seat, from_id, to_id | none |

## Commands sent to other owners (the owner's package holds the class; the engine bridge applies it until the owner moves)

| Command | Package | What the bridge does |
|---|---|---|
| `ShiftValueWeight(field, delta)` | `sim/polity/` | shifts a society value weight within its floor and ceiling; answers (before, after) or a `not_a_value_weight` refusal |
| `GainReputation(amount)` | `sim/polity/` | the acting household's reputation rises, capped at the scale's top |
| `SetEmployed(trade, headcount)` | `sim/workforce/` | `labour.set_employed`, then `labour.resync_pools` |
| `NoteTradeSpread(trade, introduced_year, endemic)` | `sim/workforce/` | records the year a taught trade was first seen and marks it endemic |
| `RecordEvent` | `sim/reporting/` | the log lines (`society_changed`, `school_progress`, `trade_no_longer_only_yours`) |

## Reads (views of owners that have not moved, published by `bridge_diffusion.py` unless noted)

| Owner | Views |
|---|---|
| actors | `legacy_country_literacy` (raw strata, mutated in place: a debt), `state_knowledge`, `seat_party`; `legacy_actor_registry` (ledger's bridge) and `legacy_agent_world` (coin's) |
| seats | `seat_list`, `seat_holders`, `built_by_any_seat`, `earliest_done_year` |
| knowledge and projects | `tree` (shared), `tree_nodes`, `techniques_held` (projects' bridge), `techniques_granted`, `done_year`, `venture_opened_year`, `tech_effects`, `operating` and `civilisation` (living stock's bridge), `running` (projects') |
| production | `techniques_in_use` |
| mechanics | `effect_terms`, `effect_values`, `corpus_diffusion_pace`, `school_node` (named and shaped as the mechanics module publishes them; delete these entries when it merges), `diffusion_traits` (the category catalogue, knowledge's) |
| workforce | `literacy_references`, `literacy_capacity` (keyed by trade), `farm_share_of_hours`, `trade_spread`, `staff` (shared) |
| disease and the state | `coverage`, `disease_burden`, `disease_burden_held`, `disease_burden_weights`, `state_reach` |
| living stock | `stock_holds_met` (published by the module) |
| polity | `reputation_gain_of` (a quote of what finishing a node adds) |

## Year phases

None. `advance_society` runs in the middle of `money_world`, after the demographic recovery and before the actors' year, so it is the
command `AdvanceSociety` sent from there (`step_phase_money.py` through the forwarder). It becomes a phase of its own when
`money_world` is split.

## Forwarders left in `Sim` (`sim/engine/forward_diffusion.py`)

`country_literacy`, `literacy`, `research_productivity` (labour, the agents' port, the opening), `literacy_ceiling_general`,
`literacy_ceiling_elite`, `_schooling_flow`, `effective_schooling_flow`, `literacy_next_year` (the screens), `advance_society`,
`apply_tech_effects` (project completion), `staff_hire_advice`, `STAFF_SOURCES` (the labour port, staffing), `diffusion_share`,
`diffusion_index`, `information_diffusion_index`, `state_military_diffusion`, `knowledge_half_life_years`, `civ_diffusion`,
`_diffusible_ids`, `medical_diffusion_relief`, `_state_military_diffusion_relief` (hazard relief, the disease port, the agents' port),
`world_diffusion_report`, `_is_foreign_only` (the planner), `needs_first` (the civilisation start check), `civ_cost_factor`,
`disclosure_of`, `copy_difficulty`, `disclose`, `licensable_actor_ids`, `disclosure_listing`, `techniques_spread`; and the numbers
other topics read off the game: `STATE_MIL_RELIEF_PER_WEAPON_OUTPUT`, `STATE_MIL_RELIEF_PER_WEAPON_SACK`, `VALUE_WEIGHT_FLOOR`,
`VALUE_WEIGHT_CEILING`.

## Hard spots

- **The year step is the same arithmetic in the same order**: schooling moves elite then general literacy, each with its own flow,
  then trades are absorbed in sorted order; the micro equivalence tier and a baseline game were identical to the base.
- **`techniques_spread` keeps its memo inside the module** (the techniques in use by identity, the year, what is granted, the size of
  the record): the market asks for it once per concern per year. `note_first_runs` skips when the same set was stamped this year.
- **`needs_first` and `foreign_only`** are read by project starting on every unbuilt node every year; `foreign_only` keeps its
  answers for the life of the game (they depend on the civilisation and the node's name alone).
- **Seat handover.** The module's seat slot moves with the seat (`MOVED_FIELDS` has `modules`), the replacement's own disclosures
  count as something it would lose, and the ids in every seat's licences are renamed by `RekeyDisclosures`.
- **`apply_tech_effects` iterates the effects table in file order**; the disease branch asks the burden and its weights as views and
  reads a node's held share only when the node is one of the burden's technologies, as the old code did.
