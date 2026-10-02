# The scholar-wall slow check needs 250 simulated years, and the late years are the expensive ones

**Status:** closed - the 250-year slow check is replaced by a one-step check of the clamp, proven to fail with the clamp removed

`people_attrition_scholars` has a slow check (`auto_hire never grows scholars past the wall hire() enforces ...`) that runs a rich Rome household for 250 years. A year costs a fraction of a second early and many seconds from about year 100 onward, so the check runs for tens of minutes even after the Complaint 141 fixes. Shortening it was tried: stopping at the first year scholars pass ten (about a century in, a few minutes) does not fail when the `min(..., literate_capacity("scholar"))` clamp in `core_step_phases.py` is removed, because `hire()` enforces the wall too and the overshoot the clamp prevents only shows much later. So the short horizon loses the thing the check exists for, and the check was left unchanged.

Why it matters: this single check keeps `--slow` from finishing in minutes.

What it would take: either a test of the clamp that does not need a run (build the household state at a late-game shape directly, one `step`, and assert the target the clamp produces), or a cheaper late-game state to start from. Prove any replacement by removing the clamp and watching it fail.

## Done

`sim/tests/test_people_attrition_scholars.py` now records the scholar headcount
`auto_hire` asks for in one step (the last `_stochastic_round`) with the wall
already reached, and asserts it does not exceed the wall; a second case with an
open wall shows the same household does ask for more. With the
`min(..., literate_capacity("scholar"))` clamp removed the first check fails
(asked 2.27 against a wall of 2); restored, it passes. The widening of the wall
by institutions stays covered by the existing fast check beside it, and the
250-year slow check was deleted.
