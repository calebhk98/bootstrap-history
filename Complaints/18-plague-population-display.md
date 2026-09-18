# Population screen does not reflect announced plague losses

**Type:** UI/model consistency  
**Priority:** High
**Status (project-wide audit, 2026-09-18): PARTLY RESOLVED / LIKELY.** Population is now real simulated state (the age-cohort model, Milestone 4), not a cosmetic constant, and is refreshed immediately on a hazard via the same `_refresh_demographic_indexes()` call `Complaints/17` names. The `population` command's exact display text after a live plague was not independently re-run this session. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

The event reported approximately -27% empire population, but `population` continued to show 65,000,000 country population and 12% urban / 7.8m urban baseline.

## Suggested change

If these are reference values, label them clearly. Otherwise apply/show current population and derived urban counts.
