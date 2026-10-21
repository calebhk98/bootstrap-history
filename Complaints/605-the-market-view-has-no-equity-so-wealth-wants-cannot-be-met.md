# The market view has no `equity(agent)`, so the opening's wealth wish is never set against what households own

**Status:** partly done - `equity(agent)` is on the view and counted in households' wealth, in the year loop and in the opening's settlement; the wish still exceeds what households own (see 607)

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

Depends on 538 (land and plot titles carry a value).

**What is wrong.** Rome without a spin-up settles at about a quarter of the full-employment ceiling because the savings wish is far larger than the wealth the opening holds. A throwaway probe that added firm equity to the wealth `goods_orders` sees raised the settled ratio and reached the ceiling only near the wish.

**Evidence.** `households_orders.goods_orders`, `_opening_bids`; `ownership_share`. Reproduce with `build_setup(unopened_sim(civ="rome_100ad"))` then `opening.open_economy` (the probe is not kept).

**Why it matters.** An opening that spends less than it earns drifts for decades (CLAUDE.md 4.1, 4.2).

**What it would take.** A `view.equity(agent)` on the `MarketView` protocol (firm net worth and titles), read alike by `goods_orders` and `_opening_bids`, so year-0 income matches the opening.

**Test.** A test: realised year-0 income is within a band of the opening figure on a fixture with firms owned by households.

## Built and measured (branch `605-607-saving-finds-a-use` (merged as `44cd2125`, then deleted; `equity.py` is in main, `opening_equity.py` is no longer in `sim/economy`))

- `sim/economy/equity.py`: `holdings(setup, record, view)` is each cohort's share (the tile's ownership shares, as
  dividends are split) of the net worth of the producers its tile's owner holds: cash plus plant at replacement cost
  at the view's prices less debt, floored at zero. `CreditView.equity(agent)` answers from it (once per view);
  `credit_view.equity_of` reads it from any view. `households_orders.goods_orders` adds it to the wealth the drawdown
  compares with the savings wish.
- `sim/economy/opening_equity.py`: the opening has no producers when it settles income, so `OpeningView.owned` holds the
  firms the settlement's own runs imply (plant at replacement and working capital), shared by people and ownership
  share. A scenario that states its income skips it, as before.
- Value tests: `sim/tests/test_saving_finds_a_use.py` (shares follow ownership; a household that owns firms spends more
  than one that owns none, with the same cash and income).
- Found on the way: a working-capital loan struck ahead of the year left a key in `record.expansion_runs`, which
  `open_entrants` reads as "plant it asked for is still to come", so a market's entry stopped whenever no other loan
  request existed that year. `_lend` now clears it on its early return (`economy_entry_margin` caught it).
- Measured effect (commands under 607). The opening's own gain is small: the settled income over the ceiling on the
  fixture moves from 0.0866 to 0.0875, because the opening's firms are worth little against a wish of years of
  surplus income. The year loop gains more.
