# Merchants' terms still rest on labelled guesses

**Status:** in progress. Done under the owner decision: a hull's crew is derived from its rig,
watches and helm (`sea_freight.crew_to_sail`) instead of a stated crew; the crew's and animals' food and
water ride as cargo mass (`provisions.delivered_share`) and are charged per tonne delivered on each
foreign route leg and on domestic hauls; robbery falls with crew size (`sea_freight.boarding_loss_share`,
`hull_loss_per_thousand_km`, a labelled heuristic for raiders' numbers and meeting rate, replacing the flat hull
loss); coin carried to pay for a cargo already weighs through `coin_hoard.coin_carriage_units`
(Complaint 273). `test_freight_provisions` pins land-versus-sea grain reach from the freight function.
Remaining: crew as a choice (extra defenders against the cost of losses), the sea crew still sums
to the rig's need only, `MONOPOLY_MARKUP_SHARE`, `AGENTS_PER_CARRIER`, one merchant per carrier, the wait
counting sailings only, the class's capital from `MERCHANT_DENSITY`, retained earnings from the households'
saving share. Carried provisions are floored at the cargo-loss cap rather than priced as impassable, and
routes are still chosen on per-km rates before provisions are charged.

Complaint 346 derived merchants' wait, agents' cost, markup, speed and capital from the fleet,
the labour market and the capital market. What is left is stated, not derived:

- `MONOPOLY_MARKUP_SHARE` (`sim/world/merchant_terms.py`): the lone merchant's markup is the
  inverse of the destination market's price elasticity, which no model supplies per route.
- `AGENTS_PER_CARRIER`: a factor at each end; a house's real staffing is not modelled.
- Merchants number one per carrier; a merchant owning several, or a carrier shared, is not modelled.
- The wait counts sailings only; the time to sell a cargo into a market's demand and a sailing
  season are not modelled.
- The class's capital is the modest-merchant kit times `MERCHANT_DENSITY`, both authored guesses;
  lenders' room is read without the merchants' borrowing being added to the pool's loans.
- Retained earnings use the households' saving share.

## Evidence

`python3 sim/foreign_trade_report.py --years 100 --partner han_china_100ad` (script since removed; recover with `git show 97473f1:sim/foreign_trade_report.py`): cloth imports rise
to thousands of tonnes a year as the fleet grows, limited by lift, not by capital; compare the
earlier figures in `Complaints/346`.

Related: 346, 339.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 346 (`closed/346-merchant-terms-and-ornament-limit-are-heuristics.md`): merchant terms are derived; the remaining heuristics are listed here, ornament held stock is in 442.

Owner decision (2026-10-09): derive the merchants' terms instead of stating them: crew per ship from what the ship needs to sail and defend itself, food and water for the crew and animals over the voyage, the mass of the cargo and of the coin carried to pay for it, and the risk of robbery against crew size. Done right, heavy cheap goods (grain) only move a few tiles by land, because the carriage or the animals' feed eats the value, while a ship moves the same grain much further at a lower cost per kg.
