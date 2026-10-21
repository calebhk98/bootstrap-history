# Production chains stop at raw materials, so crafts have no products and farms buy no tools

**Status:** open (stages 1 and 2 done; later stages below)

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
- **Dead ends.** Nothing consumes some produced goods; `python3 sim/simulator.py validate` lists them (see Done, stage 1).
  Still open from the original list: `cloth_kg` (fulling) takes no fuller's earth or urine; millstone wear is not charged
  (`data/production/95_grain_milling.json`). Jars and presses for wine and oil, amphorae, ships and bread are now 616, 617
  and 614 (closed).

## Why it matters

The demand that sized ancient crafts is missing: a smith's market is the farm sector's tools, a
potter's is the jars every wine and oil shipment needs. With finished goods missing, these trades are
sized from household spending on raw materials, and the founder has no tool, container or ship
business to improve. It also hides the crafts from the non-farm need shares (530).

## What it would take

- Finished goods with their own recipes and wear lives (`data/world/service_lives.json`): nails, tiles, carts, footwear,
  and the army's equipment; needs and the army buy these instead of materials (iron tools, amphorae, ships and bread are
  done or filed as 614, 616, 617).
- Tool baskets for the farm, fishing, carting and soldiering trades, so field work consumes iron.
- Close the remaining dead ends: fulling inputs; millstone wear.
- A check in `simulator.py validate` listing produced goods nothing consumes, so a new dead end shows.

## Done (stage 1)

- **Dead-end check.** `sim/engine/validate_dead_ends.py`, printed by `python3 sim/simulator.py validate` as findings (not errors). A good counts as consumed by a recipe input or capital build, a need, a trade tool basket, a carriage, navy or capital-asset rule, a held durable, an energy field, or the state and army budget lines (`DOLE_MATERIAL`, `EQUIPMENT_MATERIAL`, now exported by `sim/agents/api.py`). Goods only tech-tree nodes consume are counted apart. `dye_kg` is no longer a dead end; run the command for the current list.
- **Iron tools.** `iron_tools_kg` (`data/production/10_ferrous.json`: iron bar and smith hours), service life in `data/world/service_lives.json`, and the `farmer` trade (the crop-growing trade; `labourer` is the unskilled fallback) now has `tool_basket: ["iron_tools_kg"]` and `tool_stock_per_worker`. `sim/labour/trade_data.py` `tool_draw` gives the stock a trade's workers hold and what wears out each year (stock over service life). The wage tools factor already reads the basket, so farm wages now follow the tool price. Wiring the wear into the economy's demand for tools is not done.
- **Dyed cloth.** `dyed_cloth_kg` (`data/production/40_organics.json`, cloth and `dye_kg`), listed under clothing in `data/world/needs.json`. Mexica does not hold the madder node, so it declares the good in `unsupplied_basket_goods`.
- **Sources read.** Science Museum Group, early iron sickle, https://collection.sciencemuseumgroup.org.uk/objects/co38922/early-iron-sickle: "overall (laid flat): 55 mm x 500 mm x 250 mm, 0.24 kg". allfiberarts.com madder recipe, https://allfiberarts.com/?p=2778: "20 grams Indian Madder Root powder" "for 100 grams of fibre" (a modern craft recipe).
- **Labelled heuristics, no source found (retire: this complaint).** Bar per kg of tool, smith hours per kg of tool, tool service life, tool kg per farm worker, dyer hours per kg, and dyed cloth counting as plain cloth for clothing. Sources looked for and not opened (blocked pages): the Hallen 2003 thesis on Swedish farm iron and Catarina Karlsson's 2015 thesis on iron wear per hectare (abstracts seen in search results only, so not used).
- **Left for later stages.** Fisher and carter tool baskets (no tool source found), nails, amphorae, tiles, ships, carts, footwear as household goods, the army's bar iron, fulling inputs, jars and presses.
- **Tests.** `sim/tests/test_production_chain_stage_one.py`.

## Done (stage 2)

- **Tool wear is a demand.** `sim/economy/tool_wear.py`. The port (`tool_wear_recipes` in `sim/engine/economy_port_setup.py`) turns each trade's `tool_basket` and `tool_stock_per_worker` (`trade_data.tool_draw`, now exported by `sim/labour/api.py`) into wear per hour worked, and `with_tool_wear` adds the wear of a recipe's hired hours to its `inputs` (and lists it in the new `Recipe.tool_wear`). Producers then plan, bid for, buy and consume it through the ordinary input path, so smiths are sized by farm demand. A tool no recipe in the society makes is not charged, and a recipe never wears the tool it makes. The data names no good in code.
- **Own-plot households.** `own_production_options` accepts a recipe whose only inputs are tool wear. A household's own-plot hours are recorded by recipe (`YearLedger.own_plot_hours`), and `cohort_orders` (`sim/economy/year_goods.py`) adds `tool_bids`: the stock those hours keep in use, less what it holds after this year's wear (the durable rule), paid from its cash before its other goods. The tools it holds wear as any cohort durable.
- **Left out.** Employers do not hold a tool stock, only buy the yearly wear (a flow). A household's first year buys the whole stock. A society with no recipe for the tool charges none.
- **Tests.** `sim/tests/test_complaint_533_stage_two_tool_wear.py`. Not run, being whole-game: `python3 sim/simulator.py economy-check`, and the shipped openings (`openings/`) are likely to need recomputing (`openings`, `opening-checks`).

## Done (tool shortage, Complaint 659)

A tool is no longer a hard input. A trade's `tool_basket` names alternatives in order (`wooden_tools_kg` after
`iron_tools_kg` for the farmer), a short tool is replaced by the next one with its own hours per run, and then by hand;
a recipe is never zeroed by a tool shortage alone (`Recipe.tool_fallbacks`, `Recipe.hard_inputs`,
`sim/economy/tool_fallback.py`). The opening no longer cuts users of a deposit-bound tool. The stage 2 note "Left out"
still holds: employers hold no tool stock. See Complaints/659 for the measurements.
