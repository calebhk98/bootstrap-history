# Prices use long-run cost, not the current market

**Status:** partly - on the agent economy (the default) every price is the year's market clearing; on the engine side a producer whose plant is built offers at its running cost (the entry's cost without the plant's repayment) and the clearing's floor is the running share of the incumbents' cost, capped by the stated floor; remaining: the coin metal's revaluation (not started, see the Update 2 list), the goods market and wages do not use the clearing, the stated floor stays as the outer bound for stock sold below any producer's cost, and `foreign_actor_trade.py` still uses the stated floor

## What is wrong

The price solver prices a good at its long-run cost of production, including a
mine's up-front cost spread over its whole lifetime output (amortisation). A
real price is set by the market now: current supply against current demand,
with sunk costs playing no part once a mine is dug.

- A mine that produces most of its ore in its first decade floods the market
  then, and the price should fall then and recover later, not sit at an
  average over a century.
- Capacity that does not exist yet (a dam that will make cheap aluminium in
  ten years) should not lower today's price.
- A windfall of stock (every household finds iron in their room) should drop
  the price at once, with no production change.
- Money: each civilisation's money is tied to its coin metal, valued at the
  metal's cost at the opening technology and then frozen. A modern silver or
  gold mine that floods the market should lower the metal's value and so the
  coin's, which is inflation (as with New World silver in early modern
  Europe). Today it does not.

## What economists use

Exhaustible resources are usually modelled with spot prices set by marginal
extraction cost plus a scarcity rent (Hotelling), stocks and flows cleared in
a market each period, and investment decided by expected revenue against
up-front cost. Sunk costs matter to the decision to build, not to the price
afterwards. See `docs/architecture/ECONOMY_MODEL_SURVEY.md`.

## What it would take

- Keep the solver's long-run cost as a reference and a starting quote.
- Add a per-period market for each good: supply from existing stocks and
  current production capacity of every actor, demand from households and
  producers, price clears between them.
- Use amortisation only in the decision to build (quotes, payback), not in
  the market price.
- Revalue each civilisation's money from its coin material's market price
  each period, so metal gluts cause inflation and shortages deflation.

## What landed, and what remains

Landed: each commodity has a yearly clearing of society capacity, actors'
output (one call, `actor_supply`), carried stock and the founder's sales
against household demand (population and income, through
`sim/world/need_demand.py`) and the founder's purchases. The quote and every
purchase bill multiply the solver's long-run cost by that year's ratio, which
can fall below one down to a running-cost floor (sunk capital is not in it)
and rise to a ceiling. A stock windfall lowers the price at once; capacity
that does not exist yet plays no part. `python3 sim/audit_costs.py` (script since removed; recover with `git show 97473f1:sim/audit_costs.py`) still
measures where the long-run anchor comes from; `market_state(material)` on a
live game shows the year's clearing.

Remains: the floor and ceiling are heuristics (a split of each recipe's cost
into running and capital parts would give the floor); the coin metal's
revaluation (inflation from a metal glut) is not wired; amortisation is still
in the solver's cost rather than confined to decisions to build; the goods
market and wages do not use this clearing; a material's own deposits and a
mine's output feed supply only through what the founder sells.

Related: 102, 326, 338, 359, 364.

## Update (Complaint 375)

The price a good clears at is no longer one solved long-run cost for the society: each producer offers at the cost of the entry it runs and the market clears the offers against demand. The solver gives the incumbents' cost, the cost of one entry for a producer, and a baseline for a good nobody yet makes. A mine's amortised cost still enters through the solver's cost of the entry; a producer that has sunk its capital selling below the full cost (the floor) is the existing floor ratio, not yet each producer's own running cost.

Owner decision (2026-10-09): high priority: a bigger issue than it looks; do it soon.

## Update 2 (running cost for sunk plants)

Done: `recipe_cost_and_allocation(..., include_capital=False)` costs an entry without its plant's repayment; `CostBook.running_unit_cost_hours` and `running_share` give the split per entry. Concerns that exist (the founder's operating ventures, firms' concerns offered through `offer_sale`) offer at that running cost (`producer_costs.py`), while the incumbents' reference, quotes and payback stay at the full cost, so capital matters to the decision to build and not to the price once built. The engine's floor ratio is `commodity_floor_ratio` (the running share of the incumbents' entry), no higher than the commodity's stated floor, so a capital-heavy good (a mine's metal) can fall further in a glut than a labour-only one. Tests: `sim/tests/test_running_cost_floor.py`.

Remains, for the coin-metal revaluation (inflation from a metal glut), which touches the money anchor and was left to its owner: the coin's value must follow `market_price_ratio` of the coin metal (today `_coin_metal_price` reads the incumbents' price with no ratio, `incumbent_prices.py`), through the mint standard in `money_units.py`; the price level (`home_price_level`) and the labour wage per hour (`labour_wages.py`) must then move with it without double counting the goods' own ratio; the foreign partners' coin prices (`partner_price_level`) need the same ratio; savings and debts in coin need a decision on who bears the revaluation. The floor ceiling for stock sellers needs `sim/world/market.py` to give stock and windfalls their own bound apart from producers' floor.
