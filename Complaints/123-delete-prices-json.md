# Deleting `data/prices.json`

**Status:** open

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

- [x] `sim/world/wages.py` is the wage provider: wage per hour is a subsistence
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
`sim/engine/labour_allocation.py` reallocates non-farm hours toward their
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

What still limits it: the coin's value is fixed at the opening technology, so
later improvements to the coin metal's production do not deflate the currency
(a labelled simplification: money supply and debasement are not modelled).
The book goods table is still in denarii, so a book-priced fallback for a gated
material is not in the civilisation's own unit.

### 3. Make endogenous material prices the only runtime path

`data.load()` defaults to the book goods table and overlays solved prices only
when requested. Reverse that relationship material by material: a price must
come from production, rent, energy, capital, transport, risk, and market state,
or the good must be explicitly unavailable. There must be no book fallback.

The blockers already known in that solve are structured land use for grown
goods, rent for non-ore extraction, incomplete capital/energy/transport/margin
costs, and an import/unavailable policy for technology-gated goods. Coverage by
a recipe is necessary but is not proof that its price is economically complete.

### 4. Remove the independent material-supply read

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

- [x] `sim/treetool.py` takes material identity from the production catalogue
  plus what tree nodes require (`load_material_namespace`); `judge` and
  `repair` cost nodes through `sim/tool_costs.py`, which uses the runtime wage
  provider and `sim/engine/prices.py`'s solver, and reports costs as
  unavailable or as a lower bound with the unresolved materials named.
- [x] `sim/validate_production.py` loads the tree, production catalogue and
  trade registry without the main loader, so it never initialises prices.
- [x] `sim/audit_costs.py` prices its cost base through the same service and
  drops the book-confidence section.
- [x] `sim/solve_prices_report.py` takes wage ratios from the live wage
  provider and says prices are unavailable when it cannot; `--compare` is gone.
- [x] `sim/tests/test_tools_without_price_book.py` runs each tool with the file
  unreadable.

The wage provider no longer reads the file's wage section, so these tools
get wages without it.

### 6. Remove comparison and test readers

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
