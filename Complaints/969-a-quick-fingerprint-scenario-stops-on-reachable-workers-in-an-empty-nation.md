# A quick fingerprint scenario stops on reachable workers in a nation of no people

**Status:** open

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
