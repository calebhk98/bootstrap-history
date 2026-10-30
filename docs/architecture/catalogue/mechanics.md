# Module `mechanics`

What the tree's effects add up to: an index over tech-tree mechanics and effect lookups.

**Status:** moved (branch `mr/mechanics`). The package is `sim/mechanics/`; this file now describes what shipped, not
the draft proposal. Counts come from the module spec
(`python3 -c "import sys; sys.path.insert(0,'.'); from sim.mechanics.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies))"`).

## What changed from the draft

- **Views:** 22 instead of 5. The draft merged by topic (`effect` for six old methods, `corpus` for seven, `patronage` for
  six). A caller asks one question, and the six effect methods differ in arithmetic (a sum, a product, a maximum, a
  grouped list), so each is a view: `effect_sum`, `effect_factor`, `effect_best`, `effect_values`, `effects_in_force`,
  with `effect_holds` and `effect_value` for the callers that still walk terms themselves, and `effect_terms` for the
  declared order. `mechanic` is keyed by mechanic name and answers `{node: parameters}`, which covers `mechanic`,
  `nodes_with_mechanic` and the index; the draft's `mechanic` mixed that with effect terms.
- **Names kept:** `running_mechanics`, `effects_in_force` (both first published by the living-stock bridge) and
  `approval_patron` (the projects bridge) keep their name and shape; the three bridge entries are deleted and the readers
  (defence stores, projects) did not change.
- **Not mechanics:** `deputy_hours`, `deputies_carry_the_work`, `founder_age` read the household, the scenario and the
  config, and `losable_node_ids` reads the techniques held and granted. None reads a mechanic except
  `losable_node_ids` (corpus dispersal, through `corpus_dispersed`). They stay as plain methods in
  `sim/engine/forward_mechanics.py` until `seats` and `knowledge` exist; the draft's `patronage` view is dropped for that
  reason (`approval_patron`, `school_node` and `patrons_lost_to_eminence` are separate views).
- **Dropped:** `dispersed_corpus_running`, `corpus_nodes_best_first` as a method (it is the view `corpus_nodes`), and
  `_mechanics_index`, `_capability_sets`. `dispersed_corpus_running` had no caller (`grep -rn dispersed_corpus_running sim`).
- **`running_with_mechanic` stays here**, not in production as the draft proposed: it is `running_mechanics` read for
  names, and mechanics reads only the `running` view of production, so the two do not read each other.
- **Class constants:** `CAPABILITY_INSTITUTIONS`, `SCALABLE_INSTITUTIONS` and `NOT_OPERATING_BENEFIT` are one view,
  `capability_sets`. The other sets stay one view each (`staff_capacity_sources`, `room_sources`,
  `labour_productivity_sources`); the draft's single `capability_sets` table of eight different shapes would have made
  every caller unpack by name. `DISEASE_BURDEN_TECH_IDS` is `mechanic["disease_burden"]` and has no view of its own.
- **`HAZARD_COUNTERS`:** the module answers the node rows (`hazard_counter_rows`); the two own-mine counters are not
  nodes and their shares are declared with the hazards, so the engine forwarder merges them in
  (`rules.hazard_counters`) in the order the old property produced.
- **No state, no commands, no relocations.** As drafted. The index cache is private to the module and keyed on the tree
  object, as before; every view is `cached=False` because the engine replaces the tree (re-derivation) and writes what is
  running outside any command.

## (a) Mixin classes and files absorbed

`MechanicsMixin` (`sim/engine/mechanics.py`, deleted). Its module-level helpers `nodes_declaring` and
`staff_capacity_sources` are in `sim/mechanics/rules.py`, reached through `sim.mechanics.api`.

## (b) State owned

None.

## (c) Views

All uncached. Quotes unless noted. `seat` means seat scoped (the answer depends on what the acting seat holds or runs).

| View | Kind | Seat | Answers |
|---|---|---|---|
| `mechanic` | keyed by name | no | `{node: parameters}` of the nodes declaring it, in id order |
| `running_mechanics` | quote | yes | `[(node, parameters)]` of the running ones |
| `capability_sets` | table | no | (capability ids, scalable ids, `{id: lost benefit}`) |
| `staff_capacity_sources`, `room_sources`, `labour_productivity_sources`, `hazard_counter_rows` | table | no | the tuples the labour and hazards code walks |
| `effect_terms` | quote | no | `[(node, spec)]` declaring a channel, in (order, id) sequence |
| `effects_in_force`, `effect_values`, `effect_sum`, `effect_factor`, `effect_best`, `effect_holds`, `effect_value` | quote | yes | the effect arithmetic, gated by held or running |
| `corpus_nodes`, `corpus_hedge_tiers`, `corpus_dispersed`, `corpus_diffusion_pace` | table / quote | pace only | the corpus hedge against a sacking |
| `approval_patron`, `school_node`, `patrons_lost_to_eminence` | quote / table | no | patrons and schooling |

## (d) Commands

None.

## (e) Reads

All through the bridge until their owners move: `tree_nodes` (the whole tree; new, in `bridge_shared.py`, because the
keyed `tree` cannot be enumerated), `techniques_held`, `running`, `institution_units`, `money_per_labour_hour`. No
`legacy_*` view.

## (f) Year phases

None.

## (g) Forwarders left

`sim/engine/forward_mechanics.py` (`ForwardMechanicsMixin`): `mechanic`, `nodes_with_mechanic`, `running_with_mechanic`,
`_effect_terms`, `effect_holds`, `effect_value`, `effect_values`, `effect_sum`, `effect_factor`, `effect_best`,
`approval_patron`, `school_node`, `patrons_lost_to_eminence`, `corpus_hedge_tiers`, `corpus_is_dispersed`,
`corpus_diffusion_pace`, `best_corpus_node`, and the properties `CAPABILITY_INSTITUTIONS`, `SCALABLE_INSTITUTIONS`,
`NOT_OPERATING_BENEFIT`, `DISEASE_BURDEN_TECH_IDS`, `STAFF_CAPACITY_SOURCES`, `ROOM_SOURCES`,
`LABOUR_PRODUCTIVITY_SOURCES`, `HAZARD_COUNTERS`. The unmoved callers are listed by
`grep -rn "\.mechanic(\|nodes_with_mechanic\|effect_sum" sim --include=*.py`.

## (h) Hard spots

- `HAZARD_COUNTERS` needs two heuristics declared in `projects_completion.py` (`HAZARD_EROSION_OWN_GOLD`,
  `HAZARD_EROSION_OWN_SILVER`); they leave with the hazards.
- The tree is replaced by a re-derivation (`node_rederive.py`); the module rebuilds its index when the object it reads
  is not the one it indexed.
