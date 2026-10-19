# The founder's living cost and the economy's household needs are two models

**Status:** open

Found closing 524. A seat's yearly living cost is `living_cost()` (`sim/engine/labour_port.py`,
`sim/engine/economy_credit.py`): a person's subsistence plus a household base for dependants, priced by the engine.
The agent economy's households pay for the same needs through `data/world/needs.json` floors at the economy's own
prices (`agent_need_floor_costs`). At a default Rome opening the founder's living cost is several times what the
economy's floors cost one person of the same income, and the two do not read each other.

Measure: in a default `rome_100ad` game compare `game.living_cost()` with the sum of `agent_need_floor_costs` for one
person on the founder's tile (no committed command prints both; the 524 regression test
`sim/tests/test_founder_income_living_cost.py` builds the game).

Why it matters (CLAUDE.md "general actors", 4.5): the founder and every household should eat, dress and house
themselves by one rule at one set of prices. With two, a founder can be ruined by a cost no household of the same
income pays, and a fix to one (524 sheds dependants a household's income cannot carry) is invisible to the other.

What it would take: the seat's household buys its needs through the same need basket and floors as the economy's
households, at the economy's prices on its tile; `living_cost()` becomes a read of that bill; the household base
for dependants becomes dependants who are people with needs (and hours) of their own. Related: 508, 514, 524.
