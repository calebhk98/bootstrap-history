# A seller facing inelastic demand has an unbounded markup, and a sold-out seller's ask ratchets

**Status:** closed - no ask is bounded by a stated multiple: the width of the band above cost comes from the seller's buyers (`ask_ceiling.py`), at clearing and in the between-year expectation; the measurements below are for the orchestrator

## What is built

- No ask is unbounded. A good's ceiling is the highest its buyers give (`ask_ceiling.good_ceiling`):
  - a household need: the price at which the good costs per need unit what the cheapest other good of the need does (that good's price
    or its making cost, `alternative_ceiling`); with no other good in the need, the highest price at which any household bid still takes
    units (`buyer_limit`: budget over floor units, held to the bid's maximum price; the clearing writes it to
    `record.goods.buyer_limits`, `goods_good_clear.note_household_limit`);
  - a recipe using the good as an input (an intermediate good has no household need): the price at which the recipe costs per unit of
    its main output what the cheapest recipe for the same output without the good costs, never more than the run's revenue less its
    other costs, the most the buyer can pay and break even (`recipe_ceiling`).
  Making the seller's own good is not counted: that is entry (`entry_trial.py`). A good none of whose buyers gives a ceiling has none and
  its seller has no room above cost (`ask_adjust.NO_BOUND_MULTIPLE`), a refusal with a cause (`no_buyer_to_bound_it`), never an unbounded number.
- `ask_ceiling.band_multiple` scales the ceiling against the seller's making cost (never below one) and takes the lower of it and the
  substitution markup (elasticity over elasticity minus one, where buyers substitute more than one for one). `AskAlternatives` reads the
  year's prices once. The clearing context keeps a band multiple table per good and tile for the kernels, `seller_offers.ask_band_multiple`
  and `unsold_search.ask_limits` read the same, and the close kernel reads a per-producer, per-slot array (`close_pack_asks.ask_multiples`).
  The stated multiple `ASK_BAND_CEILING` is deleted. `ask_adjust.band_edge` marks up only what the seller adds (labour, rent, plant), not
  the inputs it buys, so a chain of makers' ceiling grows by a sum, not a power.
- A seller chooses its ask as Eurace@Unibi's firm does (`sim/economy/price_setting.py`, called from `seller_offers.strategic_offers`): the
  best price on a grid around its own, from the market's size times its logit share against the other sellers' asks, held inside the band.
- Between years a seller's expected price moves with its stock against its target, both ways, in proportion to the gap and inside the band
  (`ask_adjust.adjusted_within_band`, called from `producers.next_expectations` and the close kernel); one with no cost to anchor on does not
  move. Within the year an unsold seller is brought down by `unsold_search.py`.
- Within-year switching of sellers: buyers split demand over sellers by logit and a rationed buyer chooses again among the sellers still
  holding stock (`goods_market_logit.py`, two rounds).
- Tests: `test_economy_ask_ceiling.py` (each path: another good of the need, the household budget, the recipe switch, the recipe break-even,
  no buyer; charcoal and glass shaped inputs; a seller's ask held to the ceiling), `test_economy_ask_band.py`, `test_economy_ask_stock_rule.py`,
  `test_economy_ask_band_chain.py`, `test_economy_seller_markup_limit.py`, `test_economy_aggregate_producer_pricing.py`,
  `test_goods_context_asks.py`; the kernel-equals-reference tests (`test_year_speed_close.py`, `test_year_speed_goods_markets.py`,
  `test_year_speed_results_arrays.py`) run with written-out band widths.

## Left to others

- `GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR` (the speed of the between-year move) is a labelled heuristic that retires to 473.
- Measurements under the new bands (no game was run here): `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`, and the two cases below.

## Charcoal's home ask far above its long-run price (PM, 2026-10-22)

`business_review_scenario`'s trace found charcoal's home ask at many times its long-run cost-covering price both before and
after the held rate (641), enough to drive a consumer concern's market factor to zero. The ask band should bound it. Measure
with `goods_market.home_unit_price('charcoal_kg')` against the long-run price on a default Rome game.

## Glass opens at many times ceramic's price (PM, 2026-10-22)

526's trace found `glass_raw_kg` opening in England at a price per kilogram tens of times ceramic's, which made it most of the
opening basket's value while it is a small share of what trades. A raw glass ask that high against its making cost is the ask
band failing to bound it, or the opening solve pricing it from a thin quote. Measure with `economy_api.agent_prices` against
`_material_prices` on an opened England game.
