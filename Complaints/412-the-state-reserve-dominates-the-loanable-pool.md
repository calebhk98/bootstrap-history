# The state's unbounded reserve (Complaint 300) is most of the loanable funds, so the market rate drifts down for a reason that is not saving

**Status:** open - found while building 110; follows from 300

`Government` accumulates a reserve every year in surplus (Complaint 300) and the loanable-funds market counts `LENDABLE_RESERVE_SHARE` of it beyond a year's need as supply (`sim/engine/economy_capital_market.py`, `market_funds`). The first meeting fixes the reference balance with no reserve; as the reserve grows the supply grows and the market rate falls below the starting rate for the whole run (measure: each decade's `market_rate()` in a 150-year Rome or Han game). It is a real effect of the mechanism and also a symptom: a state that hoards and never spends or lends is not a measured behaviour, and the reserve share that is lent is a labelled guess. Fix 300 first (more standing lines), then replace the share with the state's own lending decision through a policy, as a firm or the founder would make it.

The state borrows only when its need exceeds its revenue and reserve, which no baseline civilisation does; the borrowing path is exercised by a stress army (`standing_army` raised several times) and `sim/tests/test_capital_market.py`.
