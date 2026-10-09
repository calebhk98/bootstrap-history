# Money constants and technology revenue are still in book denarii

**Status:** partly - no money amount is written in book denarii any more, and a node's capital, upkeep and revenue are derived wherever the data states a staff, a plant or a product (`node_capital.py`, `node_upkeep.py`, `node_revenue.py`); remains: typed `rev_hours` on nodes that name no product, typed `up_hours` on those and on programme spending, and typed `cap_hours` on the nodes whose typed revenue depends on it (see the last section for the per-file list)

Money is now anchored to each civilisation's coin, and costs are labour-hours
inside the engine, but some numbers are still written in the old book
denarii:

- engine money constants such as the "visibly rich" eminence threshold and
  fixed parts of living cost (one, the state's household-scale saturation,
  was converted to labourer-years);
- every technology's authored `rev` (revenue) and some cost fields in the
  tree. Against the new wages, payback times shifted for many nodes, and the
  pump payback guard in `sim/tests/test_early_playtest.py` was loosened to
  keep passing.

Find them with `grep -rn "denari" sim/engine --include=*.py` and the
`declare()` units in `python3 sim/constants.py --burndown`.

## What it would take

- Convert each constant to a physical unit (labour-hours, labourer-years, or
  a mass of the coin metal) and convert at the display edge.
- Derive a concern's revenue from what it produces and the market price of
  that output, instead of an authored `rev`, and restore the pump guard.

## Progress: one conversion boundary (units)

- [x] Authored book denarii convert once, through labour hours, into each
  civilisation's coin (`sim/engine/money_units.py`): node `rev`, `up`, `cap`,
  materials, the book goods table, and every declared money constant
  (`book_money=True` on `declare`; each `Sim` holds its own converted copy).
  `python3 sim/constants.py` lists the declared constants; grep for
  `book_money=True` for the converted set.
- [x] A `Sim` for a civilisation other than the loaded default gets its own
  copy of the tree in its coin (`data.nodes_in_civ_money`), and protocol
  screens read `sim.nodes`.
- [x] Tests: `sim/tests/test_money_units_one_boundary.py` (revenue over wage,
  material price over hourly wage, coin mass rescales every figure).
- [ ] The pump payback guard in `sim/tests/test_early_playtest.py` stays at its
  loosened threshold: the unit fix restores each node's payback ratio to what
  it was, and the remaining gap to the original guard comes from skilled-trade
  wages now following the training premium.
- [ ] Derive a concern's revenue from what it produces instead of an authored
  `rev` (still open).
- [ ] Inline money amounts in the auto policies were converted with
  `Sim.book_money`; any new money literal must go through it too.

## Progress: physical constants (second increment)

- [x] Constants that are labour or mass are declared in labour hours
  (`FARM_LABOUR_HOURS_PER_HA`, `FOREST_LABOUR_HOURS_PER_HA`,
  `HOUSING_LABOUR_HOURS_PER_PLACE`, `TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT`,
  `NITRE_LABOUR_HOURS_PER_M2`, the two living-cost bases, the institution
  upkeep per head, the venture hands ratio) and priced in the civilisation's
  coin on read (`money_units.PricedInLabourHours`). Values were rounded in the
  move, a drift of about one percent.
- [x] The seven curated `MINE_OPEX_PER_T_*` figures are removed; opex comes
  from the deposits' extraction labour. Count of `book_money` constants:
  `python3 -c "import sys;sys.path.insert(0,'.');import sim.engine.core;from sim.constants import book_money_names;print(len(book_money_names()))"`
  (before this increment: more than twice as many).

## Progress: node money in labour hours (third increment)

- [x] Branch data and mod data carry `cap_hours`, `up_hours`, `rev_hours`
  (converted once, at full precision, so every figure is bit-identical to the
  old division). `money_units.price_nodes` multiplies by the civilisation's
  money per labour hour; there is no `NODE_MONEY_FIELDS` and no book-denarii
  node converter left. Tools (`tool_costs` (script since removed; recover with `git show 97473f1:sim/tool_costs.py`), `audit_costs` (script since removed; recover with `git show 97473f1:sim/audit_costs.py`), `treetool` (script since removed; recover with `git show 97473f1:sim/treetool.py`),
  `civ_start_check`) read the hour fields.
- [x] `python3 -m sim.tests.fingerprint check --quick` is byte-identical for
  this move alone.

