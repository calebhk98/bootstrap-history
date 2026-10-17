# Production chains stop at raw materials, so crafts have no products and farms buy no tools

**Status:** open

Reference (an outside table of ancient supply chains, not code-aware): each trade bought inputs from
named trades and sold finished goods to named ones, for example the smith sells ploughshares, sickles
and nails to farmers, carpenters and masons; the potter sells amphorae to wine merchants and tiles
to builders; the dyer dyes the weaver's cloth.

## What the data does

Measured by walking `inputs` and `outputs` of `data/production/*.json` and the goods of
`data/world/needs.json`:

- **Households buy materials, not goods.** `iron_bar_kg` meets `implements_and_arms`, `ceramic_kg`
  meets `vessels`, `flour_kg` meets `food`, `leather_kg` meets `clothing`. There are no tools,
  nails, amphorae, tiles, lamps (531), bread (530), sandals, harness, carts, yokes, furniture or ships.
- **The army wears bar iron** (`sim/agents/budget.py`, `EQUIPMENT_MATERIAL = "iron_bar_kg"`).
- **Farms buy no tools.** `labourer`, the farm trade, has no `tool_basket` in `data/world/trades.json`;
  the only iron a grain field draws is in the plough-team capital of one wheat technique. Fishers,
  carters and soldiers have no tool basket either. Farms take no manure or storage jars, and seed is
  netted out of the yield (`sim/world/agriculture.py` docstring says the physical form lists it).
- **Dead ends.** Nothing consumes `dye_kg`, so dyers make a good nobody uses and cloth is never dyed.
  `cloth_kg` (fulling) takes no fuller's earth or urine. `wine_common_kg` and `olive_oil_kg` need no
  press and travel without jars. Millstone wear is not charged (`data/production/95_grain_milling.json`).

## Why it matters

The demand that sized ancient crafts is missing: a smith's market is the farm sector's tools, a
potter's is the jars every wine and oil shipment needs. With finished goods missing, these trades are
sized from household spending on raw materials, and the founder has no tool, container or ship
business to improve. It also hides the crafts from the non-farm need shares (530).

## What it would take

- Finished goods with their own recipes and wear lives (`data/world/service_lives.json`): iron tools,
  nails, amphorae, tiles, ships, carts, footwear; needs and the army buy these instead of materials.
- Tool baskets for the farm, fishing, carting and soldiering trades, so field work consumes iron.
- Close the dead ends: dyed cloth from cloth and `dye_kg`; fulling inputs; jars as an input or
  carriage cost of wine and oil; a press as capital.
- A check in `simulator.py validate` listing produced goods nothing consumes, so a new dead end shows.
