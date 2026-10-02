# Merchants' terms still rest on labelled guesses

**Status:** open

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

`python3 sim/foreign_trade_report.py --years 100 --partner han_china_100ad`: cloth imports rise
to thousands of tonnes a year as the fleet grows, limited by lift, not by capital; compare the
earlier figures in `Complaints/346`.

Related: 346, 339.
