# The market view has no `equity(agent)`, so the opening's wealth wish is never set against what households own

**Status:** open

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

Depends on 538 (land and plot titles carry a value).

**What is wrong.** Rome without a spin-up settles at about a quarter of the full-employment ceiling because the savings wish is far larger than the wealth the opening holds. A throwaway probe that added firm equity to the wealth `goods_orders` sees raised the settled ratio and reached the ceiling only near the wish.

**Evidence.** `households_orders.goods_orders`, `_opening_bids`; `ownership_share`. Reproduce with `build_setup(unopened_sim(civ="rome_100ad"))` then `opening.open_economy` (the probe is not kept).

**Why it matters.** An opening that spends less than it earns drifts for decades (CLAUDE.md 4.1, 4.2).

**What it would take.** A `view.equity(agent)` on the `MarketView` protocol (firm net worth and titles), read alike by `goods_orders` and `_opening_bids`, so year-0 income matches the opening.

**Test.** A test: realised year-0 income is within a band of the opening figure on a fixture with firms owned by households.
