# Trade-hours status falsely reports machinists as booked

**Type:** Status/constraint bug  
**Priority:** High
**Status (project-wide audit, 2026-09-18): PARTLY RESOLVED / LIKELY.** `craft_hands_available()` (`sim/engine/labour.py`) already folds contract hours into a trade's availability ("a year of a carpenter's time IS a carpenter"), which closes the general class of bug described here (a project's own staffing gate disagreeing with `portfolio`'s allocation numbers). The specific machinist repro was not independently reproduced this session. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

`master_screw` and later `micrometer_gauges` said machinist hours were booked elsewhere despite `portfolio` showing demand below supply, `oversubscribed: false`, and no competing machinist project. The project later progressed normally.

## Impact

A player may hire/train unnecessary workers or incorrectly stop a viable project.

## Suggested check

Make the per-project waiting reason use the same allocation data as `portfolio`; add a regression test for demand < supply.
