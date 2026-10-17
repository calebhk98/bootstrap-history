# Tin is cheaper than copper because cassiterite has no deposit stock

**Status:** partly - recipe mass balance fixed; aged-game price falls below the labour that digs it, tracked by 507 stage 7 (unsold asks)

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

Lead (`galena_kg`) and mercury (`cinnabar_kg`) had the same defect and are restated the same way: the ore good is
the rock raised at the deposits' output-weighted grade, mining hours from `vein_hours_per_tonne_ore`, and the
smelting recipe asks for the rock its grade and recovery imply. `test_ore_recipe_mass_balance.py` now covers
every smelting recipe.

Measure: the `YearInputs` stepping loop of `test_economy_tin_dearer_than_copper.py` over `rome_100ad`. Opening
year shown tin over copper went from 0.015 to 0.74. Later years still show tin far below copper, falling from
about 0.7 in year one to under 0.1 and staying there (eight years). Two causes, neither in the recipes:
- The remembered ask of idle gravel sellers (`cassiterite_kg|united_kingdom_01`, `|spain_03`) decays to a fraction
  of the labour that digs a tonne, and tin trades a few tonnes a year at a price below the labour in its gravel.
  This is an idle seller's ask decaying below its making cost, plan stage 7 of
  `docs/architecture/ONE_PRICE_OWNER_PLAN.md` (Complaints/507); the aged-game relation (tin not below copper)
  waits on it, and is not asserted until then.
- Copper ore shows tens of times the labour of raising it (a scarcity price from capped sites against demand),
  while tin's sites have room far above its demand, so tin never meets a binding site limit. Whether tin should
  bind depends on the working rate of the tin deposits (`geography.working_rate_tonnes_per_year`) against the
  demand for bronze; re-measure both before acting.

## Update 2: the failing ratio is copper's scarcity price, not tin below its labour

Measured on `fix-511-tin-price` (from `economy-accounting-and-speed`) by stepping `rome_100ad` ten years the way
`test_economy_tin_dearer_than_copper.py` does (`economy.step(YearInputs(...))`, then `shown_prices_of`; the suite's
short spin-up). `python3 -m sim.tests --slow --only economy_tin_dearer_than_copper`: shown tin over copper 0.048,
embodied-labour ratio 0.441. The failure is not caused by tin selling below what it costs to make:
- Tin shows 0.64 in the first year against a cost per unit (`entry_trial.full_cost_per_unit` at live prices) of
  0.5 to 0.8, and it stays in 0.6 to 1.5 over the next years. About four to seven hours of the local wage a
  kilogram; the labour its recipes embody is about one hour. Tin is not below its labour.
- Gravel (`cassiterite_kg`) sellers hold seeded stock (UK tile: tens of thousands of tonnes, against a few
  thousand tonnes a year that tin draws), do not run, and mark their expected price down by
  `UNSOLD_ASK_MARKDOWN_SHARE` a year. It falls from 4.2e-4 per kg to 2.6e-4 by year three, level with the labour
  that digs a kilogram (1.5 hours a tonne at the tile's labourer wage, 2.4e-4). Then the stock is drawn down and the
  UK gravel producer leaves the record in year four. No year in ten shows gravel clearly below its labour, so the
  unsold-ask floor of 507 stage 7 would change nothing in this check: tin is already above that floor.
- Copper shows 13.2, 14.5, 16.6, 17.8 in years zero to three against smelting costs of 1.1 to 2.8 at every
  producer (six to nine times cost). Its smelters hold no stock and sell out, so their asks rise; the clearing price
  rises above every ask because supply is short. Spain, the largest, ran 98 of 336 runs of capacity and moves 25 percent
  of capacity a year (`OUTPUT_CHANGE_SHARE_PER_YEAR`), so supply cannot follow the demand of bronze (bronze traded
  rises from 460 t to 1141 t in three years while copper traded goes 278 t, 436 t, 426 t).
For tin over copper to reach 0.441 with tin near its cost, copper would have to show at about its cost. The relation
is therefore a copper question (the supply response of smelters against the growth of bronze demand, and whether
the opening's bronze volumes are in balance with the copper capacity it sets), not a tin or unsold-ask one.
Bisect: the check passes at `ef5ac9ff` (its own branch) and fails at `d1d2f508` (that branch's merge, ratio 0.078),
so a change that came in with the merge moved copper; the commits between are mostly unbuildable
(`git bisect` skipped them), so the first bad one was not isolated.
Status stays partly. No code change was made; no regression test was added, since no mechanism defect was shown.