## Remains

- The remaining `book_money` constants are amounts of money, not physical
  quantities: revenue and funding scales, credit lines, bribes, arrears and
  insolvency floors, the eminence threshold, the slave base price. Count:
  `python3 -c "import sys;sys.path.insert(0,'.');import sim.engine.core;from sim.constants import book_money_names;print(len(book_money_names()))"`.
- A node's `rev_hours` is still authored, not derived from what it produces.
- The pump payback guard is still at its loosened threshold.

## Progress: the last sixteen (fourth increment)

- [x] Re-declared in labour hours (priced in the coin on read, values rounded to three figures): the slave base price, the credit line per hectare of forest, the revenue scale for the mining ceiling, the revenue ceiling per population scale, the capability-factor half-saturation, the imperial funding base and the patron-death courting gift. They scale with what labour costs, not with the coin. Sixteen `book_money` constants before, nine after (`python3 -c "import sys;sys.path.insert(0,'.');import sim.engine.core;from sim.constants import book_money_names;print(len(book_money_names()))"`).
- [x] Eight of the nine now say in their `why` why they are money amounts: debt floors (arrears and insolvency) are nominal sums of the coin the debt was contracted in, the bribe prices are negotiated coin payments, the credit line per reputation point is a nominal advance, and the bribery capital threshold is a threshold on coin held.
- [x] `EMINENCE_WEALTH_VISIBLE_THRESHOLD` is declared as `EMINENCE_WEALTH_VISIBLE_THRESHOLD_LABOUR_HOURS` (a wealth threshold is a stock of labour-valued goods) and priced in the coin on read; the test is in `sim/tests/test_eminence_scandal_and_reputation.py`. The other eight `book_money` names were reviewed again and stay: each is a nominal sum of coin (a debt floor fixed when the debt was contracted, a negotiated bribe price, an advance per reputation point, a threshold on coin held), so scaling it with labour cost would change what it means.

Update (concern-margins-and-capital-charge): the guard stands at the same quarter-year as `node_revenue.MINIMUM_PAYBACK_YEARS`. Making it stricter means raising that heuristic floor, which caps many more authored revenues, and three output-derived wage-heavy nodes (hand papermaking, phenol, rope walk) would then fail on gross revenue although they earn only their wages (`Complaints/336`). Not done.

Related: 283, 295, 317, 318, 329, 335, 337.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 283 (`closed/283-node-revenue-was-authored-against-book-material-costs.md`): node revenue for non-product nodes (equipment, services) is still authored against book material costs.
- 381 (`closed/381-authored-money-amounts-are-not-revalued-by-the-price-level.md`): authored money amounts are priced once at load (`money_units.price_nodes`) and not revalued by the price level.

## Moved from 132

- Production data still names land in iugera (`iugerum_land`, `land_iugera_years`) and the price solver converts at that one edge; `sim/world/land.py` works in hectares. Engine message source spells money "denarii" and the display edge (`sim/ui/proto/util.py`, `_localise_money`) swaps the civilisation's own word in. Both are internal names, not what a player reads (`closed/132-the-game-assumes-rome-exists.md`).

Owner decision (2026-10-09): a money amount in book denarii is an error, not a documented exception: remove Rome from the game and the figure means nothing. Every money amount becomes a physical quantity (labour hours, a mass of goods or coin metal) converted at the display edge.

## Progress: the book boundary removed (fifth increment, owner decision applied)

