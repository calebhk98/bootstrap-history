# Light has no quality term, so tallow's smoke, smell and softening in heat cost nothing

**Status:** closed. Split from Complaint 531, which needs engine work in `sim/world/need_basket.py`.

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

## Resolution

A good may declare a `quality` factor per need in the `goods` table of `data/world/needs.json` (or on a
production entry): `{factor, basis, conf, heuristic, retire}`. `make_basket` reads it into `NeedSpec.qualities`.
`priced_need` weighs a good in the mix by its effectiveness times the factor to the power of a buyer's
`quality_reach`; the need units a good gives stay its effectiveness, so quality moves where spending goes, not
the light delivered. `goods_orders` sets each cohort's reach from its surplus share of spending
(`quality_reach`, a labelled temporary heuristic), so a cohort with nothing above its floors buys on cost alone and
a richer one pays more per unit for the cleaner light. A good with no factor, or a reach of zero, mixes exactly as
before. Tallow and oil-lamp light carry placeholder factors against beeswax (confidence D, retire: indoor air
model). Tests: `sim/tests/test_need_quality.py`. Not done: the aggregate demand model (`need_demand.py`) still mixes
on cost alone, and the factor does not yet vary with temperature.
