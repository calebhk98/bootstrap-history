# The cached price-table lookup is not "well under" rebuilding the done set

**Status:** open

`python3 -m sim.tests --only complaint_141_year_cost` fails "a cached price-table lookup costs well under
rebuilding the done set". The check wants lookup time below half of rebuild time
(`sim/tests/test_complaint_141_year_cost.py` around line 85). Measured alone on an idle machine, the
lookup takes about 0.53 of the rebuild on this branch and about 0.54 on main (`bcd8b65`).

Why it matters: either the cache got slower, or the done set got cheaper to rebuild and the check's ratio
no longer means anything. A timing check that fails on an idle machine will also fail under load.

What it would take: time the lookup against the uncached computation it replaces, not against an
unrelated rebuild. Or assert on a counted operation instead of wall time.
