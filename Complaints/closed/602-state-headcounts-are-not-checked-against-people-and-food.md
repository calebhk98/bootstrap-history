# The state's soldiers, officials, scholars and builders are not checked against working-age people and food

**Status:** closed - pinned by sim/tests/test_state_headcount.py and test_state_headcount_home.py. A state's army is limited by its country's working-age people less the farm hands the food needs, and by last year's food ratio (sim/agents/headcount.py; hands from sim/agents/country_hands.py for a foreign country, `state_hands` in sim/engine/agents_port_budget.py at home); the shortfall and its cause are on the state's `record.headcount`. Officials, court, roads, masons and navy count against the same pool but are not themselves scaled down.

Part of Complaint 489 (Population is one national figure, and soldiers, scholars and builders are not checked against food and people).

Needs per-country population (home exists; foreign is 590). Related: 486.

**What is wrong.** The state's army and officials are budget lines paid at the going wage. No check holds farmers, soldiers, scholars and builders to the working-age people and surplus food that exist, and a shortfall does not force the state to disband or levy.

**Evidence.** `sim/agents/budget.py`; the farm-hours shift in `sim/labour/labour_allocation.py` acts on society's hours, not on the state's headcounts.

**Why it matters.** A state reallocating tens of thousands to research and an army must be fed by real surplus, or face famine and revolt (486).

**What it would take.** A headcount ledger per country (farm, soldier, scholar, builder, other) checked each year against working-age people and food, with a shortfall forcing disbanding or a levy.

**Test.** A test sets an army larger than the surplus allows: the ledger shows the shortfall and the state disbands or levies; a feasible army is untouched.
