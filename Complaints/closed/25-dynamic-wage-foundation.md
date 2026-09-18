# Wages need an endogenous cost-of-living foundation

**Type:** Economic-demographic simulation depth  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `wage_cost_factors()` (`sim/engine/labour.py`) now builds a wage from food/housing/tool-input price factors plus a fixed skill-and-difficulty share ("forty-five percent is subsistence food, twenty percent housing, ten percent tools/consumables, and twenty-five percent that fixed skill/difficulty premium") - exactly the structure requested here. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player concern

Trade wages appeared to be fixed catalogue numbers rather than outcomes of
what workers must pay for food, housing, and the tools or consumables of their
job. That makes cheaper essentials or expanded housing fail to reduce labour
costs, while material scarcity does not reach the workers who must maintain
their own equipment.

## Why it matters

Wages are one of the principal checks on industrial expansion. If only a global
multiplier or a hard-coded trade table can move them, improvements to food and
housing do not feed back into household costs and different jobs lack an
explainable economic basis.

## Expected behavior

Keep historically calibrated trade differences for skill, difficulty, hazard,
and training, but build the current wage from visible food, housing, tool-input,
general demographic-scarcity, and local trade-scarcity components.
