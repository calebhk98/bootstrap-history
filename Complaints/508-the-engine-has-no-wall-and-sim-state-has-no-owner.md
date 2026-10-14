# The engine has no wall: `Sim` state is reached from everywhere, so a change cannot see its readers

**Status:** open

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
