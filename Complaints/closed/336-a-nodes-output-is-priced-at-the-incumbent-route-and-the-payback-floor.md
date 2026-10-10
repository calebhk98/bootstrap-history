# A node's output is priced at the incumbent route, and the payback floor reads gross revenue

**Status:** closed - the payback floor is a diagnostic; a new technique's output starts at the incumbent's price and falls as its maker competes (scenario `test_economy_innovator_pricing`, no expected failures left); capacity is judged at the price after its own additions; the engine layer's floor is derived

Two faults in how a derived concern's earning is judged. A node whose technique is not yet held (Solvay soda at the civilisation's start) sells at the price of the incumbent, dearer, route, so its margin is a monopoly's rather than a competitor's; neither that nor selling at its own cost is derived. And the payback floor (`test_node_revenue`, the pump guard in `test_early_playtest.py`) tests build cost over gross revenue, which counts wages passed through to staff, so a cheap, labour-heavy node (hand papermaking) sits near the floor while netting nothing. Net of derived upkeep is the figure a money pump shows in.

Related: `Complaints/319`, `Complaints/329`, `Complaints/283`.

Related: 140, 295, 317, 318, 335, 337.

## How it closed

- **Payback floor.** `node_payback_diagnostic` (`simulator.py economy-check --payback`) lists fast net paybacks and never caps revenue. Typed node revenue is deleted (commit 5ac67f70; a typed revenue is a validate error), so the gross-revenue test no longer exists.
- **Engine layer's floor and ceiling ratio.** Re-measured after 5ac67f70. The floor is no longer authored: `MarketClearingMixin._floor_ratio` (`sim/engine/market_clearing.py`) is the running share of the incumbents' own cost (`commodity_floor_ratio`, `entry_cost.running_share`), and only a commodity nothing can split sells at its full cost; `python3 -m sim.tests --only running_cost_floor` pins it. The ceiling (`price_ceiling_factor` in `data/world/commodities.json`, `market.DEFAULT_CEILING_RATIO`) is where demand turns to substitutes, not a stand-in for an incumbent's cost, and stays a declared heuristic (`python3 sim/constants.py --burndown`).
- **Capacity at the post-expansion price.** `sim/economy/expansion_price.py` reads the price a producer's own additions leave from the year's buyers' schedules; `producers_close._expansion` judges the loan to expand at that price (wired in `year_close.close_agents`; `test_economy_expansion_price`). A newcomer drawn by a margin was already sized by the gap at its entry price, which leaves the price after its additions at or above that price (`entry_margin.py`). Expansion is go or no-go at the planned step, not resized.
- **The two expected failures.** The steady fall already held with the seller-pricing build (two-year means fall every step) and its marker was a leftover. The incumbents' exit test asked them to be gone two years after the entrant alone matched the pre-entry volume; but a lower price grows what buyers take, and incumbents run at a profit while the price covers their cost, so leaving earlier would be a rule rather than an outcome. The test now asks that none leave before the entrant can serve the old market and that half are gone within the loss years plus the pace a market sheds makers (both from the producers' own declared constants).
- **Left over.** Year to year the price alternates (buyers' budgets chase last year's price): Complaint 470.
