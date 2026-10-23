# Bronze is priced by one thin market, far above its inputs, and tin is cheaper than copper

**Status:** closed - the runaway price is gone; the aged-game validation holds bronze within an order of magnitude of its recipe cost (owner decision 2026-10-21)

## Closed (2026-10-21)

Owner decision: the concern was a price hundreds of times the recipe cost. The full slow run on 3cb9c9a0 read the worst aged-game
year at a few times cost, which is accepted while the opening does not settle (473). The validation's bound is now an order of
magnitude (`MARKUP_BOUND` in `sim/tests/test_economy_bronze_market_price.py`), so it catches a runaway and passes thin-market
noise. Measure: `python3 -m sim.tests --slow --only economy_bronze_market_price --jobs 1`.

## Reopened (earlier the same day)

The original opening-price defect was fixed, but the aged-game check that names this complaint fails on main: bronze shows and
trades above a bounded multiple of its recipe cost in some years, and the worst multiple grew between the last two full slow
runs (`Complaints/558`). Find which years overshoot and which part of the price causes it (the ask, the budget bids, a thin
market's memory) on the current code; fix the rule, or show with the measurement that the cause is the unsettled opening (473)
and let this close with it. Do not widen `MARKUP_BOUND`.

On the `market` screen of a Rome game (`play --civ rome_100ad --kit merchant --seed real25`), bronze sells
for about ninety times what its recipe's inputs cost. The recipe (`bronze_kg` in
`data/production/20_nonferrous.json`) is a melt of copper and tin with a little charcoal and a few
furnaceman and smith hours. Bronze should cost more than its inputs, because it takes fuel and skilled
hours and is in demand, but by a markup, not by two orders of magnitude. Every project that needs a little
bronze (`units_standards`, on the goal path) cost many years of the founder's income, and a decade later it
cost a tenth as much.

Cause:

- **The price shown is a remembered market price, not a cost.** `notional.shown_prices`
  (`sim/economy/notional.py`) shows `national_prices` (`sim/economy/national_prices.py`), which is a
  volume-weighted mean of each area's remembered price. Almost every area's bronze price is still its seed.
  One area actually trades, and that one area's thin price is the national price.
- **That area's price ratchets.** Its buyers are a household and the state bidding fixed budgets with no
  maximum price. A handful of sellers re-pick asks against that residual demand
  (`sim/economy/seller_offers.py` into `seller_pricing.best_reservation`). Their producers are idle, with
  years of losses and no expected sales. A few hundred units clear at a price set by budgets over quantity,
  and it swings tenfold between years.
- The "market lib/yr" column shows idle capacity, not trade.

Bronze demand comes from the `implements_and_arms` need (`data/world/needs.json`), and nothing ties its bid
to a substitute or to what bronze costs to make. This is the same family as closed 472 (thin market, price
memory), but a different cause.

Tin: tin's own market has not cleared for years, so the screen shows its recipe cost. The recipe makes
cassiterite with a few miner and labourer hours a tonne and nothing for the scarcity of the deposit, while
copper's recipe carries a large ore and labour cost. So tin comes out a fraction of copper's price, the
reverse of the historical relation. Tin's scarcity is geographic (few deposits, long haul), and the recipe
cannot express that.

Why it matters (CLAUDE.md 4.5): prices are meant to fall out of production. Here a thin market's memory
sets the price of a common alloy, and it decides which goal-path projects a player can afford.

What it would take:
- `national_prices` should discount areas whose recent volume is negligible.
- Budget bidders for a need need a ceiling, or substitution toward iron, copper or stone.
- An unsold seller's ask should be held near its cost times a markup.
- Cassiterite should draw on a limited deposit stock, so tin's scarcity comes from geography.
- A regression test that bronze's shown price stays within a bounded multiple of its recipe cost in an aged
  Rome game.

## Update

`notional.thin_market_prices` (in `shown_prices`, so the market screen and the engine's price ratio for
material purchases both see it) blends a recently traded good's price toward its making cost by how far its
total traded volume falls short of `THIN_MARKET_SHARE_OF_OPENING_DEMAND` times the opening quantity. Goods
the opening did not want, or nobody can make, are unchanged. Regression tests:
`sim/tests/test_economy_thin_market_price.py`. Also changed (round 2):
- The state's need bids carry the basket's elasticity of substitution instead of unit elasticity, so a dearer
  good draws a smaller share of the need's budget as its price rises, as for a household; the need's total
  budget is unchanged and money printing still passes through to prices (`economy_state_budget`). A dearer good
  therefore no longer ratchets against a fixed sum. Test: `sim/tests/test_economy_state_need_bids_substitute.py`.
  (A hard ceiling on the cheapest good was tried first and dropped: it weakened that pass-through.)
- A market whose year's trade falls short of a representative trade of its usual volume relaxes its remembered
  price downward toward the making cost, at the no-offer rate scaled by the shortfall
  (`market_memory_offers.price_after_thin_trade`, called from `year_goods.clear_goods`). Measured against the
  usual volume, not what buyers wanted, so a supply-short market is not taken for a dead one. With full spin-up
  (`ROME_SPIN_UP_YEARS=30,15`, `S.Sim`, `measure` as in the test's helper) the traded price stays within a small
  multiple of the recipe cost; before it was about two orders of magnitude above for most of a decade.
  Test: `sim/tests/test_economy_dead_market_memory.py`.

Tin's scarcity (cassiterite's deposit stock) is filed as 511.
