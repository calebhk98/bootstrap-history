# Generic artisans can supervise unrelated advanced concerns

**Type:** Balance / simulation concern  
**Priority:** Medium
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `venture_foreman()` (`sim/engine/projects.py`) now retains "the largest non-generic skilled contribution as its operating foreman" rather than letting interchangeable generic hands supervise a specialised concern - the foreman/manager requirement suggested here. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

Seven cheap generic artisans enabled distillation and plate-mirror ventures, while generic crafts also appeared usable for paper, farming, metallurgy, and optics. This produced a large income jump.

## Risk

Specialist gating matters during research/building but becomes weak during operation; diversified industrial scaling can become too cheap.

## Suggested review

Confirm this is intended. Consider profession-specific supervision or foreman/manager requirements for advanced concerns.
