# Two affordability ceilings conflict

**Type:** Financial UI/rules inconsistency  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `sim/engine/proto/dispatch.py` now computes an aggregate `total_committed_across_active_work` from `committed_spend()`/`funding_capacity()`, explicitly built as "the real ceiling, not a second formula that could drift from it" - harmonizing the two checks this complaint found disagreeing. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

The blast-furnace warning advertised a 536,384-den “real ceiling” including cash, half credit, and five years of surplus income. Immediately afterward, adding 17,541-den crucible steel was refused because cash plus credit was 280,011 against 288,031 commitments.

## Suggested check

Either harmonize the checks or explain that one figure is an advisory long-term ceiling while the other is a strict start limit.
