# A sliver of shortage sends a trade's expected income to its highest bid

**Status:** closed. The clearing's heading wage (`target_wage`, `clear_one` in `sim/labour/market/clearing.py`) now moves from the settled wage toward the clearing target by `pressure`, the same imbalance scaling `market_wage` applies, so `income_at_graduation` rises with the shortfall instead of jumping to the top bid. Function test: `ExpectedIncomeIsContinuousAcrossBalance` in `sim/tests/test_labour_core_skilled_ceiling.py`.

Found while testing the skilled-labour ceiling (`sim/tests/test_labour_core_skilled_ceiling.py`). In a built labour
market where a trade is very slightly short of hours, `income_at_graduation` (`sim/labour/market/expectations.py`)
reads the trade's heading wage at the employers' maximum bid, so a trade short by a sliver looks as rewarding to an
entrant as one short by half. Entrants and switchers then leave other trades (smiths, in the test that found it) for
it. The test avoided the case by giving the short trade slack bids.

Why it matters: a jump in the incentive at the point of balance makes trade choice flip between trades from year to
year, the cobweb shape Complaint 651 removed from the wage itself, and it can drain a trade the economy needs.

Measure: build two markets that differ only in a tiny shortfall of one trade's hours and compare `income_at_graduation`
for that trade; it should move by about as much as the shortfall, not to the bid maximum.

What it would take: the heading wage an entrant expects follows the clearing rule's own partial adjustment (the share
of the gap closed per year, `market_wage` / `pressure` in `sim/labour/market/clearing.py`), so it is continuous in the
shortfall; a function test on built inputs that the expectation is continuous across balance.
