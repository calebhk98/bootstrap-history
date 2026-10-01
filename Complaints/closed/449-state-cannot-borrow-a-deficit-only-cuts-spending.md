# A state in deficit can only cut spending: it cannot borrow

**Status:** closed - a deficit is borrowed up to the state's credit ceiling before any line is cut, and interest is booked as an outlay the next year (`sim/tests/test_capital_market.py`, the state section)

`Government.pay_standing_need` (`sim/engine/actors/government.py`) pays the standing need from the purse and, when the purse is short, cuts every line by the same share (`budget.funded_share`). A real state in a bad year borrows, debases or sells office. The place to add credit is between the revenue being credited and `funded_share` being computed: the state would draw a loan up to what lenders will give against its revenue, and next year's `standing_lines` would carry interest on it as a line like any other (`budget_lines.py` shows the pattern: people at wages, goods at the market's price, or here money owed).

Until then the only responses to a deficit are a smaller army (at `ARMY_ADJUSTMENT_RATE`), unpaid lines, and the need-driven levy on the visible founder. Check: `python3 sim/budget_series.py norse_900ad 100 1` shows the unfunded share and the levy rate year by year.
