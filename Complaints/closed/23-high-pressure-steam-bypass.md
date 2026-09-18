# High-pressure steam bypasses its intended prerequisite chain

**Type:** Tech-tree realism defect  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `en_high_pressure_engine`'s prerequisites in `data/tech_tree.json` now include `steam_high_pressure`, `thermodynamics_theory` and `mat_bulk_steel`, not only the capability rungs named here. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

`en_high_pressure_engine` was legal with boring mill, 1300 C, and 10 µm tolerance, while the main visible path required thermodynamics, atmospheric steam, Watt development, bulk steel, and further high-pressure work.

## Suggested review

Confirm this is a deliberate alternate route. If not, add thermodynamics/material/boiler safety prerequisites.
