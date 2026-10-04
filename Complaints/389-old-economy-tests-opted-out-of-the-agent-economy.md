# Tests of the old economy's mechanisms opt out of the agent economy and need replacements

**Status:** partly - agent-economy tests now cover money, state budget, loanable rate and foreign balances (test_economy_agent_*.py); labour pressure, freight, interest groups, wage table and surplus sales are still to decide

When the agent economy became the default, tests that check the engine's own yearly material market, goods saturation factor, wage table, loanable-funds rate, state budget and surplus sales, interest-group displacement, local labour pressure, freight and foreign trade were made to opt out (`agent_economy=False`). They still guard the old path, but the behaviour players now see comes from `sim/economy/`, and several of those behaviours (the state's budget and surplus, the rate's response to the money stock, foreign trade balances) have no agent-economy test of the same relationship.

List the files with `grep -ln 'agent_economy=False\|"agent_economy": False' sim/tests/*.py`.

What it would take: for each, decide whether the relationship it guards should hold on the agent economy; if so, write the agent-economy version; when the old path is deleted, delete the opted-out test with it.
