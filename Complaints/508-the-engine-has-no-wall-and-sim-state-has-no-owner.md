# The engine has no wall: `Sim` state is reached from everywhere, so a change cannot see its readers

**Status:** partly - the owner and the wall are built; what remains is the forwarders. Each fact has one owner module (`sim/<module>/`) that publishes views and applies commands; modules read only declared views and send only declared commands (`python3 tools/check_module_reads.py` lists any that are not), the engine bridge answers no module read, and a guarded game refuses a write through a view's answer (`sim/assembly/read_guard.py`); the measures: `bash tools/done_check.sh`, `python3 tools/measure/module_graph.py --modules`. Open: `Sim` still inherits the forwarder mixins (`sim/engine/forward_*.py`, `core_properties.py`) that give old names to engine, mod and test callers; close this when `bash tools/done_check.sh` shows no mixin classes left on `Sim` (the plan is `docs/architecture/MODULE_MIGRATION_TASKS.md`)

The walled packages (`docs/architecture/PACKAGE_WALLS.md`) each have one surface and a wall test. The
engine has neither. `Sim` (`sim/engine/core.py`) is one object composed of many mixins that talk through
`self`; splitting it into files stopped merge conflicts (`SIM_DECOMPOSITION_REVISITED.md`) but left every
method free to read and write every field. Measure:

    python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(len(Sim.__bases__), len(Sim.__mro__), sum(callable(getattr(Sim,n,None)) for n in dir(Sim)))"
    grep -rlE "(self|sim)\.nodes\b" sim/engine sim/ui sim/agents --include=*.py | wc -l
    grep -rnE "\bsim\.[a-z_]+ = " sim/ui sim/agents sim/economy sim/labour --include=*.py | wc -l
    grep -c "@property" sim/engine/core_properties.py

The last line counts forwarding properties that give one field two names (`sim.capital` and its home under
`sim.state`). `sim/engine/ui_port.py` re-exports private `Sim` methods under public names, and many engine
paths assume the founder's household (`grep -rn "self\.household\.\|self\.state\.household" sim/engine | wc -l`),
against CLAUDE.md's general-actors rule.

Why it matters: an agent changing one method has no interface telling it which other methods read the same
field, so a fix that is right in its file is wrong somewhere it never opened. Several playtest defects were
one number computed in two places (the rule in `STATE_OF_THE_PROJECT.md` that a screen and the engine use
one function exists because of this).

What it would take, staged and fingerprint-checked: pick the most-read state groups (markets, projects, the
founder's household), give each an owning object with a small interface, move readers onto it, delete the
forwarding properties for that group, and add a wall test like `test_labour_core_walls.py` that fails when
code outside the owner touches its fields.

## Ownership map (outside review)

An owner per fact, with other systems receiving narrow views; all can stay in one process and one save:

| Fact | Owner | Others receive |
|---|---|---|
| Money and goods balances | ledger | balances, reservations, settlement receipts |
| Debt contracts | finance (555) | exposure, payment schedules |
| People, skills, employment | workforce (556) | available hours, employment results |
| Land, deposits, transport assets | resource owners | capacity grants, usage results |
| Plants and capacity | production (514) | planned and realised output |
| Orders and market outcomes | markets (507) | quotes, clearing results |
| Knowledge and actor objectives | actors and research | available techniques, orders |
| Indicators | reporting (554) | derived views |

Rules: one owner mutates its fact (production asks the ledger to pay, a market cannot make stock);
services take narrow inputs, not `Sim` (adapters such as `LabourWorld` in `sim/engine/labour_port.py`
still hand over the whole state); a cross-domain action commits whole or reports a partial or refused
result; every view says what it means and as of when. Not duplicates: `HouseholdState.capital`
delegating to the purse, forwarding properties that are aliases, the save record against the live
economy (`flush_record`), and expected, last, cost and quoted prices, which differ on purpose.

Order: document each fact's owner, writers, readers, units and timing; market reports (507); food and
land (549); common production (514); debt (555) and labour (556); shrink `Sim` alongside. Each slice is
tested at its boundary (no goods spent twice, no hours allocated twice, reports reconcile to
settlements, clearing caches changes nothing, save and load preserve the next step), and
behaviour-preserving moves are kept apart from economic fixes so a changed result can be attributed.
