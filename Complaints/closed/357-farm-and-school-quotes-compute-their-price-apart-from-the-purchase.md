# Farm and school quotes compute their price apart from the purchase, and most quotes are untested against the charge

**Status:** closed - farm and school price come from one engine function each, and test `quote_matches_charge` holds every buy target, hire fee and yearly wage, commission, train, bounty, open, research and project bill to what the cash ledger shows debited

`quote farm` computes `FARM_COST_PER_HA * price_index` in `sim/ui/proto/quote_purchases.py` and `invest_farm` recomputes it in `economy_goods.py`; `quote school` and the school purchase (`labour_population.py`) do the same. They agree today; nothing makes them. Quotes round ad hoc in each quoter. The quote-equals-charge test (`test_complaint_61_quote_matches_purchase`, by its current name) covers forest, nitre, mine and similar purchases only, not farm, school, hire wages or research and project bills.

Fix: one engine function per price that both the quote and the action call (a `quote_for(kind, arguments)` returning price or refusal), and one parametrised test that every command with a quote is charged exactly what it quoted.
