# Zero-duration capabilities require a year boundary

**Type:** Interaction/timing mismatch  
**Priority:** Low
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `start_project` (`sim/engine/projects.py`) now completes a project immediately (`self._complete(k)`) when hours, calendar floor, cost and risk are all genuinely zero, instead of waiting for the next annual tick. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

`cap_measure_temp` had zero cost, zero founder-hours, zero calendar floor, and no failure chance, but its dependent capability remained unavailable until a turn boundary. A zero-cost platinum capability showed the same pattern.

## Suggested change

Complete truly instantaneous projects immediately, or label them as resolving at the next annual tick.
