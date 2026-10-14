# Bronze is priced by one thin market, far above its inputs, and tin is cheaper than copper

**Status:** partly (shown price blends toward making cost by this year's trade; producers' asks are held to cost times the substitution markup and idle ones come down to it; the remembered market price of a dead market still decays only with its usual volume, budget bidders' ceiling for a dearer good is open, and so are tin deposits)

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
`sim/tests/test_economy_thin_market_price.py`. Still open: the budget bidders' missing ceiling or
substitution, holding an unsold seller's ask near cost times a markup, cassiterite's deposit stock, and the
aged-Rome-game bound on bronze's shown price (not yet measured).

## Update 2

Measured with `python3 -c "from sim.tests.test_economy_bronze_market_price import bronze_multiples; print(bronze_multiples(26))"`
(Rome's agent economy stepped on its own after the suite's short spin-up): bronze's shown price over its recipe
cost at the shown input prices, and the traded market price (`national_prices`) over the same cost, both stay
within a bounded multiple (`sim/tests/test_economy_bronze_market_price.py`, a slow check). Before the changes
the traded multiple of the same run reached a few times its cost late in the run and, in the Sim game
(`sim/tests/harness.py` openings, `S.Sim` stepped), several times; the shown multiple was already near one.

What changed:
- `notional._estimated_prices`: untraded goods (made-cost) and thin goods (blend toward making cost) are now
  priced in one pass in input-depth order. Before, a thin good was blended toward a cost computed from an
  input's stale remembered price, because the input's making-cost estimate was applied afterwards; bronze's
  shown price jumped against its inputs' shown prices.
- The thin-market depth counts a market for the smaller of what it usually trades and what it traded last
  year, so a market that dried up no longer stands for the good on its remembered volume.
- `seller_offers.strategic_offers` holds a producer's ask to its unit cost times `substitution_markup`
  (price over cost of a constant-elasticity seller at the basket's elasticity of substitution, derived, not
  chosen). Against buyers that spend a fixed sum and name no maximum, profit rose with the ask without limit and
  the ask ratcheted up by the markdown share a year; now it cannot. A producer that sells less than
  `IDLE_SALE_SHARE` (a labelled heuristic) of its offer at an ask above the limit comes down to the limit at
  once. Tests: `sim/tests/test_economy_seller_markup_limit.py`, `sim/tests/test_economy_thin_market_price.py`.

Still open:
- Budget bidders: households already carry a substitution ceiling on the cheapest good of a need
  (`need_basket.price_ceilings`); a dearer good has none (bought for variety). Giving the state the same
  ceiling was tried and dropped: it weakened the pass-through of money printing into prices
  (`economy_state_budget`, printing test) and did nothing for bronze, which the state buys as a dearer good. A
  ceiling for the dearer good needs a derivation that does not price out luxuries (silk against cloth).
- A dead market's remembered price moves only by trade over usual volume (`year_goods.remembered_price`), so
  after years of near-zero trade it decays with the usual volume rather than at once. The shown price no longer
  follows it; planning (producers' expectations, household store values) still does. That is the price-memory
  family of closed 472, not changed here.
- Cassiterite's deposit stock (data and geography work) is not filed as its own complaint yet.
