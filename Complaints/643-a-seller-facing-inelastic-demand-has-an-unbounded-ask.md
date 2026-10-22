# A seller facing inelastic demand has an unbounded markup, and a sold-out seller's ask ratchets

**Status:** partly fixed (asks are bounded and the sold-out raise stops at the band; within-year rounds where buyers switch sellers are not built)

- `seller_offers.py` gives the markup a seller that moves the price asks as elasticity over elasticity minus one, and
  infinity when demand is inelastic (the `math.inf` branch). Floors such as food are inelastic, so a seller that moves
  the clearing price searches the whole book for its best reservation (`seller_pricing.py`) with no cost anchor.
- A seller that sold out raises its ask by `SOLD_OUT_ASK_RAISE_SHARE` a year (`ask_raise.py`), while an unsold seller
  cuts by search. A good whose supply cannot respond climbs year after year (511: copper; 558: bronze).

What the established models do (`Complaints/reports/research-agent-based-economy-design.md`): Lengnick 2013 keeps each
seller's price inside a band around its marginal cost and moves it by inventory against target; Caiani et al. 2016 set
price as a markup on expected unit cost, nudged by inventory; Peters et al. set a cost-covering minimum. None gives a
seller the buyers' whole demand curve; strategic pricing is for a real single owner (550).

What it would take: a seller's ask anchored on its own unit cost, moved by its stock against its target, bounded on both
sides; the book search kept only for a producer that is the whole market; within-year rounds where buyers can switch
sellers (Lengnick, Caiani). Tests call the ask functions with built inventories: a sold-out seller's ask rises within
the band and stops; an inelastic book does not give an unbounded ask.

## Done

- `seller_offers.substitution_markup` no longer returns infinity; where buyers do not substitute more than one for
  one, `ask_raise.ASK_BAND_CEILING` stands in (a labelled temporary heuristic, `retire` this complaint, citing
  Lengnick 2013 eq 8-9 and Caiani et al. 2016 eq 3.6-3.7; no figure is claimed for it). `ask_band_multiple` is the
  derived markup, never past that ceiling. The width is derived only where buyers substitute; deriving it from the
  buyers' cheapest alternative priced from recipes is not built.
- The whole-book search (`seller_pricing.best_reservation`) stays for a one-workshop owner (an aggregate stands for
  many workshops and takes the price, 550) and its ceiling is now always finite, cost times the band.
- A sold-out seller's expected price (`producers.next_expectations`) rises through `ask_raise.raised_within_band`:
  one step, stopping at the band around the price that just covers a unit's cost, and no raise when no cost can be
  worked out.
- Tests: `test_economy_ask_band.py` (a sold-out ask rises within the band and stops after 500 sold-out years; an
  inelastic book gives a finite ask; a sole owner still raises its ask; an aggregate does not search),
  `test_economy_seller_markup_limit.py` (the stated band bounds the ask without substitution),
  `test_economy_aggregate_producer_pricing.py` (a single workshop raises within the band).

## Left

- Stock against target as the signal: only the sold-out half is built (next_expectations); a seller with stock left
  is cut by the unsold search, not by a stock target.
- Within-year rounds where buyers switch sellers (Lengnick, Caiani).
- Re-measure the spin-up: `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

## Charcoal's home ask far above its long-run price (PM, 2026-10-22)

`business_review_scenario`'s trace found charcoal's home ask at many times its long-run cost-covering price both before and
after the held rate (641), enough to drive a consumer concern's market factor to zero. The ask band should bound it. Measure
with `goods_market.home_unit_price('charcoal_kg')` against the long-run price on a default Rome game.
