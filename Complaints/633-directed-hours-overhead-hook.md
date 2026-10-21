# A mod cannot charge overhead against the directed-hours pool

**Status:** open

**What is wrong.** Mod `bh_orghierarchy_r4k8` (feature of `Complaints/closed/104`) works out the management layers a
workforce needs from a span-of-control rule and hires the managers through the ordinary labour path. It cannot make that
overhead bind on the founder's own directed hours: the contract has no way for mod code to add to the hours already
spoken for. Managers exist on the payroll, but the pool is unchanged.

**Evidence.**

- `director_hours_committed` (`sim/labour/labour_capacity.py`) totals teaching, relocation, supervision and wage hours.
  Every caller that works out free hours (`director_pool() - director_hours_committed()`: `labour_job.py`,
  `labour_wages.py`, `labour_training.py`, `sim/ui/proto/guidance.py`, `sim/ui/cli_interactive.py`) reads that one
  function. A mod cannot add a term to it. Find the callers with `grep -rn "director_hours_committed" sim`.
- `supervision_hours_this_year` (`sim/engine/state.py`) is read in `director_hours_committed` and reset in
  `sim/engine/core_step_phases.py`, but nothing writes it, so there is no existing field a mod could feed, and mod
  code may not poke it. `ModEffects` (`sim/engine/mod_effects.py`) has no effect that spends hours.
- A mod can now run `staff_managers` every year from a phase (`ModCodeApi.phase`, `sim/engine/mod_code.py`), so the
  missing year-start hook is no longer the gap; the missing pool term is. Whether the mod uses a phase yet is not checked.

**Why it matters.** The rule "hours are consumed by management" is general to every actor that directs work (a firm's
layers, a state's civil service, a guild). Without a way to charge the hours, a mod can only report the cost, not impose it.

**What it would take.** `ModCodeApi.director_overhead(function)` and a registry of functions that
`director_hours_committed` sums (each called with the sim, negative results ignored), reached through the labour world
port (`sim/engine/labour_port.py`). With no registration the sum is zero, so nothing changes. A regression test
registers an overhead and checks the free hours fall by exactly that amount.

**Tried.** A proof of concept on branch `engine-director-overhead-hook` (not in main) did exactly this; it was never merged.
