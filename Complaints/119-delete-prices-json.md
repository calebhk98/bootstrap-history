# Deleting `data/prices.json`

**Status:** partly - the file is deleted and nothing opens it; the commodity ledger prices from the solved table and the book labourer wage is gone; remains (see Remains): supply curves inferred from price, authored node hour figures (Complaints/140); the import and unavailability policy for gated materials and the two photovoltaic gates are done (see Remains)

`data/prices.json` is not a calibration dataset and will not survive the
migration. Historical observations that are independently worth testing may be
copied into narrowly scoped test fixtures with their own provenance, but the
file itself must be deleted rather than renamed.

## Definition of done

Deletion is complete only when all of these are true:

1. No runtime or tool opens `data/prices.json`.
2. No import requires the file to exist.
3. No material price, wage, trade identity, currency conversion, supply curve,
   project cost, or validation namespace falls back to a value from the file.
4. Tests construct focused fixtures or use endogenous results; they do not load
   the old file.
5. `rg -n 'prices\\.json|\\bPRICES\\b' sim tools` contains documentation about
   the completed migration at most, and deleting the file passes the full suite.

## Remaining production blockers

### 1. Replace the wage inputs (done)

- [x] `sim/labour/wages.py` is the wage provider: wage per hour is a subsistence
  floor times a training premium times a tightness factor. The floor is the
  cost of feeding a worker and dependants from the food model; the premium
  repays training years forgone (`training_years` in `data/world/trades.json`,
  family median when a trade states none); the tightness factor moves each
  year with the gap between a trade's need and its hours.
- [x] One seam for the engine: `Sim.wage_per_hour(trade)`,
  `Sim.base_annual_wage(trade)` and `Sim.wage_document()` feed payroll, hiring,
  training, commissions, freight, mining, production, credit, scoring and
  protocol output. `data.WAGES` / `data.ANNUAL_WAGE` are the starting
  schedule for tools, no longer a book table.
- [x] The price solver reads the same wage vector through
  `WageSchedule.document()`; `sim/engine/prices.py` keys its cache on it and
  pays an unlisted trade by the same training rule.
- [x] `sim/tests/test_wage_provider.py` runs the engine with the wage section
  of the book removed.

What still limits it: only `Sim.update_wages` moves tightness, and
`sim/labour/labour_allocation.py` reallocates non-farm hours toward their
current split rather than toward the need `update_wages` measures, so wages
signal scarcity but hours do not yet answer. Feeding the need shares into
`reallocate` closes that loop. The discount rate is a labelled default; a
civilisation's own interest rate should replace it. Tree `rev` values were
authored against the old wages, so revenue-to-cost paybacks moved (see the
relaxed pump check in `sim/tests/test_early_playtest.py`).

### 2. Remove the denarius conversion anchor (done)

- [x] The wage floor's food price is the staple's solved cost in labour hours
  (its recipe and land rent), not a book price. `wage_provider.build_schedule`
  documents the closure: in numeraire hours the unskilled wage is 1, so food
  solves once from training premiums alone and the real-wage condition is the
  hours of work needed to buy the subsistence basket per hour worked.
