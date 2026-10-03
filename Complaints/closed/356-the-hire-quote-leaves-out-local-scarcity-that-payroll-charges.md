# The hire quote leaves out the local scarcity that payroll charges

**Status:** closed - pinned by sim/tests/test_one_labour_market.py

`quote hire` gives the yearly wage with `annual_wage(trade, include_local_scarcity=False)` (`sim/ui/proto/quote_spending.py`), while the year-end payroll charges `annual_wage(trade)` with the scarcity premium (`sim/engine/core_step_phases.py`) and the `labour` screen shows the premium-included figure. Whenever a trade's `labour_price_factor` is above one, the quote understates what the player will pay.

Fix: the quote and the payroll call one function; extend the quote-equals-charge test to the hire wage.
