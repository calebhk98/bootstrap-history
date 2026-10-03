# round2_policy_hazards_options: two checks fail

**Status:** open

Two checks in `round2_policy_hazards_options` fail:

- "on a rich one it actually hires": the rich founder ends with no staff (staff 0.00, capital 2770693), so the auto-hire policy hires nobody.
- "england_1300: state full stays readable": the check on the full state screen for England fails (why was not read; the screen is the same size before and after the labour split).

Both fail identically at commit `12d8d0e` (after the package moves, before labour's two-way split) and after the labour split. They were not checked on `main` before the package split (`da86abf`), so whether they predate that work is unconfirmed.

Evidence: `python3 sim/test_regressions.py --only round2_policy_hazards_options` (slow: give it about 25 minutes).

What it would take: run the topic on `da86abf` first to place the regression, then read why auto-hire declines for a founder with ample capital, and what the England state-screen check measures.
