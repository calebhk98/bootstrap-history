# Merchants cross any distance in one year and see every market's price

**Status:** partly fixed. Travel time and news lag are in (below); chains of merchants working a stretch they know, and the before/after measure of traded tonnes by route length, stay open.

`sim/economy/merchants.py` lets a merchant buy in any market area and carry to any other in one step. Carriage is
charged per tonne by mode and distance (`tile_costs.carriage_table`), which is right, but the rest of the trip is
not: goods bought one year are sold the next whatever the distance, so a haul across a continent ties up money and
loses to spoilage for one year, the same as a haul to the next town; and every merchant reads every area's price
(`expected_price` falls back to `view.price` for any area).

Historically long-distance trade went through many hands, each trader working a stretch they knew, and only goods
with a high value per kilogram (silk, spices, metals) travelled far. Carriage per kilogram does most of that
filtering already; transit time and local knowledge do the rest.

What it would take: transit time from the route's distance and mode, so interest and spoilage grow with the
journey (a long haul spans years); merchants that know prices only where they trade or have recently been (or
hear them with a lag through neighbouring markets, which 488's belief model would generalise), so long routes are
covered by chains of merchants rather than one. Measure before and after: the share of traded tonnes by route
length, by value per kilogram.

## Done: travel time and news lag

- `CarriageTable.days_between` (`sim/economy/tile_costs.py`): the days of the cheapest haul, from geography's
  per-mode pace.
- `sim/economy/merchants_transit.py`: a haul is held for the whole years its days span (at least the one year
  every merchant already holds goods). A longer haul leaves the merchant's stock for the transit account
  (`edge:transit`) and reaches the destination tile in the year its days put it in; each year on the road
  spoils the good at its yearly rate. `Merchant.in_transit` and the account are saved state; the shipments
  count toward the merchant's wealth and toward the destination's supply when it sizes bids.
- `merchants.orders` weighs the haul's years: interest and spoilage for each, so a gap that pays for one year
  can fail for two. Financing is real: the money stays tied up and the merchant borrows it again.
- News: a merchant learns a distant market's price as many years late as the haul there is held beyond the
  first (`Merchant.price_history`, `close_year(lag_years=)`), measured from its home tile. A market it has no
  expectation of and whose news has not arrived is unknown to it, not read from the view.
- Tests: `sim/tests/test_merchant_travel_time.py`.
- Still open: volumes are not lagged; whole-year steps (a 300-day and a 10-day haul both count one year);
  the haul's mode is the cheapest path's, not chosen for speed; no measurement yet of tonnes by route length.
