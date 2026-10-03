# The labour market prices housing from the founder's household, and three wage uses skip its cost factors

**Status:** closed - the housing term reads the town (everyone employed in it against its spare dwellings, `LabourMarket.town_housing_factor`), and commission, bondage and the workshop read the market quote; pinned by sim/tests/test_labour_market_town_pricing.py

`LabourMarket.quote` (`sim/labour/labour_market_api.py`) multiplies the schedule wage by `wage_cost_factors`, whose housing term is the founder household's occupancy of its own places. Every employer is quoted that one figure, but it is a fact about one household, not about the town's housing. Separately, `commission_cost`, the bondage repayment rate and the workshop's output value take the schedule hour in today's money (`in_current_money`) without the cost factors, the scarcity premium or the output pay scale a hire pays, so a commissioned hour and a hired hour of one trade are priced by different rules.

What it would take: a town-level housing factor not read off one household, and commissions, bondage and the workshop reading `quote` (with the commission premium applied to it). That moves the founder's own numbers, so it needs its own fingerprint run.
