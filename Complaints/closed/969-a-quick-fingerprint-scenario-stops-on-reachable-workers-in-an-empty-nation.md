# A quick fingerprint scenario stops on reachable workers in a nation of no people

**Status:** closed - the reach figures are the year's clearing's and outlived later deaths; `supply_hours` now bounds them by the working people alive (unconfirmed against the failing scenario: the fingerprint was not run)

Recording the quick fingerprint (`python3 -m sim.tests.fingerprint record --quick --jobs 2 OUT.json`) on the merge of
PR #112 plus the log-line `cause` fix stopped partway through with:

    AssertionError: reachable lime_burner 0.01 exceed the nation of 0.0

raised by `check_labour_market_invariants` (`sim/engine/invariants.py:60`, the assertion at :73), called from `verify_step_invariants`
(`sim/engine/year_steps.py:39`) at the end of a year. The traceback does not name the scenario; it is one of
`QUICK_SCENARIOS` in `sim/tests/fingerprint.py` (Rome seeds 1 and 2, Han China seed 1, England seed 1, a hundred years
each). It surfaced only after the log-line crash was fixed, so it may have been hidden behind that one before.

Two readings fit and neither is checked:
- the nation's population really reached zero and the reachable-workers view keeps a remainder for a trade
  (a fraction left after people are removed, or a figure carried from an earlier year);
- the population view reads zero for a nation that still has people (a seat or country read through the wrong scope).

Why it matters: the year stops, so a long game can end in a crash; and the fingerprint, the check that proves a refactor
leaves the game unchanged, cannot record a baseline while it fails.

What it would take: run each quick scenario alone with `python3 -m sim.tests.fingerprint record --quick --jobs 1` (or a
small driver over one scenario) to find which one fails and in which year, save the game the year before, then read
`population` and `reachable_trade_population` there. A regression test then calls the view's rule on that state. Note
that a quick fingerprint takes over twenty minutes on a four-core machine, so it is a long run under CLAUDE.md section 1.

## Cause found from the code

`Supply.market_supply` (and `labour_supply_block.reach_block`) built the reachable figure from the hours households offered at the
year's clearing and the core's people of the trade; both are written in the `market` phase. The phases after it (`random_events`,
`world_hazards`, `campaigns`, `revolts`, `famine_watch` in `sim/engine/year_phases.py`) can kill people through demography's
`kill_people`, which lowers the nation, but nothing bounded the kept figures by the working people alive. The invariant at the end of
the year then read a nation of nearly nobody against the earlier reach. `trade_supply_rules.supply_hours` now also takes
`people_alive` (the nation's working age). Regression: `sim/tests/test_trade_supply_rules.py`.
Not reproduced in a game; a fingerprint quick record would confirm.
