# A state buys a material no market quotes for nothing

**Status:** closed

`material_cost` answers 0.0 when the market quotes no price for a material, at home
(`sim/engine/agents_port_budget.py`, `AgentsPortBudget.material_cost`: `0.0 if quote is None`) and now for a
country (`sim/agents/country_state.py`, `CountryStateView.material_cost`). Every state budget line that buys goods
reads it: the army's equipment (`sim/agents/budget.py`), the dole and the granary (`budget_lines.py`,
`budget_works.py`, `government_granary.py`), works and fleets (`budget_lines.py`), state enterprises' shortfalls
(`state_enterprises.py`) and the levers' purchases (`government_levers.py`). So where nobody sells a material, the
state's need for it costs nothing and is counted as met.

Why it matters: a state in a country whose markets do not trade grain or iron feeds and arms its people for free,
which removes exactly the scarcity the budget is meant to feel (CLAUDE.md 4.1, 4.3). Complaint 642 already made an
untraded market report a named quote instead of a price; the budget ignores that distinction.

What it would take: `material_cost` returns "not on sale" as a value (None or a refusal with a `cause`), each caller
treats the unbuyable part as unmet (the line's shortfall, with the consequence it already has for an unfunded need),
and a rule test per caller on a built world with an unquoted material.

**Done.** `material_cost` answers None (not on sale) at home (`BudgetView.material_cost`, `sim/engine/agents_port_budget.py`)
and for a country (`CountryStateView.material_cost`); `material_price` still answers 0.0 for a valuation. A line that needs a
material nobody sells books the tonnes in `Line.unbuyable` (`budget_line.goods`) and prices and buys none of it: army,
dole, campaign, navy (a ship type with no seller ranks after every one on sale), mandates, and the state's plants (an
input nobody sells limits what the plant makes to what the stores cover). The stores meet unbuyable need first; the
granary does not restock grain nobody sells. The state records the tonnes as `unmet_goods`, an army short of its iron
shrinks as an unfunded one does (`budget.supplied_share`), its own plants are asked for them (`needs_of`), and a state
with unmet goods lends nothing (`cannot_meet_own_need`). Rule tests: `sim/tests/test_unquoted_material_not_free.py`.
Not changed: unmet goods raise no levy (there is no price to levy), and `material_price` of an unquoted material is
still 0.0 for the granary's sale and in-kind revenue valuations.
