# Multiple parallel models exist for related concepts; define which is authoritative

**Source:** playtest findings document, ARCH-001. **Status:** Architecture
recommendation, largely already answered by an existing document; this
complaint's job is to say so precisely, per CLAUDE.md's own request, rather
than duplicate the answer.

## The player's reasoning

The repository contains rich standalone modules (`sim/world/demand.py`,
`sim/world/labour_market.py`, `sim/world/deposits.py`) while the live engine
has separate labour, demand/revenue and mining paths of its own. Standalone
modules are useful for development, but duplicate concepts drift. Their
recommendation: for each domain, document the authoritative live model, the
experimental/reference model, the intended migration path and the
invariants shared between them; then either wire the standalone model in,
deliberately keep it as a research module, or retire it.

## What already exists, checked directly

This exact question is already answered, per-module, in `docs/architecture/
STATE_OF_THE_PROJECT.md` (Part 2's import table and Part 3's per-module
write-up), and the answer is current as of the same day this review was
done:

    agriculture.py         imported by sim/engine/core.py
    demography.py          imported by sim/engine/core.py
    land.py                 imported by sim/engine/core.py
    transport.py            imported by sim/engine/economy.py (as freight_physics)
    military_logistics.py   imported by sim/engine/society.py
    deposits.py             imported ONLY by sim/solve_prices.py (a standalone tool);
                             reaches the engine only when use_solved_prices=True,
                             which is False everywhere by default
    demand.py               imported by NOTHING under sim/engine/ or sim/solve_prices.py
    labour_market.py        imported by NOTHING under sim/engine/

So: five of the eight `sim/world/` domain modules are already authoritative
and wired directly into the engine (agriculture, demography, land, transport,
military_logistics). One (`deposits.py`) is reachable through a tool the
engine can call but does not by default - the live engine still prices ore
through its own `sim/engine/economy_mining.py` path, and `deposits.py`'s
Ricardian-rent mechanism only takes over when `use_solved_prices` is flipped
on, which it is not. Two (`demand.py`, `labour_market.py`) are wired into
nothing at all - the live engine has its own separate revenue path
(`sim/engine/economy_production.py`) and its own separate labour-pricing
path (`sim/engine/labour.py`, the static `TRADE_DENSITY` classification the
`labour_market.py` docstring itself names as what it is meant to replace),
and neither reads the standalone module.

`docs/architecture/STATE_OF_THE_PROJECT.md` Part 4 also already states the
intended migration path for the two fully-unwired modules, in priority
order: wire `labour_market.py` into the engine first (named the single
most-referenced missing piece across the open complaints), then wire
`demand.py` into `sim/solve_prices.py` in place of the current mass-split
joint-byproduct allocation. Neither module is a dead research artifact
awaiting a retire decision; both are complete, tested, and simply not called
from production code yet, per that same document's own framing ("a wiring
job, not a design job").

## How this sits against CLAUDE.md

§4 states plainly that "nothing reads this data yet" for `data/production/`
is a different, earlier-stage problem than what is described here; the
`sim/world/` situation is one level further along; the mechanism exists in
working, tested code, only the wiring is missing. That distinction (data
exists vs. code exists vs. code is called) is worth being precise about
whenever this area comes up again, because conflating "unwired" with
"unbuilt" is exactly the mistake this finding's own framing risks if read
too quickly.

## Size

The documentation this finding asks for already exists; the remaining work
is the wiring itself, which is `Complaints/106`'s scope, not a new
documentation task. This complaint's only remaining contribution is noting,
for the record, that `deposits.py`'s status ("reachable through a tool the
engine can call but does not by default") is subtly different from
`demand.py` and `labour_market.py`'s status ("wired into nothing"), a
distinction the player's original finding does not draw but which matters
for prioritising the wiring work.

## Cross-references

`docs/architecture/STATE_OF_THE_PROJECT.md` Parts 2-4 answer this finding
directly; read that document rather than re-deriving the answer.
`Complaints/106` (ECON-004) is where the actual wiring work is tracked.
