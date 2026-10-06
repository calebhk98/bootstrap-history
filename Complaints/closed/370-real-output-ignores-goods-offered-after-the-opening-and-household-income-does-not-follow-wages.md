# Real output ignores goods offered after the opening, and household income does not follow wages

**Status:** closed - folded into 369

- A good households were not offered at the opening, that the home society now makes, enters the household demand model (`market_demand._household_demand_now`: the opening's goods and any home-made good are priced; a good only a partner offers stays out). It counts in real output at the price it was first offered at (`economy.introduction_prices`), in the quantity households want times the share of that demand the market cleared (`market_book[...]["cleared_share"]`). Labelled temporary: a chained basket (re-based each year, quantity index linked) would credit what a new good saves, not only its introduction price. Measured at the opening for Rome: Portland cement becomes demand once a producer runs its heat and kiln; the demand model's quantity for it is large (compare the opening value with `_fp/explore3.py`-style output), so its step in output per head is large; the model's quantity, not the mechanism, is the doubtful part.
- Household income is the opening's mean times what an hour of the unskilled trade pays now over the opening (`LabourMarket.household_wage_ratio`: scarcity of hands and the share of output gain pay passes on, `LABOUR_PAY_SHARE_OF_OUTPUT_GAIN`), before the price level and the cost of living, which the solver's prices carry. After a mortality shock Rome's wage ratio rises with the scarcity of hands and so does what households buy per head. Returns to land and capital are not yet in it (labelled).
- Real income (`Sim.household_real_income_ratio`) is income over the cost of the opening basket at today's prices: it rises when a technique that is run cheapens goods, and not when it is merely held.
- Society output no longer deducts soldiers under arms (it is the quantities cleared, which armies do not change).

Related: 101, 112, 369, 375.
