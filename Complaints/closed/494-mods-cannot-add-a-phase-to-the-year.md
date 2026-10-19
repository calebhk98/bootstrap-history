# Mods cannot add a step to the year: the phase order is a fixed list in code

**Status:** closed - phase registry in `sim/engine/year_phases.py`; `api.phase` in `ModCodeApi`

`run_year` (`sim/engine/year_run.py`) calls each phase by name in a fixed order. A mod can register
commands, actor kinds, policies and spawners (`sim/engine/mod_code.py`); a policy runs at the start or end
of the year and a spawner after the actors' turns. Nothing lets a mod run a step between two engine phases,
for example a conflict step after the market closes, a magic step before harvest, or a politics step
before the money phase.

Why it matters: every system the alt-history review asked for (Complaints 481 to 493) and the systems
the next groups will ask for (a fantasy world with magic and other creatures) need their own step in the
year. CLAUDE.md asks for dynamic over enumerated; the year is the largest enumerated list left.

What it would take: a phase registry: each phase a named entry with "after" and "before" constraints, run
once for the world or once per seat; the shipped phases registered the same way; `api.phase` in
`ModCodeApi`; a load error naming both mods when constraints form a cycle. The fingerprint
(`python3 -m sim.tests.fingerprint`) proves the shipped order unchanged.

## Resolution

`run_year` now iterates a registry (`sim/engine/year_phases.py`): the shipped phases are entries of the same
kind as mod phases, each with a scope (world or seat) and optional `after` and `before` constraints. A mod adds
one with `api.phase`; unknown names, cycles and unsatisfiable constraints are load errors naming the mod and
phase. With no mod the order is the shipped list, unchanged. Held by `sim/tests/test_year_phases.py`; how to
use it is in `mods/README.md`.
