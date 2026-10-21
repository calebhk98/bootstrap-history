# An opened Rome game holds almost no smiths, so smith work is refused for want of people

**Status:** open

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
