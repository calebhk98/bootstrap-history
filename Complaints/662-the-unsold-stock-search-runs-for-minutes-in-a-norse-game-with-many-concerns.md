# The unsold-stock search runs for minutes in a Norse game with many concerns

**Status:** open

`sim/tests/test_staff_closure_reopening_scenario.py` (a Norse game with many concerns and `auto_hire`, moved
unchanged out of `arrears_hours`) steps its first years in seconds, then one further year runs for minutes. A
faulthandler dump taken while it runs shows the time in `sim/economy/unsold_search.py` (`_unsold`, `trial`,
`clear_with_search`) calling `goods_market._crossing` over and over: the search for the price at which unsold stock
clears does not converge quickly, or is re-run per seller, in some state this game reaches.

Measure: `python3 -m sim.tests --slow --only staff_closure_reopening_scenario` (times out), and
`python3 -X faulthandler` with `faulthandler.dump_traceback_later` around a `step()` of that scenario's game.

Why it matters: a year that takes minutes in one reachable state makes a whole game unplayable there (497), and the
scenario that guards staff-closure reopening cannot run.

What it would take: capture the inputs of the slow `clear_with_search` call from that game (pickle them), write a
function test that times it and counts `_crossing` calls, find why the search's iteration count explodes (a bracket
that does not shrink, a fallback that restarts, a seller loop that is quadratic), and bound it by its own rule, not by
a cap on years in the scenario.
