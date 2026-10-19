# A failed step leaves a half-run year, and the protocol saves it

**Status:** closed. A step snapshots the game before each year (`sim/ui/proto/step_atomic.py`) and restores it if the year raises; the reply carries `cause` `year_failed` and `exception_kind`, and a multi-year step keeps the years before the failure. Test: `sim/tests/test_complaint_587_atomic_year.py`.

Found closing 582. When a phase raises partway through a year, the phases before it have run, the year counter has not
advanced, and the agent protocol saves the game after the failed command; the next step then runs those phases
again. In the playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`) a step failed and the retry succeeded, so a year was partly run twice without the
player knowing.

What it would take: a year either completes or leaves the saved game as it was (run the year on a copy, or roll back
the save on an exception, or do not save after a failed step), and the reply says the year did not run, with a
`cause`. Test: a phase that raises leaves the save unchanged and the next step runs the year once.
