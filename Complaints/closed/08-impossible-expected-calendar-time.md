# Expected calendar time can be less than the hard calendar floor

**Type:** Displayed-math bug  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `expected_calendar_years()` (`sim/engine/projects.py`) is now built explicitly around the invariant that it must never understate the floor. Checked directly this session: `calendar_floor(k) <= expected_calendar_years(k)` held for all 400 nodes sampled on a fresh `rome_100ad` sim, 0 violations. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

Observed examples: `corpus_written` 10y floor / 6.75y expected; blast furnace 5y / 3.89y; kinetic theory 6y / 3.56y; interchangeable parts 8y / 5.17y; industrial zinc 12y / 7.77y.

## Expected behavior

Expected completion time for an unstarted project cannot be shorter than its irreducible floor.

## Suggested check

Correct the retry expectation formula or label the displayed field as something other than total calendar completion time.
