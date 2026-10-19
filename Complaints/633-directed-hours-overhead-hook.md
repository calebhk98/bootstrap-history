# A mod cannot charge overhead against the directed-hours pool

**Status:** open

Mod `bh_orghierarchy_r4k8` (feature of `Complaints/closed/104`) works out the management layers a workforce needs
from a span-of-control rule and can hire the managers through the ordinary labour path. It cannot make that overhead
bind on the founder's own directed hours, because the contract has no way for mod code to add to the hours already
spoken for. Managers exist on the payroll, but the pool is unchanged.

## Evidence

* `sim/labour/labour_capacity.py:930` `director_hours_committed` totals teaching, relocation, supervision and wage
  hours, and every caller that works out free hours (`director_pool() - director_hours_committed()`, for example
  `sim/labour/labour_job.py:18`, `sim/labour/labour_wages.py:108`, `sim/ui/proto/dispatch_guidance.py:26`) reads that
  one function. A mod cannot add a term to it.
* `supervision_hours_this_year` (`sim/engine/state.py:82`) is read there and reset at `sim/engine/core_step_phases.py:413`
  but nothing writes it, so there is no existing field a mod could feed either, and mod code may not poke it.
* `sim/engine/mod_code.py` `ModCodeApi` offers commands, actor kinds, policies and spawners only. There is also no
  year-start or year-end hook for code, so even the hiring in `staff_managers` has to be run by hand (a data policy
  cannot name a code command when the mod's code is not allowed: `sim/ui/proto/mod_commands.py` `_check_references`).

## Why it matters

Without a way to charge the hours, a second mod with an organisational mechanism (a firm's layers, a state's civil
service, a guild) can only report its cost, not impose it. The rule "hours are consumed by management" is general to
every actor that directs work.

Proof of concept: branch `engine-director-overhead-hook`. It adds `ModCodeApi.director_overhead(function)`, a registry
`DIRECTOR_OVERHEADS` in `sim/engine/mod_code.py`, and `director_hours_committed` adds the sum of the registered
functions' hours (each called with the sim, negative results ignored) through a `director_overhead_hours` method on the
labour world port (`sim/engine/labour_port.py`). With no registration the sum is zero, so nothing changes. A regression
test in `sim/tests/` registers an overhead and checks the free hours fall by exactly that amount.
