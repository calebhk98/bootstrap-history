# Money constants and technology revenue are still in book denarii

**Status:** partly - seven more money constants are labour hours now; nine remain in book denarii and are documented as genuine money amounts (eight) or still to document (the eminence threshold); revenue is derived from output for nodes that make something (`sim/engine/node_output.py`, 283) and authored for the rest; the pump guard is still loosened

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
- [ ] `EMINENCE_WEALTH_VISIBLE_THRESHOLD` (in `sim/engine/society_state_pressure.py`, owned by the state-budget work at the time) still needs the same decision: it reads as a wealth threshold, which is a stock of labour-valued goods, so it probably belongs in labour hours.

Update (concern-margins-and-capital-charge): the guard stands at the same quarter-year as `node_revenue.MINIMUM_PAYBACK_YEARS`. Making it stricter means raising that heuristic floor, which caps many more authored revenues, and three output-derived wage-heavy nodes (hand papermaking, phenol, rope walk) would then fail on gross revenue although they earn only their wages (`Complaints/336`). Not done.

Related: 283, 295, 317, 318, 329, 335, 337.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 283 (`closed/283-node-revenue-was-authored-against-book-material-costs.md`): node revenue for non-product nodes (equipment, services) is still authored against book material costs.
- 381 (`closed/381-authored-money-amounts-are-not-revalued-by-the-price-level.md`): authored money amounts are priced once at load (`money_units.price_nodes`) and not revalued by the price level.

## Moved from 132

- Production data still names land in iugera (`iugerum_land`, `land_iugera_years`) and the price solver converts at that one edge; `sim/world/land.py` works in hectares. Engine message source spells money "denarii" and the display edge (`sim/ui/proto/util.py`, `_localise_money`) swaps the civilisation's own word in. Both are internal names, not what a player reads (`closed/132-the-game-assumes-rome-exists.md`).
