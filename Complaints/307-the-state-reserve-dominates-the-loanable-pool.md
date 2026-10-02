# The state's unbounded reserve (Complaint 286) is most of the loanable funds, so the market rate drifts down for a reason that is not saving

**Status:** partly - the state's reserve is bounded (Complaint 327), so it no longer floods the pool; the lent share is still a labelled guess, not a policy decision

`Government` accumulates a reserve every year in surplus (Complaint 286) and the loanable-funds market counts `LENDABLE_RESERVE_SHARE` of it beyond a year's need as supply (`sim/engine/economy_capital_market.py`, `market_funds`). The first meeting fixes the reference balance with no reserve; as the reserve grows the supply grows and the market rate falls below the starting rate for the whole run (measure: each decade's `market_rate()` in a 150-year Rome or Han game). It is a real effect of the mechanism and also a symptom: a state that hoards and never spends or lends is not a measured behaviour, and the reserve share that is lent is a labelled guess. Fix 300 first (more standing lines), then replace the share with the state's own lending decision through a policy, as a firm or the founder would make it.

The state borrows only when its need exceeds its revenue and reserve, which no baseline civilisation does; the borrowing path is exercised by a stress army (`standing_army` raised several times) and `sim/tests/test_capital_market.py`.

Update: the discretionary sweep is gone (Complaint 327). A reserve beyond `RESERVE_CEILING_YEARS_OF_NEED` years of need buys works, so the reserve stays within a small multiple of the need and the state's supply stays a small share of the pool; measure with `python3 sim/budget_series.py <civilisation id> <years> <seed>` (works and discretionary lines) and each decade's `market_rate()`. Left: replace `LENDABLE_RESERVE_SHARE` with the state's own lending decision through a policy.

Related: 106, 308, 332.

Owner decision (2026-10-02): can be ignored for a while.
