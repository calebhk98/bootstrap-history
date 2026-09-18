# Active and permanent institution benefits are conflated

**Type:** Tooltip/state clarity  
**Priority:** Medium
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `sim/engine/proto/techtree.py` now returns explicit `permanent_on_completion` and `only_while_open` fields, replacing the single ambiguous "KEEP THIS OPEN" line - the exact two-group split suggested here. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

`corpus_written` and sanitation affected `risk` while closed, but `state` said an associated benefit was inactive. The generic “KEEP THIS OPEN” language reads as though all benefits disappear. Similar ambiguity appeared for closed collegium/freedman institutions satisfying future prerequisites.

## Why it matters

Players cannot reliably decide whether upkeep is required for a hedge, a prerequisite, standing, capacity, or only a subset of benefits.

## Suggested change

List benefits in two explicit groups: **permanent on completion** and **only while open**.
