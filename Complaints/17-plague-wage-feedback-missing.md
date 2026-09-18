# Announced plague wage shock is absent from economy and hiring

**Type:** Simulation/UI inconsistency  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `wage_index` is now a computed property driven by population shortfall (`WAGE_SCARCITY_ELASTICITY`), and `_refresh_demographic_indexes()` (`sim/engine/core.py`) is called immediately after a hazard fires specifically so "a shock's announced effects [are] visible immediately, not lag a step." See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

The Antonine plague event said wages would stay dear for ~92 years. Immediately after, `economy` still showed wage and price indices 1.000 with no 5/10-year movement; generic artisan and smith pay remained 250 and 281 den.

## Impact

Replacing general workers remained cheap, weakening the event and obscuring whether the promised macroeconomic feedback exists.
