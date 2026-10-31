# A seller facing inelastic demand has an unbounded markup, and a sold-out seller's ask ratchets

**Status:** partly - asks are bounded by a cost band and move with stock against target; the band's width where buyers do not substitute is a stated multiple (`ASK_BAND_CEILING`), and the charcoal and glass asks are not re-measured

## What is built

- No ask is unbounded: `seller_offers.substitution_markup` is elasticity over elasticity minus one where buyers substitute
  more than one for one, else `ask_adjust.ASK_BAND_CEILING`; `seller_offers.ask_band_multiple` never exceeds that ceiling.
  `ask_adjust.band_edge` marks up only what the seller adds (labour, rent, plant), not the inputs it buys, so a chain of
  makers' ceiling grows by a sum, not a power.
- A seller chooses its ask as Eurace@Unibi's firm does (`sim/economy/price_setting.py`, called from
  `seller_offers.strategic_offers`): the best price on a grid around its own, from the market's size times its logit share
  against the other sellers' asks, held inside the band. The whole-book search is gone. That rule has no demand response to
  its own price except through the share against rivals, so the band is what stops a lone seller climbing the grid.
- Between years a seller's expected price moves with its stock against its target, both ways, in proportion to the gap and
  inside the band (`ask_adjust.adjusted_within_band`, called from `producers.next_expectations`); one with no cost to anchor
  on does not move. Within the year an unsold seller is brought down by `unsold_search.py`.
- Within-year switching of sellers: buyers split demand over sellers by logit and a rationed buyer chooses again among the
  sellers still holding stock (`goods_market_logit.py`, two rounds).
- Tests: `test_economy_ask_band.py`, `test_economy_ask_stock_rule.py`, `test_economy_ask_band_chain.py`,
  `test_economy_seller_markup_limit.py`, `test_economy_aggregate_producer_pricing.py`.

## What is wrong now

- `ASK_BAND_CEILING` is a labelled temporary heuristic (`retire` this complaint; Lengnick 2013 eq 8-9 and Caiani et al. 2016
  eq 3.6-3.7 are the shape, no figure is claimed). The width is derived only where buyers substitute; deriving it from the
  buyers' cheapest alternative way to meet the need, priced from recipes, is not built.
- `GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR` (the speed of the between-year move) is a labelled heuristic that retires to 473.
- The spin-up has not been re-measured under the Eurace price rule: `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

## Charcoal's home ask far above its long-run price (PM, 2026-10-22)

`business_review_scenario`'s trace found charcoal's home ask at many times its long-run cost-covering price both before and
after the held rate (641), enough to drive a consumer concern's market factor to zero. The ask band should bound it. Measure
with `goods_market.home_unit_price('charcoal_kg')` against the long-run price on a default Rome game.

## Glass opens at many times ceramic's price (PM, 2026-10-22)

526's trace found `glass_raw_kg` opening in England at a price per kilogram tens of times ceramic's, which made it most of the
opening basket's value while it is a small share of what trades. A raw glass ask that high against its making cost is the ask
band failing to bound it, or the opening solve pricing it from a thin quote. Measure with `economy_api.agent_prices` against
`_material_prices` on an opened England game.
