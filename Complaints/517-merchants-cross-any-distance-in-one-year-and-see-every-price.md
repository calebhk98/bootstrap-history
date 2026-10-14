# Merchants cross any distance in one year and see every market's price

**Status:** open

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
