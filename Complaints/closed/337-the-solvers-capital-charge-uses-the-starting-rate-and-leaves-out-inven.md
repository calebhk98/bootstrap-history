# The solver's capital charge uses the starting rate and leaves out inventory

**Status:** closed - folded into 335

`solved_prices` takes the civilisation's starting rate unless a caller passes `interest_rate`; nobody passes the live rate (`Sim.market_rate`), because every move of the rate would re-solve the price vector (a cache key per rate). Inventory (stock held between making and selling) and working capital in inputs carry no interest either. Both belong with the capital-markets work: a banded rate in the cache key, and a holding period per material stated by its physical keeping, not a flat figure.

Related: `Complaints/319`, `Complaints/329`, `Complaints/283`.

Related: 140, 295, 317, 318, 335, 336.
