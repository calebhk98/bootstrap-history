# Agent-economy fixes from the economy review have tests outside the suite

**Status:** closed - the scratch tests are in sim/tests as test_economy_<topic>.py; the two that drove whole games through the deleted validator were cut to their unit parts (metal_gap_timing) or dropped (routes_equal, a one-off old-against-new comparison)

The second round of agent-economy fixes (cobweb, entry on price, rent damping, the mint metal gap, speed; see Complaints/reports/agent-economy-review.md) was made while only `sim/economy/` could be edited. Their regression tests were written and run as scratch unittest files outside the repository, so the suite does not hold them.

What it would take: copy the test sources recorded in the review report into `sim/tests/test_economy_<topic>.py` once `sim/tests/` can be edited, and run them with `python3 -m sim.tests --only economy_<topic>`.
