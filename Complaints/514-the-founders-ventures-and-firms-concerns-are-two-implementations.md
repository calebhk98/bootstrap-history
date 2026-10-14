# The founder's ventures and other actors' concerns are separate implementations of running a business

**Status:** open

Found closing 479: firms took their crew from the plant while the founder's ventures still took it from takings,
and nothing stopped the two from diverging, because they are different code. The founder's ventures are `Sim`
mixin methods (`sim/engine/projects_ventures.py`, `projects_venture_quotes.py`: `open_venture`, upkeep, staffing,
closure); firms and player seats run concerns in `sim/agents/` (`concern_ops.operate_concern`, `firm.py`,
`player.py`). Each rule a business follows (crew, upkeep, takings, closure, sale) can exist in two versions, one
of which only the founder sees. Measure: `grep -rn "def open_venture\|def operate_concern\|def operate" sim --include=*.py`.

Why it matters (CLAUDE.md "general actors"; multiplayer): every mechanism the founder uses must be usable by any
actor, and a fix in one path silently misses the other.

What it would take: one business object (a firm with plants, see 510) in `sim/agents/`, run by the same code for
every owner; the founder's commands act on the founder's firms through it, and `projects_ventures.py` keeps only
the founder's choices (what to open, whom to staff it with). A wall test that fails when the engine computes a
business's crew, upkeep or takings outside that object.
