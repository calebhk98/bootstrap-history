# Farm and school quotes compute their price apart from the purchase, and most quotes are untested against the charge

**Status:** partly - farm and school price now come from one engine function each (`farm_price_per_hectare`, `trade_school_price_per_seat`) and test `quote_matches_charge` holds every buy target, hire fee, commission, train and bounty to its quote; the hire yearly wage (Complaint 356), and open, research and project bills are not yet in that table

`quote farm` computes `FARM_COST_PER_HA * price_index` in `sim/engine/proto/quote_purchases.py` and `invest_farm` recomputes it in `economy_goods.py`; `quote school` and the school purchase (`labour_population.py`) do the same. They agree today; nothing makes them. Quotes round ad hoc in each quoter. The quote-equals-charge test (`test_complaint_61_quote_matches_purchase`, by its current name) covers forest, nitre, mine and similar purchases only, not farm, school, hire wages or research and project bills.

Fix: one engine function per price that both the quote and the action call (a `quote_for(kind, arguments)` returning price or refusal), and one parametrised test that every command with a quote is charged exactly what it quoted.
