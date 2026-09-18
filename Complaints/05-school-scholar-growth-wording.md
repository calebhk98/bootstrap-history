# School “+2 scholars/year” wording misstates the visible effect

**Type:** Tooltip clarity  
**Priority:** Medium
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `data/branches/00_core.json`'s `school_founded` note now says explicitly: "Grants +4 scholars immediately and adds capacity for +2 scholars per year to the household training pipeline thereafter; this raises the reachable staff pool and deputy capacity, not the school headline count. Graduates become usable as hiring and training fill that capacity." See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

After opening the school, its headline scholar count remained 5 across several years despite text promising “+2 scholars/yr.” Population/reachable pools and deputy capacity did increase.

## Suggested change

Specify where the annual scholars are added (national pool, reachable market, deputies, or household) and when they become usable.
