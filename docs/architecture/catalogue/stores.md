# Module `stores`

Mod-declared key/value stores (`state.stores`).

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 1 / 1 |
| Old methods and properties owned (after regrouping) | 1 |
| Of those, referenced from another module's mixin code | 1 (1 classed read-only or pure by Appendix B, 0 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 3 (1 from mixins, 0 only from outside) |
| Views per used name | 0.33 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 1 |
| Views of other modules it reads | 0, from 0 modules |
| Commands of other modules it sends | 0 |

**Existing surface and files.** Existing: `sim/engine/mod_stores.py` (one property), `mod_effects.py` (write a store). Candidate to fold into the assembly itself rather than be a module.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `ModStoresMixin` | `sim/engine/mod_stores.py` | 1 | 1 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): none.

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
| `store` | keyed | no | The value in a declared store for a tile, actor or actor pair (default if none was written). | `stores`, `stores.view` | - | - | `stores` | 7 |

**Coverage.** 1 methods are referenced from other modules' mixin code: 1 are replaced by a view here, 0 by a command. 0 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 3 used names, 1 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 2 are package handle members.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `WriteStore` | store, key, value | `mod_effects` write a store. Methods: `stores.write` | `sim/engine/mod_effects.py`, `sim/engine/mod_stores.py` | `undeclared_store` | - |

## (e) Reads and sends

Reads: none.

Sends: none.

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- none

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 8 | `stores` |
| engine/mod* | 2 | `stores` |
| agents | 1 | `stores` |
| engine/(function modules) | 1 | `stores` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `stores` 8; land 3; campaigns 1; agents 1; mod code.

## (h) Hard spots and caches

- Declared by mods, not by the shipped data; its state is the generic slot `SimulationState.stores` that assembly already carries, so this is the one module that is really a framework service.
