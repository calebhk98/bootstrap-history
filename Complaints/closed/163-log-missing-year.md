# `step 2` printed only the first year's events and `log` shows nothing for the second

**Status:** closed - measured: not a bug. `step N` logs and prints exactly what N single steps do (test_multi_year_step_log); the 'population still N% below trend' line is throttled in core.py `_refresh_demographic_indexes`, so it does not appear every year

From 106 AD, `step 2` printed only "DURING 106" lines and landed on 108 AD. `log limit:12` has no 107 AD entries at all, not even the "population still N% below trend" line every other year logs.

Unverified whether 107 was truly empty; worth a check that multi-year steps log every year.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
