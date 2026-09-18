# A shortage in one material throttles unrelated projects globally

**Type:** Simulation bug  
**Priority:** Critical
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `project_resource_throttle(k)` (`sim/engine/economy.py`) now scopes the throttle to projects whose own materials share the actually-binding tag, per its own docstring: "paper research does not become short of saltpetre because a gunpowder project is." See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

Saltpetre demand made `resource_throttle = 0.05`, slowing unrelated rag paper, mirrors, distillation, coal, and coke to 5%. Copper demand later set `0.605` and also slowed unrelated cast iron and Work/Power. `capacity` confirmed a single global binding throttle.

## Expected behavior

Only projects consuming the short resource—or a genuinely shared constrained facility—should slow.

## Impact

One obscure shortage silently reduces the entire research portfolio by up to 95%.
