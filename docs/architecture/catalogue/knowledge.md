# Module `knowledge`

What each seat knows and can see: techniques held, forgotten, revealed (fog), and the tree itself.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 3 / 3 |
| Old methods and properties owned (after regrouping) | 19 |
| Of those, referenced from another module's mixin code | 8 (7 classed read-only or pure by Appendix B, 1 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 16 (8 from mixins, 8 only from outside) |
| Views per used name | 0.19 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 3 |
| Views of other modules it reads | 4, from 2 modules |
| Commands of other modules it sends | 0 |

**Existing surface and files.** Engine: `FogMixin`, `done_in_order`, `Sim.has`, `starting_techs.py`, `tree_source.py`/`tree_merge.py` (the tree), `knowledge_warning.py`, `save_fog.py`. Complaint 508: 'knowledge and actor objectives'.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `Sim` | `sim/engine/core.py` | 1 | 1 |
| `EconomyMixin` | `sim/engine/economy.py` | 1 | 1 |
| `FogMixin` | `sim/engine/fog.py` | 10 | 4 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 14 | 4 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_free_prereq_hint`, `_hidden_prerequisite_kinds`, `prerequisite_label`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `KnowledgeSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.projects.done` | seat | <ui> 70, projects 18, <engine-functions> 15, materials 9, ventures 9, core 5, +13 more | seats 2, projects 1, polity 1, hazards 1, ventures 1 |
| `state.projects.done_year` | seat | diffusion 2, <ui> 2, seats 1, projects 1, markets 1, production 1 | seats 2, projects 2, <ui> 2, core 1 |
| `state.projects.forgotten` | seat | hazards 3, <ui> 3, projects 2 | - |
| `state.projects.granted` | seat | production 17, <ui> 16, <engine-functions> 9, prices 6, land 4, seats 2, +9 more | - |
| `state.projects.revealed` | seat | seats 1, <ui> 1, <engine-functions> 1 | <ui> 3, seats 1 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `techniques_held` | table | yes | Techniques the seat has finished (in tree order), when, which were granted at the start, which are forgotten. Replaces `projects.done` (the most-read project field: 70 UI reads, 18 projects, 12 materials) and the forwarding properties `done`, `granted`, `forgotten`, `done_year`. | `has`, `done_in_order`, `done_year` | `projects.done`, `projects.done_year`, `projects.granted`, `projects.forgotten` | `tree` | `done` | 24 |
| `visibility` | keyed | yes | Whether a node is visible to the seat, which prerequisites are hidden, the labels and hints, and whether to keep walking toward the goal. | `is_visible`, `fog_scrub`, `fuzzy_estimates`, `prerequisite_label`, `missing_prereq_message`, `_hidden_prerequisite_kinds`, `_free_prereq_hint`, `fog_summary`, `never_abandon`, `on_road_to_goal`, `fog` | `projects.revealed` | `techniques_held`, `seats.goal` | `done`, `revealed` | 10 |
| `tree` | keyed | no | The tech tree: node data by id, as built from `data/branches/` and re-derived when society's techniques change. Replaces `self.nodes`, read in 99 files (263 sites in sim/engine alone: `grep -rnE '(self/sim)\.nodes\b' sim/engine --include=*.py / wc -l`). | - | - | - | `tree` | 1 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `tree`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 8 methods are referenced from other modules' mixin code: 7 are replaced by a view here, 1 by a command. 8 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 16 used names, 12 are covered by a view or command through the method itself, 4 through a field alias, 0 are year-phase hooks and 0 are package handle members.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `LearnTechnique` | seat, node, year, via | `projects.done.add`, `done_year[...] =`, `_done_changed()`. | `sim/engine/projects_completion.py:203,210`, `sim/engine/core.py:1824,1828`, `sim/engine/projects_staffing.py:752`, `sim/engine/starting_techs.py:18`, `sim/agents/household_party.py:106,112` | `already_known`, `unknown_node` | `projects.done`, `projects.done_year`, `projects.granted` |
| `ForgetTechnique` | seat, node, cause | Loss by hazards and by completion rules. | `sim/engine/society_hazards.py:607`, `sim/engine/core_step_phases.py:515,589` | `not_known` | `projects.forgotten` |
| `RevealNodes` | seat, nodes, cause | `reveal_from`, hearing of other seats. Methods: `reveal_from` | `sim/engine/fog.py (reveal_from)`, `sim/engine/seat_sight.py` | none: always applies | `projects.revealed` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `projects.done`: 9 sites: `sim/agents/household.py:353`, `sim/engine/society_hazards.py:607` (.discard()), `sim/engine/core_step_phases.py:589` (.discard()), `sim/engine/core_step_phases.py:515` (.discard()), `sim/engine/core.py:1824` (.add()), `sim/engine/seat_handover.py:46`, `sim/engine/projects_staffing.py:752` (.add()), `sim/engine/starting_techs.py:18` (.add()), `sim/engine/projects_completion.py:203` (.add())
- `projects.done_year`: 11 sites: `sim/ui/cli_interactive.py:256` (assign (alias)), `sim/ui/cli_economy_check.py:43` (assign (alias)), `sim/ui/cli_agent.py:66` (assign (alias)), `sim/ui/cli_economy_accounts.py:56` (assign (alias)), `sim/engine/core.py:1834`, `sim/engine/core.py:1828`, `sim/engine/core.py:1827`, `sim/engine/baseline_game.py:31` (assign (alias)), `sim/engine/opening_checks_run.py:76` (assign (alias)), `sim/engine/projects_completion.py:210` and 1 more
- `projects.granted`: 2 sites: `sim/engine/seat_handover.py:47`, `sim/engine/starting_techs.py:20` (.add())
- `projects.revealed`: 6 sites: `sim/ui/replay.py:57` (assign (alias)), `sim/ui/cli_interactive.py:264` (assign (alias)), `sim/ui/cli_agent.py:70` (assign (alias)), `sim/agents/household.py:408`, `sim/engine/core_properties.py:446`, `sim/engine/saveload.py:372`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `projects`: `projects.active_projects` (projects.active); `projects.running_gates` (relied_on_running); `projects.start_check` (start_reason)
- `seats`: `seats.goal` (input of knowledge.visibility)

Sends: none.

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- none of its own; `LearnTechnique` is sent from project completion and hazards

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 219 | `done`, `fog`, `is_visible`, `granted`, `fuzzy_estimates`, `done_year`, `has`, `revealed` |
| engine/(function modules) | 20 | `done`, `granted`, `done_year`, `never_abandon`, `has`, `fog`, `is_visible` |
| mods | 5 | `done`, `has` |
| engine/saveload* | 4 | `fog`, `fuzzy_estimates` |
| engine/save* | 1 | `done` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `done` 75 reads, `fog` 64, `is_visible` 29, `granted` 17, `fuzzy_estimates` 7, `done_year` 6, `has` 6, `revealed` 5; `saveload` writes `fog` and `fuzzy_estimates`; mods: `done`, `has`.

## (h) Hard spots and caches

- The done set is invalidated by hand at twelve places (`economy.py:293-299` comment); every write becomes `LearnTechnique`/`ForgetTechnique` which bumps the `done` channel, which is the point of the module.
- Sums over `done` must go in tree order (`done_in_order`); this view fixes that order once.
- The tree is shared static data that `refresh_derived_nodes` mutates (production); it needs a version, or the mutation must become a command here.
- Fog is a mode of the game (`_fog`), per game, not per seat; `fuzzy_estimates` too.

Caches and version counters held today (feed for task 1.2):

- `household._done_seq` (`economy.py:221`), `done_version`
- `_diffusible_ids_cache` is diffusion's, keyed by the done set