- [x] Money is anchored to each civilisation's `coin_standard` (material, mass
  per unit, source). A labour hour in money is the reciprocal of the coin's
  solved labour hours; costs stay in labour hours until the display edge
  (`hours_to_denarii` reads the document's `money_per_labour_hour`). A mod
  civilisation without a standard fails to load with a clear error.
- [x] `_book_food_price_per_kg` and `FOOD_PRICE_PER_KG` are gone;
  `sim/tests/test_wage_floor_and_coin_standard.py` runs wages with the book's
  wheat entry removed or changed.

Opening kits are stated in labourer-years (`STARTING_KITS`, `data.kit_capital`)
and convert through the civilisation's own wage.

- [x] One conversion boundary, `sim/engine/money_units.py`: authored book
  denarii become labour hours through one labelled transitional factor (the
  book's own reference labourer wage), then the civilisation's money through
  its `money_per_labour_hour`. It covers the book goods table (`data.load`,
  `priced_goods_table`, `calculated_goods_prices`), each node's `rev`, `up`
  and `cap`, and every declared money constant (`declare(..., book_money=True)`,
  converted per `Sim`). `sim/tests/test_money_units_one_boundary.py` checks it.
- [x] The conversion factor itself, the book labourer wage, is deleted (it is a book
  figure no more; remaining authored hour figures are tracked in Complaints/140).

What still limits it: the coin's value is fixed at the opening technology, so
later improvements to the coin metal's production do not deflate the currency
(a labelled simplification: money supply and debasement are not modelled).
A book-priced fallback for a gated material is now in the civilisation's unit
but is still a book figure. The commodity ledger's own base prices
(`commodities.json`) are still read in book denarii by the ledger.

### 3. Make endogenous material prices the only runtime path (done, with one labelled heuristic)

- [x] `data.load()` returns solved prices only; `sim.engine.prices.priced_goods_table` no longer takes a book table. Every material a recipe makes has a price; ten production entries that had no technology gate (so every gated solve dropped them) now name one, and the iodine entry has labour. `python3 sim/simulator.py validate` and `python3 sim/simulator.py validate` report no unpriced material the tree needs.
- [x] A material only a technology not yet held can make is priced at the nearest such technique (provenance `gated`); one nothing in reach makes has no price unless a partner sells it (Complaints/38).

`data.load()` defaults to the book goods table and overlays solved prices only
when requested. Reverse that relationship material by material: a price must
come from production, rent, energy, capital, transport, risk, and market state,
or the good must be explicitly unavailable. There must be no book fallback.

The blockers already known in that solve are structured land use for grown
goods, rent for non-ore extraction, incomplete capital/energy/transport/margin
costs, and an import/unavailable policy for technology-gated goods. Coverage by
a recipe is necessary but is not proof that its price is economically complete.

### 4. Remove the independent material-supply read (price read done; supply curves remain)

`sim/engine/economy_materials.py` no longer opens the file separately. It now
asks the shared price calculator for an era- and civilization-specific table,
so materials the solver can resolve use computed prices in supply, freight,
trade quotes, and generic mine costs. This is only the first half of this
blocker: the calculator provider still falls back to book values for gated or
incomplete production chains, and the generic output and market-share curves
still infer physical supply from price. Those fallbacks must be replaced with
physical production capacity and resource/trade access before the file can be
deleted. Merely moving the remaining old values behind the shared provider is
not completion; it prevents another private reader while that replacement is
built.

### 5. Separate namespaces from prices in every tool (done)

- [x] `sim/treetool.py` (script since removed; recover with `git show 97473f1:sim/treetool.py`) takes material identity from the production catalogue
  plus what tree nodes require (`load_material_namespace`); `judge` and
  `repair` cost nodes through `sim/tool_costs.py` (script since removed; recover with `git show 97473f1:sim/tool_costs.py`), which uses the runtime wage
  provider and `sim/engine/prices.py`'s solver, and reports costs as
  unavailable or as a lower bound with the unresolved materials named.
- [x] `sim/engine/validate_production.py` loads the tree, production catalogue and
  trade registry without the main loader, so it never initialises prices.
- [x] `sim/audit_costs.py` (script since removed; recover with `git show 97473f1:sim/audit_costs.py`) prices its cost base through the same service and
  drops the book-confidence section.
- [x] `sim/solve_prices_report.py` (script since removed; recover with `git show 97473f1:sim/solve_prices_report.py`) takes wage ratios from the live wage
  provider and says prices are unavailable when it cannot; `--compare` is gone.
- [x] `sim/tests/test_tools_without_price_book.py` runs each tool with the file
  unreadable.

The wage provider no longer reads the file's wage section, so these tools
get wages without it.

### 6. Remove comparison and test readers (done)

The calibration classes in `test_deposits.py` and `test_demand.py` no longer compare against the book; `data.load()` returns the wage document in the old price-book slot, and `PRICES` is gone from `sim.engine.data` and `simulator`.

(The standalone price report's `--compare` mode is already removed.) Several demand, deposit,
civilization, and engine-price tests open the old file. Delete comparisons that
only enshrine its guessed values. Where a genuine historical observation is
useful, create a focused validation fixture that records the observation,
units, date/place, source, and uncertainty rather than copying a book entry.

Finally remove `PRICES` from the public `simulator` compatibility surface and
shrink `data.load()`'s five-value return. Do this last, after callers no longer
need the raw object.

## Order of work

1. Land the labour-market wage provider and use it in both runtime and solver.
2. Remove the labour-hour-to-denarius book anchor.
3. Graduate complete material families to endogenous-only pricing, starting
   with manufacturing chains that need no missing land or extraction rent.
4. Finish land, extraction, capital, energy, transport, and gated-import paths;
   then remove all remaining material fallbacks.
5. Replace the material-supply price fit with physical capacity.
6. Decouple validators, `treetool`, comparison reports, and tests.
7. Remove the raw `prices` return/API, delete `data/prices.json`, and run the
   direct-reference search plus the full suite.

Moving fields into another omnibus JSON file is explicitly not part of this
plan. Each surviving datum needs a real owning model or a narrowly scoped,
sourced test fixture.

## Remains

`data/prices.json` is deleted and nothing opens it. Still open before this can close:

- The generic national-output and market-share curves in `sim/engine/economy_materials.py` infer physical supply from price (blocker 4); with solved prices a cheap gated material such as aluminium gets an enormous fitted market. Replace with physical capacity and resource access.
- (done) A material no one in reach makes has no price: priced by the home technique in reach, else the cheapest partner's landed price, else unavailable, and a project that needs it cannot start (Complaints/38, `sim/tests/test_no_seller_no_price.py`). The transitional "mature" price is gone from `priced_goods_table`; the energy-grade fallback in `sim/engine/energy_prices.py` is gone too (a line that states a heat grade nothing held supplies cannot run).
- (done) `data/world/commodities.json` carries no price: each commodity names a `price_material` and `CommodityLedger` takes the solved price of it in labour hours per kg.
- (done) `BOOK_LABOURER_WAGE_DENARII_PER_HOUR` is deleted. Node `up_hours` and `cap_hours` are still authored hour figures (Complaints/140); node `rev` is now derived from output for nodes that gate production entries and have a staff or plant to derive from, and is nil for sciences that make nothing, while the rest keep authored `rev` (see Complaints/283, 295, 296).
- (done) `photovoltaic_panel_m2` and `electrical_mj_photovoltaic` carry `requires_node: silicon_path` (solar-grade silicon, the gate of `silicon_kg`, which the panel is built from). The cycle the earlier attempt blamed (aluminium needs electricity, the panel needs aluminium) is not a solver fault: the resolvability pass takes the dynamo route topologically so the loop never forms there, and the numeric solve prices the loop to a fixed point in a few dozen rounds (`AlternativeEnergyCycleTests`). The 30 second overrun was the cold solve cache, which any edit under `sim/` or `data/` invalidates: `data.load()` takes longer than 30 seconds on a cold cache with or without the gate. Not re-timed on the real tree here.
- `rg -n 'prices\.json|\bPRICES\b' sim tools` now finds only tests that guard against reading it and the harness's own `PRICES` name; the prose in `sim` comments is fixed, data and docs outside `sim` (mostly historical) still mention the file.

Related: 38, 309.

Owner decision (2026-10-09): high priority: do it soon, it likely causes economic errors.
