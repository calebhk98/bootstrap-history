# The founder's ventures and other actors' concerns are separate implementations of running a business

**Status:** open - one design with 510 (`docs/architecture/FIRMS_OWN_PLANTS_PLAN.md`); 510 also carries the opening check for whether plants pay their way (was 528)

Found closing 479: firms took their crew from the plant while the founder's ventures still took it from takings,
and nothing stopped the two from diverging, because they are different code. The founder's ventures are `Sim`
mixin methods (`sim/engine/projects_ventures.py`, `projects_venture_quotes.py`: `open_venture`, upkeep, staffing,
closure); firms and player seats run concerns in `sim/agents/` (`business_books.operate`, `firm.operate`,
`player.operate`). Each rule a business follows (crew, upkeep, takings, closure, sale) can exist in two versions, one
of which only the founder sees. Measure: `grep -rn "def open_venture\|def operate" sim --include=*.py`.

Why it matters (CLAUDE.md "general actors"; multiplayer): every mechanism the founder uses must be usable by any
actor, and a fix in one path silently misses the other.

What it would take: one business object (a firm with plants, see 510) in `sim/agents/`, run by the same code for
every owner; the founder's commands act on the founder's firms through it, and `projects_ventures.py` keeps only
the founder's choices (what to open, whom to staff it with). A wall test that fails when the engine computes a
business's crew, upkeep or takings outside that object.

## Economy producers (outside review)

The split is wider than founder against firms: actor businesses run through `sim/agents/business_books.py`
(takings, upkeep, crew, payments) while the agent economy's `Producer` objects run recipes with their own
capacity, inputs, workforce, stock and cash, and founder concern output enters the economy through
`EDGE_LEGACY` (`sim/engine/economy_port_year.py`). Double counting was not established; the risk is a
constraint enforced on one path and bypassed on the other. Target: owners (founder, firm, state) decide
what to build and run, and one production machinery runs every plant.
