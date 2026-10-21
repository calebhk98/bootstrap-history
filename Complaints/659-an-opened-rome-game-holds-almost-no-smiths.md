# An opened Rome game holds almost no smiths, so smith work is refused for want of people

**Status:** fixed on branch tool-fallback-and-iron-site-room (the full opened-game smith count was not re-measured: a cold spin-up does not finish inside the two-minute rule; re-measure with `national_trade_population("smith")` on `sim(civ="rome_100ad")`)

Found in deep extraction 3 (640). In an opened `rome_100ad` game the labour core's people of the smith trade read
about a thousandth of a person, against tens of thousands in an unopened game; `start horse_collar` is then refused
with cause `people_exist` ("no one left to do the smith work"). It reproduces on a clean checkout of the integration
branch, so it is not the extraction's doing. `start_and_upkeep_quotes_scenario` fails two checks on it.

Measure: `national_trade_population("smith")` (labour api) on `sim(civ="rome_100ad")` against `unopened_sim(civ="rome_100ad")`.

Why it matters: a trade the opening empties cannot be hired, so whole branches of the tree are refused at the start,
and 533 stage 2 now makes farms buy iron tools that smiths make.

What it would take: find which rule moves the opening's smiths out (the opening's placement by expected sales, the
post-spin-up trim to the plot trade, 551's landless cohorts, or 644's formation step), test it as a function, and fix
it so a trade the economy's recipes book hours to keeps the people that work them.

## Findings (opening workforce pass)

Measured by building `sim(civ="rome_100ad")` with the spin-up cache bypassed and reading the record at each step
(`sim/economy/labour_state.opening_workforce`, `workforce_settle.trim_to_expected_hours`, `opening_runs.fit_to_supply`):

- The placement and the trim are not the rule that empties the smiths. `opening_state` places the people the booked
  hours take and `trim_people` keeps the people the wanted hours take (both now have regression tests,
  `sim/tests/test_opening_workforce_follows_hours.py`). Both are fed hours near zero: after `fit_to_supply`,
  `iron_tools_kg` producers hold an expected-sales total of about 6e-12 runs against about 1.5e6 before it, and
  every `smith` recipe producer is 0.0 to the second decimal.
- The cause is upstream of the workforce. 533 stage 2 made worker tool wear a recipe input, so almost every recipe now
  uses iron tools. `limited_goods` then holds nearly the whole economy to the iron deposits: the sited iron ore limit
  caps the bloomery at tens of thousands of runs, tools are cut to about 2% of what the wear asks, and the cut repeats
  through every user (wheat, millet, leather, charcoal users, bread) each sweep (trace: print factor, supply and wanted
  inside the sweep loop). The smith hours the recipes book at the opening's volumes are therefore a few hundred hours,
  a handful of smiths, which `national_trade_population` reads as the core holding people (not "nobody"), so the old
  estimate is no longer used.
- Separate defect found and fixed: `labour_state.plot_trade` skipped every land recipe with an input, and 533 stage 2
  gave every crop its tools as an input, so the plot trade became `herder` instead of `farmer`. It now ignores inputs
  that are tool wear, as `households_own.own_production_options` does.

Not fixed: the volumes. A smith count that follows the hours needs the opening to book tool wear against an iron
supply that can meet it (the iron sited limits against the wear of the tool stock, `data/world/trades.json`
`tool_stock_per_worker`), or `fit_to_supply` to stop propagating a tool shortage through every user. Both are outside
the opening's workforce modules.

## Done (the real cause)

Two defects, both fixed.

1. **A missing tool stopped the work.** `produce` treated the tool wear of 533 stage 2 as a Leontief input, and the
   opening held every user of a deposit-limited good to its supply. Now a trade's `tool_basket` is an ordered list
   (`data/world/trades.json`; `tool_hours_factor`, `tool_hours_factor_by_hand`): the first good a recipe in the society
   makes is the tool, each later one is a `ToolFallback` on the recipe (`Recipe.tool_fallbacks`, built by
   `with_tool_wear`), then the work is done by hand. `producers.produce` draws the fallback when the tool is short and
   the extra hours lower the runs the hired hours allow (`sim/economy/tool_fallback.py`); a tool is no longer in
   `Recipe.hard_inputs`, which the opening's ceilings, `limited_goods`, `fit_to_supply` and entry sizing read. Planners
   bid for the fallback tool as well. In the opening, `shift_unmet_tools` meets the wear a capped tool cannot with the
   next tool. New good `wooden_tools_kg` (`data/production/96_wooden_tools.json`, service life in
   `data/world/service_lives.json`): every figure is a labelled heuristic with `retire` naming this complaint (no source
   found for the hours factors, wood per tonne, carpenter hours or service life). Stone tools (618) join by being
   listed in a trade's basket; none is listed yet. Own-plot households are unchanged: their output never depended on
   holding the tool, and their tool bids still buy the first tool.
2. **The iron site room is not too tight.** Measured on Rome's opening: the six sited iron deposits give a yearly room
   equal to the data's historical rates (`deposit_history.py`), which sum to the 82,500 t of metal a year the data state
   for the empire (`data/world/resources.json`, Craddock 2008 p. 108 as quoted in Poehler et al. 2019, read; source
   string corrected). The working share (0.004) is below those rates for every deposit, so the rate is the room. About
   1.7e8 kg of ore a year, against about 4e7 kg the opening wants. The room rule is right; a test pins it.
   The real cause upstream of it was in placement: `opening._add_producers` skipped a second share of runs on a tile
   that already held the producer, so the pooled share of the areas with no site of their own was dropped and the ore
   was placed at a tenth of the runs the smelters needed. It now adds the share to the producer.

Opening of Rome (`unopened_sim(surveyed=())`, `open_economy`; before and after this branch): expected sales of wheat
2.7e9 to 3.6e9 kg, bread 1.72e9 to 1.71e9 kg, iron tools 4.3e5 to 1.39e6 kg (wooden tools 0 to 6.5e5 kg), iron ore
3.5e6 to 4.1e7 kg; smiths the opening places 1773 to 5726, carpenters 2195 to 5986. Tests:
`sim/tests/test_complaint_659_tool_fallback_and_site_room.py`.
