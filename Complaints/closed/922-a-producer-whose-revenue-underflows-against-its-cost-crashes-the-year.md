# A producer whose revenue underflows against its cost crashes the year

**Status:** fixed (`sim/economy/producers.py` `_standard_score`; regression test `sim/tests/test_share_working_extremes.py`)

`share_working` and `working_cost_ratio` judge how many of a producer's workplaces the expected revenue covers from the log of
revenue over cost. Both guard a revenue or a cost at or below zero, but not a positive revenue so small against the cost (or a
cost so large, up to infinite) that the ratio underflows to zero: `math.log` then raises `ValueError: math domain error` and the
year stops. The base build has the same code and crashes the same way; it surfaced when the long equivalence tier (4 scenarios,
100 years) was first recorded on the base.

Fixed: an underflowed ratio scores below every workplace's cost (minus infinity), which is the answer both callers already give
for no revenue: no workplace works, and the working cost is the producer's own. Elsewhere nothing changes. For the long tier the
same patch is applied, uncommitted, to the base checkout the tier is recorded on (`docs/architecture/baseline/README.md`).
