# Tests of the old economy's mechanisms opt out of the agent economy and need replacements

**Status:** closed - agent-economy counterparts exist for money, state budget, loanable rate and foreign balances; the opt-outs left each carry a one-line reason and pin a legacy mechanism the default game no longer runs

When the agent economy became the default, tests that check the engine's own yearly material market, goods saturation factor, wage table, loanable-funds rate, state budget and surplus sales, interest-group displacement, local labour pressure, freight and foreign trade were made to opt out (`agent_economy=False`). They still guard the old path, but the behaviour players now see comes from `sim/economy/`, and several of those behaviours (the state's budget and surplus, the rate's response to the money stock, foreign trade balances) have no agent-economy test of the same relationship.

List the files with `grep -ln 'agent_economy=False\|"agent_economy": False' sim/tests/*.py`.

What it would take: for each, decide whether the relationship it guards should hold on the agent economy; if so, write the agent-economy version; when the old path is deleted, delete the opted-out test with it.

## Resolution

Every remaining `agent_economy=False` line in `sim/tests` now ends in a `# legacy: ...` reason, or states that the switch itself is under test. Count them with `grep -rnE 'agent_economy=False|"agent_economy": False' sim/tests`.

Decided case by case by removing the opt-out and running the file:

- Opt-out removed, file passes on the agent economy unchanged: `test_cross_system_invariants`, `test_agents_cast_wiring`, `test_demographics`.
- Ported in part: `test_labour_market_town_pricing` (housing factor, firm/founder equivalence, bondage, workshop, pressure release now run on the agent economy; only the two checks that read housing through the engine's wage quote stay legacy), `test_economic_levers_inventory` (the farmland lever's food-cost factor runs on the agent economy; the wage-quote half stays legacy), `test_allocate` (only the standing work order, compared with the engine's wage-table rate, stays legacy).
- Kept, with a reason, because every failing check pins the engine's own yearly market, wage table, loanable rate, goods-market saturation or foreign trade: `real_output`, `dynamic_wages`, `state_strata_fiscal`, `state_budget`, `state_revenue_forms`, `foreign_economy_trade`, `capital_market`, `concern_volume`, `state_surplus`, `per_producer_supply`, `foreign_freight_balance`, `market_engine`, `luxuries_cross_borders`, `firm_expansion`, `firm_costs_scale`, `actors`, `actor_firms_compete`, `wage_provider`, `goods_market`, `economic_caching`, `player_log`, `interest_groups`, `civ_starting_rates`, the loom fixture in `harness`.
- Intentional: `test_agent_economy_wiring` tests the switch.

When the legacy path is deleted, delete the `# legacy:` tests with it. Behaviours with no agent-economy test of the same relationship yet (freight lift shortfall, interest-group displacement, surplus grain sales, wage response to food cost) are the follow-up list; the agent economy models them differently, so each needs a new test of its own mechanism, not a port.
