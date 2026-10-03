# First-attempt failures looked higher than the displayed FAILURE RISK (unproven, one seed)

**Status:** closed - measured: matches; the displayed figure and the roll are the same call, now pinned by a test

By 121 AD on seed 1, 7 of 25 projects failed on the first attempt where the displayed risks summed to ~3.2 expected (P(>=7) roughly 4-5%). In 119 AD three projects at 20%, 12% and 15% all failed in the same year.

This may be one unlucky seed. What it would take: a many-seed check that realised first-attempt failure rates match the figure shown at `start`/`why` (e.g. whether reputation or opposition multipliers apply at roll time but not in the displayed figure).

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

**Resolution (measured: matches).** `why`/`start`/`available` read `effective_risk` (sim/ui/proto/techtree.py, `_explain_timing_and_risk` and `_brief`) and the completion roll is `rng.random() < effective_risk(node_id)` (sim/engine/projects_completion.py, `_complete`); reputation, opposition and staffing multipliers do not touch either, only retry learning and the process-controller relief do, and both are inside `effective_risk`. The roll happens once per attempt. Empirical check: 1,500 seeds each on 6 nodes with 5-25% displayed risk, `_complete` called with the real generator, gave 1,199 first-attempt failures against 1,170 expected (standard deviation about 30). Note for anyone repeating it: seeding `random.Random` with consecutive small integers (0, 1, 2, ...) makes the first draw run about 15% high (measured: 474 failures against 400 expected on 3,200 rolls), so draw seeds from a master generator. The seed-1 playtest run was most likely an unlucky draw. Pinned by `python3 sim/test_regressions.py --only failure_roll_matches_display` (a draw just under the shown risk fails, just over succeeds, on first and later attempts).
