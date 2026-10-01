# Portfolio bottlenecks cover only running work

**Status:** closed - `portfolio` carries a "waiting to start" section (`waiting_to_start`, `sim/engine/proto/portfolio_waiting.py`) grouping visible, prerequisite-met, unstarted work by the first kind `start_blockers` gives, and each running row carries `hours_effective_last_year` from the yearly snapshot's `project_hours_effective`. Test: `sim/tests/test_portfolio_waiting_and_last_year.py`.

Reported in Complaint 88.
