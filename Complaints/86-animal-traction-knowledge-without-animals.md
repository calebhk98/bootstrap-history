# Knowledge of animal traction should be visually separate from actual animal availability

**Status:** partly - `why` carries `living_stock` (material, held, needed, brought_by) and prints a `KNOWLEDGE:` line apart from a `HELD:` line; a `needs_first` gate on a material is now a supply blocker, not a knowledge one (`stock_gates` in `sim/engine/living_stock.py`; test `sim/tests/test_small_screen_items.py`). Remains: `available` and `state` still list the technique without the held-stock line.

Mexica could complete knowledge and capability relating to draught-animal muscle power while carts and treadmills remained blocked because no local draught animals existed in that civilization.

The blocker was mechanically correct - the capability should not work without the physical resource. However, the capability name in isolation could imply that the physical resource now existed.

## Why it matters

A player who sees "draught-animal power: known" may incorrectly believe they can now use animal traction, when the actual bottleneck is a separate geographic/biological resource that requires domestication or import. This sets a false expectation about what the technology accomplishes.

## What would resolve it

Display knowledge and resource availability as separate items:

```text
Knowledge: draught-animal power - known
Local draught animals: unavailable
Import/domestication route: required
```

This pattern can generalize to any technology that depends on biological or geographic resources.

## Where it lives

Likely in `sim/engine/proto/techtree.py` and capability display sections where technology effects are shown.

**Confidence:** Design recommendation
