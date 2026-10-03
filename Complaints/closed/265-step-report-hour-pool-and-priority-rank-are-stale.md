# RUNNING lines quote last year's hour pool ("sharing this year's 200 directed hours") and "priority #9 of 9" counts finished work

**Status:** closed

B (107 AD and 129 AD): after a new year began with 2,000 hours free, RUNNING still said "sharing this year's 200 directed hours"; the step report showed "priority #9 of 9" while `priority` listed five active projects.

Cause, by code reading: `_work_description` (`sim/ui/proto/state.py`) reads `pool_rank_this_year`, `pool_active_count_this_year` and `pool_total_this_year` from the progress record written inside `step()` when hours were allocated; nothing refreshes them when a project finishes or the pool changes later, and the rank is the allocation-time rank. Not reproduced in a short script here (the projects I started finish inside one year); needs a played game. The tester's two observations fit one stale bookkeeping cause.

What it would take: compute the rank and pool at render time from the live active list (or say "last year"). Related: 88, 99.


Found in the final blind playtests of this branch (Rome 100 AD fog, won 301 AD; B bugs 6 and 7 (code reading only)). Reports: `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
