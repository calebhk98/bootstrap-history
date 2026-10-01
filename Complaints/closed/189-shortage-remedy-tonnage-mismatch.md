# The shortage remedy suggests a mine size unrelated to the shortfall `capacity` shows

**Status:** closed - one shortfall per material (Sim.material_shortfall_t) feeds the capacity rows and shortage_remedy_plan; capacity_remedies takes the numbers, not the sentence

In a late-game save, `capacity` listed copper short 704 t/year while the remedy text built by `shortage_remedy` (sim/engine/economy_freight.py) suggested "quote mine copper 23". The remedy computes its own shortfall differently from the capacity rows, so the command it suggests would not cover the shortage the same screen reports. Found while adding the "WHAT WOULD FIX EACH SHORTAGE" section for complaint 90 (sim/engine/proto/capacity_remedies.py reuses the remedy text).

What it would take: one shortfall figure per material, computed once and used by both the capacity row and the remedy text; a test that the suggested tonnage covers the reported shortfall.
