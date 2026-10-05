# The subsistence staple behind the opening wage is wheat for every civilisation

**Status:** closed - regression test subsistence_staple_is_civilisation_data

`sim/labour/wage_provider.py` `FOOD_PRICE_MATERIAL = "wheat_kg"` prices the subsistence basket that
sets every civilisation's wage floor (`sim/engine/wage_schedule.py` reads it). That basket is wheat for
Han China (millet and rice) and Mexica (maize) as well. A mod civilisation without wheat cannot open:
`build_schedule` raises when the staple cannot be priced. Complaint 398 shows the same wheat-only
measure misreading wages.

What it would take:
- The civilisation file states its staple, or better its subsistence basket from
  `data/world/needs.json`, as the agent economy's `outside_option_by_tile` already does.
- `wage_schedule.build_schedule` reads that instead of the constant.
- The constant is then deleted. Its only readers are in `sim/engine/`, so the change is outside
  `sim/labour/`.
