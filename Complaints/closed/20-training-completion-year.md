# Training “ready in YEAR” is ambiguous

**Status:** closed

**Type:** Wording clarity  
**Priority:** Low
**Audit (2026-09-18): RESOLVED, verified.** `sim/engine/labour.py` now says trainees "finish training during %d's annual resolution and join your staff automatically... Until then they cannot do a day of the work" - the exact clarification suggested here. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

Workers marked ready in 186/187 only became usable during the associated annual resolution, effectively at the following year's opening.

## Suggested change

Use “finishes during YEAR” or state explicitly whether trainees are available at the start or end of that year.
