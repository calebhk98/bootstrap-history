# Deleting `data/prices.json`

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

### 1. Replace the wage inputs

`sim/engine/data.py` still opens the file at import time to build `WAGES` and
`ANNUAL_WAGE`. Those globals feed hiring, training, payroll, freight, production,
credit, scoring, and protocol output. The dynamic labour market must become the
provider for both hourly and annual trade costs. Trade identity and initial
availability have already moved to `data/world/trades.json`; no replacement
wage table should be added there.

The price solver also derives skilled/unskilled wage ratios from the old wage
table. It must instead consume the same labour-market wage provider as the live
engine so project costs and payroll cannot disagree.

### 2. Remove the denarius conversion anchor

Solved material costs are expressed in labour-hours, then multiplied by the old
`labourer` rate to return to denarii. Choose and implement one authoritative
unit boundary: keep real costs in labour-hours internally and convert at the UI
edge, or derive a current money wage from the model. A replacement literal
`denarii_per_labour_hour` would only move the dependency and does not count.

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

`sim/engine/economy_materials.py` opens the file separately and reverse-engineers
national output and market share from book price for uncurated materials. That
must be replaced with physical production capacity and resource/trade access.
Threading the same old prices through `Sim` would hide the direct read without
removing the dependency and therefore does not count.

### 5. Separate namespaces from prices in every tool

`sim/treetool.py` still uses purchase-price keys as the material namespace and
uses the book values in `judge` and `repair`. Material identity must come from
the production catalogue plus technology requirements. Cost audits must use the
same endogenous pricing service as runtime, or explicitly report a material as
unavailable/incomplete.

`sim/validate_production.py` currently reaches the file indirectly through the
main simulator loader. Validation must load the tree, production catalogue, and
trade registry without initializing runtime prices.

### 6. Remove comparison and test readers

The standalone price report's `--compare` mode and several demand, deposit,
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
