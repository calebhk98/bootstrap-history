# Module `mechanics`

What the tree's effects add up to: an index over tech-tree mechanics and effect lookups.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 5 / 0 |
| Old methods and properties owned (after regrouping) | 32 |
| Of those, referenced from another module's mixin code | 24 (24 classed read-only or pure by Appendix B, 0 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 26 (24 from mixins, 2 only from outside) |
| Views per used name | 0.19 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 5 |
| Views of other modules it reads | 7, from 4 modules |
| Commands of other modules it sends | 0 |

**Existing surface and files.** Engine only: `MechanicsMixin` (33 methods; 115 inbound references, all reads). Function modules `corpus_hedge`-style helpers in `hazard_hedge_timing.py`, `hedge_steps.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `MechanicsMixin` | `sim/engine/mechanics.py` | 32 | 24 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `LABOUR_PRODUCTIVITY_SOURCES`, `ROOM_SOURCES`, `_capability_sets`, `_mechanics_index`, `corpus_nodes_best_first`, `dispersed_corpus_running`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| none: this module owns derived values only, no stored field | | | |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `mechanic` | keyed | no | Nodes carrying a mechanic and the effect terms of a node. | `mechanic`, `nodes_with_mechanic`, `_effect_terms`, `_mechanics_index`, `_capability_sets` | - | `knowledge.tree` | `tree` | 17 |
| `effect` | quote | yes | The value, sum, factor, best or truth of an effect for the techniques held and running. | `effect_value`, `effect_values`, `effect_sum`, `effect_factor`, `effect_best`, `effect_holds` | - | `knowledge.techniques_held`, `production.running` | `done`, `operating` | 12 |
| `capability_sets` | table | no | Named sets: capability institutions, scalable institutions, staff-capacity, room and labour-productivity sources, hazard counters, disease burden tech ids. | `CAPABILITY_INSTITUTIONS`, `SCALABLE_INSTITUTIONS`, `NOT_OPERATING_BENEFIT`, `STAFF_CAPACITY_SOURCES`, `ROOM_SOURCES`, `LABOUR_PRODUCTIVITY_SOURCES`, `HAZARD_COUNTERS`, `DISEASE_BURDEN_TECH_IDS` | - | `knowledge.tree` | `tree` | 8 |
| `corpus` | quote | yes | Corpus nodes best first, hedge tiers, whether the corpus is dispersed, nodes that can be lost. | `best_corpus_node`, `corpus_nodes_best_first`, `corpus_hedge_tiers`, `corpus_is_dispersed`, `dispersed_corpus_running`, `losable_node_ids`, `corpus_diffusion_pace` | - | `knowledge.techniques_held`, `production.running` | `done` | 4 |
| `patronage` | quote | yes | Approval patron, school node, patrons lost to eminence, deputies and the founder's age. | `approval_patron`, `school_node`, `patrons_lost_to_eminence`, `deputies_carry_the_work`, `deputy_hours`, `founder_age` | - | `knowledge.techniques_held`, `seats.founder` | `done` | 6 |

**Coverage.** 24 methods are referenced from other modules' mixin code: 24 are replaced by a view here, 0 by a command. 2 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 26 used names, 26 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

## (d) Commands

None: this module owns no state that others change; it only publishes views.

## (e) Reads and sends

Reads (views of other modules), by provider:

- `knowledge`: `knowledge.techniques_held` (has, input of mechanics.corpus, input of mechanics.effect, input of mechanics.patronage ...); `knowledge.tree` (input of mechanics.capability_sets, input of mechanics.mechanic)
- `production`: `production.institution_units` (institution_units); `production.running` (input of mechanics.corpus, input of mechanics.effect, running)
- `seats`: `seats.founder` (input of mechanics.patronage)
- `workforce`: `workforce.labour_market` (labour.money_per_labour_hour); `workforce.staff` (household.directors_extra, labour)

Sends: none.

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- none of its own

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 19 | `CAPABILITY_INSTITUTIONS`, `deputy_hours`, `deputies_carry_the_work`, `SCALABLE_INSTITUTIONS`, `STAFF_CAPACITY_SOURCES`, `founder_age`, `effect_holds`, `effect_value` |
| engine/(function modules) | 4 | `mechanic`, `CAPABILITY_INSTITUTIONS`, `corpus_hedge_tiers` |
| engine/agents_port* | 2 | `nodes_with_mechanic` |
| agents | 1 | `nodes_with_mechanic` |
| engine/economy_port* | 1 | `nodes_with_mechanic` |
| engine/ui* | 1 | `_effect_terms` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `CAPABILITY_INSTITUTIONS` 9, `deputy_hours` 3, `deputies_carry_the_work` 2; agents_port: `nodes_with_mechanic` 3; economy_port 1.

## (h) Hard spots and caches

- `running_with_mechanic` reads production's `running`; with production also reading mechanics, the two would read each other. It moves to production (derived from `mechanic` and `running`), leaving mechanics reading only knowledge.
- `_mechanics_index` is built once from the tree (`__dict__['_mechanics_index_cache']`, `mechanics.py:36`) and must be rebuilt when `RederiveNodes` changes the tree.
- Class constants (`CAPABILITY_INSTITUTIONS`, `HAZARD_COUNTERS`) are content data read as names; they become the `capability_sets` table.

Caches and version counters held today (feed for task 1.2):

- `__dict__['_mechanics_index_cache']` (`mechanics.py:36`)

Detected by the cache scan in this module's mixin files: `engine/mechanics.py:36 __dict__[_mechanics_index_cache]`.
