# A failed step leaves a half-run year, and the protocol saves it

**Status:** open

Found closing 582. When a phase raises partway through a year, the phases before it have run, the year counter has not
advanced, and the agent protocol saves the game after the failed command; the next step then runs those phases
again. In the playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`) a step failed and the retry succeeded, so a year was partly run twice without the
player knowing.

What it would take: a year either completes or leaves the saved game as it was (run the year on a copy, or roll back
the save on an exception, or do not save after a failed step), and the reply says the year did not run, with a
`cause`. Test: a phase that raises leaves the save unchanged and the next step runs the year once.
