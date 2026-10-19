# Start accepts a project whose trade does not exist, and it fails a year later

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed7-agent-100-years-log.md`). Around 130 AD,
`start precision_three_plate` replied `ok` while no machinist existed in the society; the next step reported
`major_project_failure ... no machinist here` and stopped the multi-year step early. Training machinists takes longer
than the project's first year.

Why it matters: a refusal the game already knows at `start` arrives a year later as a failure that costs money and
time; an agent cannot plan around it. Every check a project will fail on its first year should be a refusal with a
`cause` at `start` (`sim/engine/projects_starting.py`), or `start` should say the project will wait for the trade.

What it would take: find the staffing check that fails in the year (`major_project_failure`) and run the same check
at `start`, refusing with the same `cause`, or queueing the project until the trade exists and saying so. Test: a
project needing a trade nobody holds is refused at `start` with that cause.
