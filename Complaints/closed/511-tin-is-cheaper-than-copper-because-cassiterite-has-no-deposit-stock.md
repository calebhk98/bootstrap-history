# Tin is cheaper than copper because cassiterite has no deposit stock

**Status:** closed

Split from 502. The recipe `cassiterite_kg` (`data/production/20_nonferrous.json`) costs a few miner and
labourer hours a tonne and carries nothing for the scarcity of the deposit, while copper's ore recipe carries a
large ore and labour cost. In an aged Rome game tin shows a fraction of copper's price, the reverse of the
historical relation (measure: `python3 sim/simulator.py play --civ rome_100ad --seed real25`, `market` screen, or
`shown_prices_of(economy)` for `tin_kg` and `copper_kg`).

Tin's scarcity is geographic: few deposits, long haul. The recipe cannot express that; a producer anywhere with
a mine recipe can make cassiterite at alluvial cost.

What it would take (data and geography work): cassiterite draws on a limited deposit stock at located tiles
(as other ores draw on `sim/world/deposits`), so tin's price rises as near deposits deplete and the route to
far ones lengthens; no engine special case for tin (CLAUDE.md 4.7). A regression test that tin's shown price
over copper's is not below the ratio of their deposit scarcity in an aged game.

## Update

The mechanism already covered cassiterite (`ore_goods` in `data/world/geography/resources/minerals.json` sites the
recipe at the tiles holding tin deposits and draws their stock, `sim/engine/economy_port_sites.py`); the data
did not. `cassiterite_kg` was a dressed concentrate costing a few hours a tonne, while the site accounting treats
a run's output as whole deposit ore at the deposit's grade, and `tin_kg` asked for under two tonnes of it. A
tonne of tin therefore drew a few kilograms of tin's worth of stock. `cassiterite_kg` is now the gravel dug and
washed (labour from `ALLUVIAL_HAND_PROCESSING_HOURS_PER_TONNE`) and `tin_kg` asks for the gravel its deposits'
grade and the washing and smelting recoveries imply (sources in the entries' `yield_basis`, the washing
recovery a labelled conf D heuristic). Tests: `sim/tests/test_ore_recipe_mass_balance.py` (every smelting recipe
asks for ore holding its metal at the richest located grade; lead and mercury are listed as not yet restated),
`sim/tests/test_economy_tin_dearer_than_copper.py` (opening-year shown tin over copper is not below the ratio of
the labour their recipes embody).

Measure: the `YearInputs` stepping loop of `test_economy_tin_dearer_than_copper.py` over `rome_100ad`. Opening
year shown tin over copper went from 0.015 to 0.74. Later years still show tin far below copper; that is not
the recipe but copper ore's scarcity price and unsold-seller drift, filed as 516.
