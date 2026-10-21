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

## Update 3: copper's supply is not held by cash, expansion pace or entry; year zero is set by the opening

Measured by stepping `rome_100ad` the way the test does (spying `producers.plan`, `producers.produce`,
`year_labour.clear_labour` and the entry planners; scripts were throwaway). What was ruled out:
- Cash and working-capital loans do not bind. Every copper smelter holds tens to hundreds of thousands in cash
  against a run costing about two thousand; `affordable` in `producers.plan` is never the smallest term.
- Copper ore does not bind in the first years: the ore producers hold seeded stock and plan zero runs while
  smelters buy it at a price near their cost of digging. (Later, around year four, the seeded stock is gone, the
  ore producers' expected price is still below their cost, and Spain's smelter gets about one run of ore: a lag in
  the ore sellers' expectation, not measured further.)
- Plant capacity does not bind year zero. Spain has capacity 336 runs; its plan is 182 because the opening seeds
  `last_runs` at 98 and `within_a_years_change` allows 25 percent of capacity (84) more. But removing that limit
  (plan 335) leaves year-zero copper at 13.9 against 13.2: the achieved runs stay at 172 because smith hours
  (40 a run) in the Spain labour area are all hired (bid 11112, offered 11342) and furnaceman and charcoal run out
  next. The opening's workforce by trade matches the opening's output, so supply cannot rise in year zero by any
  rule on the producers' side. The test measures year zero only, so entry, expansion and loans cannot change
  its result; it follows the opening (`opening*.py`, the workforce by trade), another branch's ground.
- Later years: tripling `EXPANSION_SHARE_PER_YEAR` (0.1 to 0.5) triples capacity by year three
  (Spain 336 to 497, the others to 3x) and leaves copper at 17.7 in year three (17.8 before): plans are still
  bounded by last year's achieved runs plus 25 percent of capacity, and by inputs.
What does bind the smelters outside Spain from year one (4 of 7 producers, about a fifth of planned runs):
flux (`flux_kg`, crushed limestone). Algeria, Turkey and Italy have flux makers of capacity 0 to 1 run, so they
buy 0 to 4 runs of flux against 15 to 55 planned (year two: Algeria 17.8 planned, 0.0 achieved). Their
`last_runs` then collapses and the 25 percent pace rebuilds it only slowly. The flux maker never grows because
`entry_sizing.sized_runs` caps a newcomer at `ENTRY_SHARE_OF_TRADED_VOLUME` of what the market traded last year
(Algeria: 32 kg traded, 1.29 runs of gap, built 0.016 runs), and traded volume is small precisely because the
market was starved. Sizing on traded volume plus the buyers turned away (`share * (volume / output + whole_gap_runs)`)
raised the flux makers and halved copper in years three and four (17.8 to 8.1, 21.3 to 8.1), still four to five
times cost, but it contradicts `test_a_gap_far_beyond_the_trade_is_sized_to_the_trade`, which pins the cap as
deliberate (a phantom gap must not build a works), so it was not kept: a rule that tells a starved market from a
phantom gap is needed first (the buyers' bids at the entry price against the maker's cost, for the markets where
no sale shows a price).
Status stays partly. No code change; the binding constraints are the opening's workforce by trade and seeded
`last_runs` (year zero), then input makers that never grow from a starved market (flux), then the ore sellers' lagging
expectation.

## Update 4: entry sized from unfilled bids (559) does not move flux or copper in the short Rome run

`entry_sizing` now counts bids left unfilled at the entrant's full cost (Complaint 559). With `ROME_SPIN_UP_YEARS=2,1`
flux traded and the copper price are unchanged over five years (copper 2.88, 8.40, 12.44, 13.67, 15.47 before and
after), because the flux gap is a few kilograms and flux entry is never sized there. The test still fails (0.047
against 0.441) and reads year zero only. The full-spin-up case was not rerun.

Note (Complaint 570): the opening now makes the charcoal its smelters burn, which raised tin against copper at the opening; the check `economy_tin_dearer_than_copper` still fails by a narrower margin.

## Update 5: year-zero copper is a spin-up transient plus a labour ceiling; no engine defect found, check kept

Traced on `tin-against-copper` (from `pm-complaints-burndown`) by stepping `rome_100ad` one year on the suite's
opening (the harness sets `ROME_SPIN_UP_YEARS=3,2`) and on longer ones, with throwaway in-process probes (spies on
`producers.plan`, `producers.produce`, `year_labour.run_labour_year`; the book's edge flows; `notional.making_costs`).
Read each price against its making cost at the shown input prices and at the full chain cost (every input at its own
making cost, labour at the shown wages):
- Tin shows above its labour and near its cost (a little under cost at the shown inputs, a little over its chain cost).
  Gravel sellers, tin works and the gravel price are not the gap.
- Copper shows several times its chain cost and a little over twice its making cost at the shown inputs. Its inputs
  carry scarcity too: wood well above its labour, charcoal above its making cost, ore above its making cost. Copper
  burns far more charcoal and ore per kilogram than tin, so the same scarcity weighs on it far more.
- Even with both metals at exactly their chain cost the ratio sits just under the embodied-labour ratio, so the check
  asks that copper show at or just above its chain cost in year zero.
- Why copper does not: the suite's opening is not settled (`spin_up_result["settled"]` is false). In its last hidden
  year the smelters ran almost nothing (their expected price sat under their expected cost) while the brass and bronze
  makers consumed copper from seeded stock (`book.edge_goods_net` on `edge:production` and `edge:consumption`). Stock is
  gone in year zero, and each smelter may move only `OUTPUT_CHANGE_SHARE_PER_YEAR` of capacity from last year's runs
  (`within_a_years_change`), so supply is a fraction of the demand and the sold-out asks rise. Where that pace does not
  bind, smith hours do: every copper labour area has smith vacancies at a wage equal to its ceiling, the cost of
  training a substitute (`trained_substitute_wage`, `sim/labour/market/clearing.py`), while the smelters bid far above it. Cash, ore,
  charcoal and flux do not bind.
- A longer spin-up does not cure it. With `ROME_SPIN_UP_YEARS=6,2` the smelters run at about half of capacity, the
  smith ceiling binds everywhere, and copper climbs to tens of times its cost (the ask raise on sold-out sellers keeps
  ratcheting while supply cannot respond). The shipped full opening has a different price level and other outliers
  (flux far over its cost); not traced.
So the year-zero gap is the model's own short-run answer (a trade whose hands cannot grow within the year, a producer
that idled the year before), not a recipe, entry or accounting error. Raising the smith wage above the training-cost
ceiling in a vacancy, or allocating scarce hours by value, is a labour-core design decision (the `trained_substitute_wage` rule, the
wall in `sim/labour/`), not made here. No code change; the check is unchanged and stays red.

## Sourced: skill premia (2026-10-20)

`Complaints/reports/research-how-trades-spread-and-skill-premia.md` (each claim with its URL): the English building
craftsman's wage over the labourer's (Munro's table of Phelps Brown and Hopkins) fell after the Black Death and kept
falling for decades, since unskilled hands were scarce too; over the early modern centuries it sat near three to two in
southern England (Allen, through Broadberry and Gupta). No source was found for a short-run premium of one scarce trade
far above its training cost. The long-run anchor at the cost of training a substitute stands; a short-run premium needs
a sourced case of one trade short while others were not before it is built.

## Update 6: decomposition of the shown ratio on the current code (no rule defect found)

Measured by stepping `rome_100ad` one year as `test_economy_tin_dearer_than_copper.py` does (`--slow --only
economy_tin_dearer_than_copper`: shown tin over copper 0.11 against 0.441), then reading `economy.record`
(`memory.prices`, `producers`, `setup.site_limits`), `country_figures.wages_per_hour`, `notional.cheapest_cost` at the
shown prices (throwaway in-process probes, not kept). The log of the gap (0.441 over 0.11) splits into two parts:
- Which price is shown: tin is one market area (`france_05@b3`, the only Roman-touching tin area; its one seller is the
  UK tin works), copper is `france_05@b4` plus the Egyptian area. Carriage and area choice are not the gap: every
  shown figure is one area's cleared price over its own producers.
- Copper clears at about three times its making cost at the shown inputs, tin at about one and a third. Every copper
  seller's remembered ask sits below the clearing price (asks near twice cost); the price clears above all asks because
  copper supply is short. Planned runs summed over the copper smelters are about twice the runs achieved (Spain plans
  2040, achieves 1742; China plans 1620, achieves 6; Algeria 414 to 245), while the tin works achieve nearly all of
  their plan. The smelters' last-year runs are the opening's seed (idle the year before), so supply cannot follow demand
  within the 25 percent a year pace, and the hands (smith hours at the training-cost ceiling) cap the rest: Updates 3
  and 5, not changed by anything here.
- Copper's inputs carry scarcity that tin's barely do. A kilogram of copper burns four kilograms of charcoal and 50 of ore;
  a kilogram of tin 0.6 of charcoal and 643 of gravel. Charcoal shows near three times its making cost in the main area, so
  even with tin and copper both made at cost from the shown inputs the ratio is about 0.24, under the embodied-labour
  ratio, which prices charcoal at its labour alone.
Site scarcity and the sellers' asks for tin are not the cause: gravel shows above its labour (not decayed under it), the
UK gravel site limit sits far above any tin demand, copper ore's sites are not binding in year zero (ore sellers hold seeded
stock), and no carriage or area rule puts tin low. The cause is the unsettled opening (Complaint 473) acting on copper and
charcoal, and the labour ceiling on smith hours; a fix is a labour-core and opening change, so none was made here. No
regression test added, since no rule was found wrong; the slow check stays red and unchanged.

## Update 7: the smith ceiling is not what holds copper down; rule kept (skilled-labour-ceiling-rule)

Rule tests: `sim/tests/test_labour_core_skilled_ceiling.py` (plain records, calls `clearing.clear_all`, `year.run_year`,
`trained_substitute_wage`). Findings:
- The ceiling caps the quoted wage, not the hours. Employers bidding far above it are quoted the ceiling and every hand in
  the trade is hired (hours wanted stay above hours offered); raising the maximum bid changes neither wage nor hours.
- New hands come only as trainees through the trade's own places (incumbents times `APPRENTICES_PER_MASTER`, plus school
  seats), never by the wage directly and never by switching from labourers while the wage sits at the ceiling. Once those
  places are full, removing the ceiling adds no trainees, so in the long run places, not the ceiling, bound growth.
- Research (`Complaints/reports/research-how-trades-spread-and-skill-premia.md`): no opened source shows a craft premium
  rising above its long-run level when the craft was short; after the Black Death the premium fell. One-off imports of
  artisans cost a large multiple (Epstein), which the core already prices as `ImportCosts`, a cap below the ceiling.
  So the rule is not shown wrong and was not changed.
- Year zero on `rome_100ad` (spies on `year_labour.run_labour_year`, `producers.plan`, `producers.produce`, as for Update
  6): the smith ceiling does not bind copper. Smith hours hired meet the smith hours the smelters' runs need in every copper
  area; the binding terms in `producers.produce` are unskilled labourer hours (employers want more than all offered, in
  every copper area), furnaceman hours in the one area whose furnacemen are few, and flux in one area. The plan is held by
  the 25 percent pace from seeded `last_runs` (a smelter idle the year before plans a quarter of capacity), then achieved
  runs fall below plan on those hours. So the measured split is the opening's seeded `last_runs`/pace (Complaint 473)
  plus total unskilled hours, not the skilled-labour ceiling. Remeasure: spy as above on one `economy.step` of the suite's
  opening. The check stays red and unchanged.
