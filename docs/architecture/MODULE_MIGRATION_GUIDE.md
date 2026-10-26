# How to move a topic out of `Sim` into a module

The rules every migration task follows. The design is `MODULE_REGISTRY_PLAN.md` section 4; the order and the
status are `MODULE_MIGRATION_TASKS.md`; the proposed views and commands per owner are in `catalogue/`. CLAUDE.md
applies throughout (names spelled out, short comments, a test calls one function).

## The shape of a module

- A package `sim/<module>/` with `__init__.py`, `api.py` (`WALL = "two-way"`, the only door), `module_spec.py`
  (its `MODULE_SPECS`; the engine finds it by that file), `rules.py` (the rules as plain functions of their inputs),
  the `Module` class, and `commands.py` for the commands it owns.
- It imports only `sim.assembly.api`, other packages' `api`, and the shared pure modules (`sim.world`,
  `sim.unit_conversions`, `sim.constants`, `sim.refusal`). Never `sim.engine`.
- A rule worth testing is a function in `rules.py` that takes plain values and returns plain values. The module's
  methods fetch inputs from views, call the rule, and send or apply the result.

## Reading what others own

- Every outside fact comes through `self.needs.<view>`: `view()` for a table, `view[key]` for a keyed view,
  `view(*arguments)` for a quote.
- Use the view names in `catalogue/<owner>.md`. If the owner has not moved yet, publish the view from the engine
  in `sim/engine/bridge_<your module>.py` with `@bridge_view` (never cached: legacy code writes the state behind
  it directly). When the owner moves, it publishes the same name and the bridge entry is deleted.
- A view's name and shape are set by its first publisher. Before adding one, look for it:
  `grep -rn "bridge_view(\"<name>\"\|ViewSpec(\"<name>\"" sim`. Reuse an existing view rather than adding a near
  copy with another name or shape; if the existing one does not answer your question, say so in your report.
- The scenario facts every module needs (the year, the civilisation, the tree, the acting seat) come from the
  `scenario` views; the acting seat is also `self.clock.acting_seat`.
- A raw state object you must still mutate in place (a purse, a ledger dict) is a `legacy_<name>` bridge view. These
  are debts: list them in your report; they go when that state moves.

## Changing what others own

- Send the owner's command (`self.needs.send(Command(...))`). If the owner has not moved yet, apply the command
  in your bridge file with `@bridge_command`, calling the engine exactly as the old code did.
- A command class lives with its owner: `sim/<owner>/commands.py`, exported by `sim/<owner>/api.py`, even while
  the owner has not moved (the package then holds only those two files, and the bridge applies the command).
- A command's handler returns its outcome: a value, or a `Refusal` with a cause. A refusal is a string and so is
  truthy: test `isinstance(answer, Refusal)`, never the answer's truth.
- Engine code not yet in a module sends with `sim.send(command)` and reads with `sim.view(name)`.

## Your own state

- Move the fields you own into your `world_state` / `seat_state` dataclasses and delete them from the old
  dataclass. Every reader of the old path changes to your view (grep `sim/`, `sim/ui/`, `sim/agents/`, `mods/`).
- When you delete a field from an old dataclass, check it is gone (`grep -n "<field>" sim/engine/state.py`): those
  files use tabs, and an edit that matched nothing leaves the field behind, which the equivalence check reports as an
  empty leaf on the current side.
- In the same commit, add a relocation to `sim/tests/equiv_fields.py` (`(current prefix, base prefix)`, `*` for a
  seat id) for each moved field, so the equivalence check still compares it.
- Write your state only inside your module, and bump the channel your views declare. A view is `cached=True` only
  when every write to everything it depends on happens inside its owners' commands; otherwise `cached=False` with
  a comment naming the outside writer.
- A method that reads but also writes (lazy creation, a trial value set and restored, a snapshot) is split: the
  creation moves to `setup()` or the fresh slot, the trial becomes a pure quote, the write becomes a command.

## Phases

Your year phases become `PhaseHook`s in your spec, and their entries in `sim/engine/year_phases.py` `SHIPPED`
become `module_seat_phase("<name>")` or `module_world_phase("<name>")`. Edit only your own lines there.

A step of yours that runs in the middle of another topic's phase (read something before the year's payments, act
after them) stays where it is as a view your module publishes plus a command it applies; split a phase only when
the whole step is yours. When you split a shared phase, keep the old name on the part a mod's `after:` most likely
meant, and name the new parts after their owners.

## Holders, hooks and points

- A command names who holds what by id: `None` for the acting seat's household, otherwise an actor id. Never put an
  object in a command.
- A rule that runs inside a free function of a walled package (a transfer hook, a listener) becomes an extension
  point of the owner: the owner installs the hook and posts what its providers answer as plain tuples
  (`sim/ledger/` `transfer_surcharge` is the example).

## The old mixin

- Its logic moves into the module. Methods still called from outside your topic become one-line forwarders (to a
  view or a command) in `sim/engine/forward_<module>.py`, listed in your report. A forwarder goes when its last
  caller moves.
- When the mixin is empty, delete it and its name in `Sim`'s base list in `sim/engine/core.py` (edit only that).

## Tests

- Tests that fake your mixins (`class X(YourMixin)`, `YourMixin.method(fake, ...)`) are rewritten in the same task:
  a rule is tested by calling the function in `rules.py`, the module by `sim.tests.module_harness.build` with plain
  values for its views. A test no longer imports `sim.engine` for code you moved.
- A test that builds a whole game stays as it is.

## Behaviour must not change

- Run the topics you touched (`python3 -m sim.tests --only a,b --topic-seconds 240`), then the micro equivalence
  check: `python3 -m sim.tests.equiv check docs/architecture/baseline/micro.json --tier micro --base-checkout
  /home/user/base-tool-wt`. On a divergence, find the cause; never accept one.
- Keep the arithmetic in the same order: a float sum in another order is a different game.
- A real bug you find is not fixed in the move. File a Complaint (next number, see `Complaints/README.md`), keep the
  behaviour, and name it in your report. The orchestrator decides whether a fix rides along (one rule with two
  drifted copies made one, like Complaint 681, is the usual exception).
- Never run the full suite, `--slow` or the full and long equivalence tiers; the orchestrator does.

## Report

Files moved and created, the views and commands (and which are bridged, with the `legacy_*` debts), state fields
moved with their relocations, forwarders left, tests rewritten, the topics and the equivalence check you ran with
their output, Complaints filed, and the commit SHA.
