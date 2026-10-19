# Light has no quality term, so tallow's smoke, smell and softening in heat cost nothing

**Status:** open. Split from Complaint 531, which needs engine work in `sim/world/need_basket.py`.

Households value light in kilolumen-hours only (`data/world/needs.json`, `effectiveness_basis`), and the
mix between goods serving one need is by cost per unit of need (`NEED_SUBSTITUTION_ELASTICITY`). A tallow
candle that smokes, stinks and sags in summer heat gives the same worth per lumen-hour as an oil lamp or
beeswax, so the only thing that separates them is price.

## What it would take

- A per-good quality or disutility factor on a need in the needs data (a good's `satisfies` entry carrying
  an effectiveness already discounts it; a separate field would let the reason be stated and varied with
  climate, since softening depends on temperature).
- Tallow's factor labelled a temporary heuristic until indoor air (smoke, ventilation) is modelled.
- A test reading the structured light shares, not wording: with the factor set, the share of light spent on
  tallow at a start where oil and tallow cost the same falls below the share at factor one.

## Not covered by Complaint 531's closure

The lamps and candles it added already follow where olives, herds and flax grow.