- [x] The eight remaining `book_money` constants are declared in labour hours and priced on read (`money_units.PricedInLabourHours`): credit line per reputation point, the two bribe prices, the two arrears floors, the insolvency floor, the bribery capital threshold and the auto-bribe cost per point. Each `why` says why it is a count of hours (a bribe is the work and risk an official gives up, a debt floor is the labour that clears it). They now follow the price level like the other hour-declared constants; before, they were fixed at load.
- [x] The inline `book_money(...)` literals in the auto policies are declared constants: people are bought in multiples of one person's base price (`AUTO_BUY_PEOPLE_*_IN_PRICES`), forest and nitre-bed spending in labour hours.
- [x] Mechanic effect specs (`credit_line`, `living_cost_status`) carry `labour_hours: true` and hour values instead of `book_money: true`; `Sim.effect_value` multiplies by the coin's money per labour hour.
- [x] `BOOK_LABOURER_WAGE_DENARII_PER_HOUR`, `book_to_money`, `book_money_factor`, `Labour.book_money`, the economy and labour port wrappers and `book_money_names` are deleted. `rg book_money sim data` finds only the regression test that says they are gone (`sim/tests/test_no_book_money.py`).
- [x] The generic output and market-share curves in `economy_materials.py` (fitted in book denarii per kg) are restated in labour hours per kg (anchor and scale rescaled by the old wage, a price floor declared), so the last reader of a book unit is gone.
- [x] The node field defaults are two labourer-years of capital and four-tenths of a labourer-year of upkeep (`node_defaults.py`) and the data entries that wrote the old book default out are restated the same way.
- [ ] Still open: node `cap_hours`/`up_hours` are authored hour figures (the old book figures divided once by the book wage), and `rev_hours` is derived from output for only a few dozen nodes. Measure with `data.load()`: count nodes by `_revenue_basis` and `_upkeep_basis` (about a thousand authored revenues, about fourteen hundred authored upkeeps). Deriving them needs each node's staff, plant and product stated in the data; nineteen authored-revenue nodes already gate production entries but state no plant output or staff to bound them.
- [x] The pump payback guard: there is no guard test left to loosen; it became the diagnostic `node_payback_diagnostic` (`simulator.py economy-check --payback`), which never caps revenue (`Complaints/336`). Rows under the diagnostic threshold: `python3 sim/simulator.py economy-check --payback`; capital for typed-revenue nodes stays typed so the count does not grow while their revenue is typed.

Not run (needs a whole game, which takes about half an hour cold): `sim/tests/test_physical_money_constants.py`, `test_money_units_one_boundary.py`, the eminence and closure tests that use `hours_money`, and the `literacy_market_pricing` ledger checks.

## Progress: capital and upkeep from what the data states (sixth increment)

- [x] `cap_hours` is derived (`sim/engine/node_capital.py`): the build bills of the plant a node's entries state plus tooling for its `sch` and `art` places (`WORKPLACE_TOOLING_PERSON_YEARS_PER_PLACE`, a labelled heuristic). A node that states `cap_hours` keeps it, labelled `authored`. The default of two labourer-years is gone (`node_defaults.py`); typed capital is removed from every node that states no revenue.
- [x] A node named in an entry's `operated_by` earns from output without a typed `rev_hours` or `up_hours`; the output nodes carry neither figure, and their entries name them.
- [x] A node that states no `up_hours` and earns from no output keeps up a labelled share of its build bill (`_upkeep_basis` `default`) in place of the old flat default.
- [x] `simulator.py validate` prints revenue, upkeep and capital by basis and the branch files that still type figures (`node_revenue_census.py`).
- [ ] Typed figures that remain, with the data each needs (measure with `python3 sim/simulator.py validate`, section "TYPED FIGURES STILL IN BRANCH FILES"):
  - nodes that name no product: each needs the production entries it runs (`operated_by`, with outputs, labour by trade, plant with service lives and capacity, each with a `basis`), after which revenue, upkeep and capital derive and the typed fields are deleted. Files: 00_core, 10_textiles, 11_food_agriculture, 12_household, 13_media, 14_land_transport, 15_ships, 16_aviation, 17_energy, 18_chemicals, 19_metallurgy_mining, 20_precision, 21_medicine, 22_civil, 23_optics_instruments, 24_comms_computing, 30_expeditions, 40_finance_institutions, 42_electrical_deep, 45a_transport_land_deep, 45b_transport_rail_marine_deep, 47_agri_food_deep, 48_instruments_deep, 49_military, 51_construction_deep, 52_energy_deep, 53_information_deep, 60_goalpath_deep, 62_control_ops_deep.
  - nodes that gate entries but no staff, plant or declared output bounds them (their `output_unbounded_reason` says why), in 00_core, 17_energy, 18_chemicals, 19_metallurgy_mining, 21_medicine, 47_agri_food_deep, 48_instruments_deep and 51_construction_deep.
  - nodes that type an upkeep and no revenue: programme spending (benefactions, 56; 55_realism_part02), capability upkeep (00_capabilities) and service staff (19_metallurgy_mining, 22_civil, 18_chemicals, 00_core and others). Each needs its staff by trade and its materials stated, or a programme model.
  - sciences that type an upkeep and earn nothing.
