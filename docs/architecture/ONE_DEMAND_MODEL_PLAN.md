# One household demand model, and the other duplicates Complaint 115 still lists

**Status:** stages 1 to 4 built on branch `one-demand-model` (2026-10-06); stages 5 to 7 not started. Written against
branch `structural-dedupe-and-owner-decisions`. It answers the "Still two owners" list in
`Complaints/115-multiple-parallel-models-need-an-authoritative-one.md`: three household demand models, the engine's
capital market with the agent economy off, and the merchant stand-ins.

What is built. Stage 1: `sim/world/need_basket.py` holds the pure kernel (`make_basket`, `need_prices` taking a
`price_of(good)` function, `price_ceilings`, `subsistence_cost_per_person`, `need_units`, `limit_satiation`);
`sim/economy/households_basket.py` re-exports it and prices a basket from a market view. Stage 2: `climate_basket`,
`basket_with_floors` and `mean_climate_basket` make climate floors a kernel function; `baskets_by_tile` calls it.
Stage 3: `NeedDemandModel.final_demand` takes price index, floors and surplus split from the kernel; the engine adapter
(`market_demand.household_basket`) gives it the people-weighted floors of the civilisation's tiles, so shelter, clothing
and warmth carry demand in the opt-out game. Stage 4: strata pay the floor of each need in turn
(`SimWorld.need_floor_costs_per_person_year`, `stratum_year.run_year`); `STRATUM_OTHER_NEED_FOOD_MULTIPLE`,
`housing_cost_per_person_year` and `HOUSING_FLOOR_AREA_PER_PERSON_M2` are gone; `record.shortfall` is keyed by need id.

What stage 3 and 4 left for later. The price solver's anchors (`joint_allocation.build_demand_anchors`) still build the
model without climate floors, because no map reaches that function. The strata cost comes from the engine's goods-market
prices in both modes; with the agent economy on, asking the economy's own tile prices through `sim/economy/api.py` is
not done. `household_saving` (`agents_port_capital.py`) still uses `income_bins` and belongs to stage 5.
`agents_port_budget.py`, `wage_schedule.py` and `foreign_capacity.py` still read the food-floor constant or the model
without a civilisation. Stratum surplus beyond the floors and schooling is saved, not spent by need weight: that needs a
labelled propensity and is open. The fingerprint was not recorded (owner's rule for this branch); record a new baseline
before merging.

Rules this plan keeps (`CLAUDE.md` section 4): no hardcoded outcomes, interventions through normal rules, every
heuristic labelled, no save migration, no content ids in the engine. Tests below pin relationships, never dated
values.

## Measurements used in this document

Every figure in prose is replaced by a pointer into this table. Re-run the command before acting on a row.

| Measure (2026-10-06) | Value | Command |
|---|---|---|
| Production files importing `sim.world.demand` | 35 | `grep -rn "sim.world.demand\|world import demand" sim --include=*.py \| grep -v tests \| wc -l` |
| Production call sites of the strata cost questions (`subsistence_cost_per_person_year`, `housing_cost_per_person_year`) | 14 | `grep -rn "subsistence_cost_per_person_year\|housing_cost_per_person_year" sim --include=*.py \| grep -v tests \| wc -l` |
| Per-person floors the aggregate model gives each need (food, then shelter, clothing, health, ornament, seasoning, warmth) | food positive, every other need zero | `python3 -I -c` snippet: build `need_demand.NeedDemandModel(needs, demand.production_data(), demand.income_bins(1.0, 550.0))` and print `.subsistence` |
| Price index of one need served by one, two and three identical goods at equal price, effect and substitution elasticity two: aggregate model (`need_demand.final_demand`) against the economy (`households_basket.need_prices`) | aggregate: 1, one half, one third; economy: 1, 1, 1 | same snippet: compare `(sum((price/effect)**(1-sigma)))**(1/(1-sigma))` with `1/sum(share*effect/price)` |

## 1. The three models

### 1.1 `sim/world/demand.py` plus `sim/world/need_demand.py` (the aggregate model)

What it computes. `demand.py` holds the closed form: a Stone-Geary linear expenditure system. Each `Good` has a
physical subsistence quantity and a marginal budget share; quantity demanded is the floor plus the share of income
left after every floor is paid, divided by price. Below the committed cost of all floors it applies a protected-floor
rule (`FLOOR_TRADEABLE_SHARE`). It also owns the income distribution (`income_bins`: a Pareto split of a population
from a Gini coefficient), derived demand through recipes, and joint-output value shares. `need_demand.NeedDemandModel`
puts needs on top: a need is the Stone-Geary good, goods inside a need compete through a constant-elasticity mix on
cost per unit of effectiveness, a satiation limit caps a need (`need_satiation.py`), and recipe inputs are demanded in
turn.

Inputs. `data/world/needs.json` (floors, `surplus_budget_share`, goods and their effectiveness), `data/production/`
(recipes), prices in labour hours, a population and a mean income, a Gini constant. It never reads climate: a need
whose floor is declared `subsistence_from_climate` gets zero here (see the table).

Readers. Find them with `grep -rnE "NeedDemandModel|household_demand_by_material|income_bins|household_quantity_demanded|market_clearing_price" sim --include=*.py | grep -v tests`:

- `sim/engine/market_demand.py` (`household_demand_by_material`): the year's demand ratio against the opening, which moves the engine's market price when the agent economy is off, and builds `base_basket` (`sim/engine/real_output.py`).
- `sim/engine/joint_allocation.py`: demand anchors that split a joint process's cost.
- `sim/engine/agents_port_capital.py` (`household_saving`): income bins to a savings flow, which supplies the engine's loanable funds.
- `sim/economy/households_cohort.py`: only `income_bins`, to cut a tile into income classes.
- `sim/labour/workforce_spinup.py`: `budget_weights_by_good`, `input_coefficients_per_unit_output`.
- `sim/engine/agents_port_budget.py` and `sim/engine/wage_schedule.py`: only the food floor constant, to price a subsistence dole and the wage floor.

### 1.2 The agent economy's household baskets (`sim/economy/households_basket.py` and its orders)

What it computes. `make_basket` turns `needs.json` plus recipes into `NeedSpec` records; `need_prices` prices each need
on a tile from the market view, with a constant-elasticity mix inside the need, a price index per need unit, and a
price ceiling above which a buyer stops buying a good. `households_orders.goods_orders` then turns a cohort's cash,
income, expectations and savings target into orders: floors, plus the surplus split by need weight, limited by
satiation, thinned for durables already held (`_durable_ratio`), and routed to goods that are affordable.
`economy_port_setup.baskets_by_tile` replaces the floors of climate needs with each tile's climate floor
(`sim/world/climate_needs.py`).

Inputs. The same `needs.json` and recipes, the tile's market prices, the cohort's income and cash, tile climate, the
interest rate and expected inflation (for the cash target and saving).

Readers. `grep -rnE "households_basket|need_prices|subsistence_cost_per_person\b" sim --include=*.py | grep -v tests`:
`households_orders`, `opening`, `year_goods`, `year_labour` (the reservation wage), `lending`, `state_budget`
(the state's goods budget uses the same need weights), `households_credit`, `households_store`.

### 1.3 The strata baskets (`sim/agents/stratum_year.py` and neighbours)

What it computes. A stratum is a headcount with a purse. Each year it needs three tiers: food (members times
`world.subsistence_cost_per_person_year()`), housing (`housing_cost_per_person_year()`), and "goods" (a fixed multiple of
the food cost, `STRATUM_OTHER_NEED_FOOD_MULTIPLE`, labelled as standing in for the demand system). It pays tiers in
order from its purse; the unpaid share of each tier is its shortfall, and the ratio of resources to the food bill is its
welfare, which drives births and moves.

Inputs. The engine's own food cost (`agents_port_cast.subsistence_cost_per_person_year`: the dole material priced by
`material_cost`, not by the agent economy's market) and a housing cost built from labourers' pay and the market rate.
No `needs.json`, no climate, no substitution, no income response: a richer stratum buys the same tiers and saves the rest.

Readers. `grep -rnE "subsistence_cost_per_person_year|housing_cost_per_person_year|\.shortfall|record\.welfare" sim --include=*.py | grep -v tests`:
`stratum_year`, `group_strata` (interest groups' welfare), `government_surplus`, `country_view` (other countries), and
whatever reads shortfall and welfare for population change.

### 1.4 Where they disagree

| Aspect | Aggregate (`demand.py`, `need_demand.py`) | Economy (`households_basket.py`, orders) | Strata |
|---|---|---|---|
| Functional form | Stone-Geary over needs, constant-elasticity mix inside a need | The same form per cohort, plus affordability, ceilings, durables, cash target | None: three fixed tiers paid in order |
| Floors | Food only; climate needs are zero | Every need, climate floors per tile | Food and housing as money costs; "goods" a multiple of food |
| Price index of a need | Unnormalised constant-elasticity index: it falls as goods are added to a need (see table) | Spend-weighted: need units add one for one, adding an identical good changes nothing | One price per tier, from the engine's cost model |
| Income elasticity | Floors plus weighted share of income above floors; closed form per income bin | The same, but on spending after saving and the cash adjustment, so surplus income is partly saved | None above the third tier |
| Below the floors | Analytic protected-floor rule | Budgets bind in clearing; floor bids get a price margin; the unmet floor is recorded | Tiers paid in order, shortfall per tier |
| Goods covered | Every good in `needs.json` plus recipe inputs | Every good in `needs.json`, plus stock held and credit | Food (one dole material), housing, one lump |
| Prices read | Solver prices in labour hours | The tile's cleared market prices | Engine `material_cost` and labour pay |
| Income | Pareto bins from a Gini constant, one mean | Cohorts: same bin shape, then last year's actual income | Observed cohort slices when the agent economy is on, otherwise a wage bridge |

Three of these are real inconsistencies rather than modelling levels: the aggregate model gives shelter, clothing and
warmth no floor (so its demand ratio for those needs reads income and price differently from the economy's); the two
price indices change differently as goods are added to a need; and the strata cost of living is priced by a separate
mechanism from the market the same people shop in.

## 2. Recommendation: the economy's priced-need form is authoritative, extracted to `sim/world`

Choose the need-and-floor form that the agent economy already runs, and move its pure part into a standalone
`sim/world` module so the engine and the strata can read it without crossing a wall. Reasons:

- It is the only model with climate floors, per-tile prices and satiation all live; the aggregate model is a reduction
  of it with parts missing, and the strata model is a stand-in that says so in its own constant's description.
- Its price index has the property a physical need requires: a calorie is a calorie, so offering more goods that
  deliver calories does not make calories cheaper. The aggregate index makes a need cheaper merely because more goods
  serve it, which is an artefact of the form, not a mechanism.
- The economy is the default game, and any actor (a firm's workers, a state's army, another player) must use the same
  mechanism (`CLAUDE.md` section 5, "General actors").
- It lives in a walled package, so the engine and the agents cannot import it. `sim/world` is the place for standalone
  models both may read, and `sim/economy` already imports `sim.world`.

What moves. A new module `sim/world/need_basket.py` takes `NeedSpec`, `Basket`, `PricedNeed`, `make_basket`,
`need_prices` (with the price taken as a callable `price_of(good)`, not the economy's `MarketView`), `price_ceilings`,
`subsistence_cost_per_person`, and the floors-plus-weighted-surplus step now in `households_orders._need_units`. The
climate floors (`baskets_by_tile`) become a function of tile climate in the same module, with the tile's climate passed
in by the caller. `sim/economy/households_basket.py` becomes a thin re-export so its callers keep working.

What stays where it is. Behaviour that is about an actor with a purse stays in the economy: cash targets, savings,
durables held, stores, credit, order routing and ceilings as bids. Derived demand through recipes, the income bins and
the closed-form helpers stay in `demand.py` and `need_demand.py`, but they call the kernel for floors, the price index
and the surplus split.

### 2.1 How the other two become readers

- **Aggregate model.** `NeedDemandModel.final_demand` keeps its loop over income bins but takes need specs and the price
  index from the kernel, and takes floors per need for the whole civilisation as the people-weighted mean of tile
  floors. It needs from the kernel what it lacks today: climate floors (a function of the civilisation's tiles,
  supplied through the geography api by the engine adapter `sim/engine/market_demand.py`), and the one price index.
  What the kernel lacks that the aggregate model needs, and keeps: recipe-derived demand, the Pareto bins, the
  protected-floor rule below committed cost (an aggregate shortcut for what clearing does per cohort), and a
  satiation switch for the solver (`satiate=False`).
- **Strata.** `SimWorld` (`sim/engine/agents_port*.py`) answers new questions from the kernel: the cost per person of
  each need's floor, and the quantities a class of given income buys by need. With the agent economy on, the answer
  comes from the economy through `sim/economy/api.py` and the port (the prices the cohorts actually pay). With it off,
  the adapter calls the kernel with the engine's prices. `stratum_year` then pays need by need (food, shelter, the rest
  of the floors, then surplus by weight) instead of food, housing and a multiple, and `STRATUM_OTHER_NEED_FOOD_MULTIPLE`
  goes. What the kernel lacks that strata need: a per-need shortfall (the economy records the unmet floor already; the
  kernel needs to return floors and affordable quantities so a purse that cannot pay reports which need failed), and a
  rule for what a stratum with no market tile uses for prices (the national price, `national_prices.py`).
- **Food floor constant readers** (`agents_port_budget`, `wage_schedule`) read the kernel's food floor instead of the
  constant in `demand.py`.

### 2.2 Decisions this needs from the owner

1. Confirm the spend-weighted index as the one index (it changes the aggregate demand ratio for any need with several
   goods, which moves the engine's off-economy market prices; the fingerprint will change for the opt-out game).
2. Confirm the below-floor behaviour stays two-level: the analytic rule for aggregates, clearing for cohorts, with a
   test that they agree when income covers the floors.

## 3. Capital market when the agent economy is off

State today. `sim/engine/economy_capital_market.py` (`update_capital_market`, `market_loans`, `market_funds`,
`market_credit_room`) meets once a year and sets a rate from funds demanded against funds held, using
`sim/world/capital_market.py`. With the agent economy on, `market_rate` and `market_credit_room` already ask the
economy first (`economy.api.credit_room`, `agent_rate`); the engine record answers only when it is off. But
`update_capital_market` still runs every year from `society_actors.advance_actors`, so the engine's record is built and
its savings supply (`household_saving`, which reads `income_bins`) is computed even when nobody reads them.

Recommendation. The economy's credit market is the one owner of the rate. Each of its lenders (households, firms,
state) and borrowers is an actor with a purse, which is what the loanable-funds ratio stands in for. Concretely:

- With the agent economy on: stop calling `update_capital_market` and `market_loans`; keep `capital_market_report` as a
  thin reader of the economy's rate and room. Nothing reads the engine record in that mode.
- With it off (opt-out, used by tests of old mechanisms): keep the world-level ratio rate as a labelled heuristic in
  `sim/world/capital_market.py`, behind one function `loanable_rate(funds, loans)`; delete the founder-specific
  record fields the economy cannot supply.
- The saving flow (`household_saving`) is then read from the kernel's surplus split (stage 3 below), not from a
  second use of `income_bins`.

What the economy lacks that the engine's market gives: the founder's own loan (`FOUNDER_LOAN`) is a borrower the
economy already receives through `agent_credit_room(actor_id)`; check it handles an id that is not a cohort or a firm.
The state's lending (`state_lending`) is read by `Government`; give it an economy-port member that returns the
economy's own figure.

## 4. Merchant stand-ins

State today (Complaint 115, "Merchants (405)"). The trader actors own inter-country flows of goods that actors carry.
Two stand-ins still own the rest: the engine's aggregate `foreign_traders` flow (`sim/engine/foreign_traders.py`,
`foreign_economies.foreign_trade_year_end`), dormant when the agent economy is on, and the economy's `_external_orders`
(`sim/engine/economy_port_year.py`), which offers imports and bids for exports of any good no actor carried that year,
capped by `FOREIGN_TRADE_SHARE`. The economy's own `merchants.py` moves goods between tiles only, with no partner.

Recommendation. Trader actors are the one owner of cross-border flows, and economy merchants the one owner of
cross-tile flows, so one mechanism (carry a gap net of carriage, risk and interest) is used by every actor. The route
to get there is Complaint 115 items 2 to 5: a trader as an account in the book, a partner on each order, a per-partner
edge, and domestic routes for traders. Until then `_external_orders` stays for goods nobody carries. Measure how much
it still carries with the existing checks in `sim/tests/test_foreign_actor_trade.py` before deleting anything.

What the stand-ins have that traders lack: a partner-less aggregate cap (`FOREIGN_TRADE_SHARE`) that stops an
uncarried good flowing without limit. The replacement is a trader founded where the gap is positive
(`trader_entry.py`), which needs the partner book to cover intermediates and ores first.

## 5. Staged plan

Every stage leaves the game playable (the default agent-economy game and the opt-out game both start and run a
decade), is its own commit, and adds tests that pin a relationship. Agents may take stages in parallel only where the
file sets are disjoint, as listed.

| Stage | Change | Files touched | Tests pinning a relationship | Waits on |
|---|---|---|---|---|
| 1 | Add `sim/world/need_basket.py`, move the pure basket types and price functions into it, make `households_basket.py` re-export. No behaviour change. | new `sim/world/need_basket.py`; `sim/economy/households_basket.py`; `sim/economy/households_orders.py` (import only) | The economy's priced needs equal the kernel's for the same prices (fingerprint of the default game unchanged: `python3 -m sim.tests.fingerprint check`) | Nothing in sim/economy beyond a rebase: `households*.py` is being edited by the counterparty-postings branch, so land after it merges, or touch only the import lines |
| 2 | Climate floors become a kernel function of tile climate; `baskets_by_tile` calls it. | `sim/world/need_basket.py`, `sim/world/climate_needs.py` (read), `sim/engine/economy_port_setup.py`, `sim/engine/geography_port.py` (tile climate) | A hotter tile has no larger warmth floor than a colder one; a tile's floors equal the kernel's for its climate | Geography branch (`civilisations-hold-tiles-and-roads`) changes tile ownership and the map surface the port reads: rebase after it |
| 3 | The aggregate model reads the kernel: floors per need for the civilisation, the one price index, surplus split. | `sim/world/need_demand.py`, `sim/engine/market_demand.py`, `sim/engine/joint_allocation.py` (anchors), `sim/engine/agents_port_capital.py` | Adding an identical good to a need leaves its price index and demand unchanged; at income above the floors the aggregate demand for a need equals the economy's for one cohort of that income; demand rises with income for every need whose weight is positive, and the food share falls (Engel) | Stage 1. Changes the opt-out game's fingerprint on purpose: record a new baseline in the same commit and say so |
| 4 | Strata read the kernel through `SimWorld`: per-need floors, per-need shortfall, no multiple constant. | `sim/agents/stratum_year.py`, `sim/agents/tuning_strata.py`, `sim/agents/protocols.py`, `sim/agents/api.py`, `sim/engine/agents_port_cast.py`, `sim/engine/agents_port_budget.py`, `sim/economy/api.py` (one new question), `sim/engine/economy_port.py` | A stratum whose income covers the floors has zero shortfall; shortfall is monotone non-increasing in income; welfare of a stratum falls when its need prices rise; strata and cohort floors agree for the same tile | Counterparty-postings branch (`sim/agents/stratum_year.py`, `protocols.py`, `agents_port.py`, `sim/economy/households*.py` are all in its diff): do not start until it merges |
| 5 | Capital: engine meeting stops when the agent economy is on; saving flow from the kernel; state lending through a port member. | `sim/engine/economy_capital_market.py`, `sim/engine/society_actors.py`, `sim/engine/agents_port_capital.py`, `sim/world/capital_market.py`, `sim/economy/api.py` | The rate with the agent economy on equals the economy's rate; with it off, the rate rises when funds demanded rise against funds held; founder credit room is never negative | Stage 3 for the saving flow. `society_actors.py` is in the counterparty branch's diff: rebase after it |
| 6 | Merchants: Complaint 115 items 2 to 5, then retire `_external_orders` and the aggregate `foreign_traders` flow once no good depends on them. | `sim/agents/trader*.py`, `sim/economy/merchants*.py`, `sim/economy/foreign.py`, `sim/engine/economy_port_year.py`, `sim/engine/foreign_traders.py`, `sim/engine/foreign_economies.py`, `sim/engine/foreign_actor_trade.py` | A good carried by an actor is not also offered by a stand-in the same year; a trader's cargo moves both ends' prices toward each other, never apart; money conserved across the border | Counterparty branch (trader files). Geography branch if domestic trader routes use new route queries |
| 7 | Retire what the kernel replaced: the unused canned three-good basket and food-share constants in `demand.py` if nothing reads them; `STRATUM_OTHER_NEED_FOOD_MULTIPLE`; the strata wage bridge for the home country. Move the Complaint 115 lines to `Complaints/closed/` with the measurement. | `sim/world/demand.py`, `sim/agents/tuning_strata.py`, `Complaints/115-*.md` | `grep` for the removed names returns nothing; full suite and `--slow` pass | Stages 3 to 6 |

Disjoint sets for parallel agents: stages 1 and 2 share the kernel file, so one agent; stage 3 (world and market
demand files) and stage 4 (agents files) are disjoint from each other and may run together once stage 1 has landed and
the counterparty branch has merged; stage 5 and stage 6 touch different engine and agent files and may run together
after stage 3; stage 7 last.

## 6. What waits on the in-flight branches

- `every-posting-names-a-counterparty`: edits `sim/agents/` (stratum, trader, registry, ledger, protocols, records) and
  engine adapters (`agents_port.py`, `society_actors.py`, `economy_credit.py`, `economy_goods.py`). Stages 4, 5 and 6
  wait for it. The households files under `sim/economy/` are named in its scope too, so stage 1 either lands after it
  or keeps to import lines.
- `civilisations-hold-tiles-and-roads`: reshapes geography and the map surface that tile climate and route queries
  come from. Stage 2 and the domestic-route part of stage 6 wait for it.
- Stage 3 and the kernel's pure code in stage 1 touch neither branch's files and can start now.

## 7. Risks

- Stage 3 and stage 4 change behaviour on purpose: prices in the opt-out game and strata welfare move. Each records
  its fingerprint change and a ranged check (wage-to-grain ratio, urban share, grain more volatile than metals), not a
  dated event, before and after.
- Hiding a wall: the kernel is in `sim/world`, so the economy, engine and agents each import it directly. That is the
  existing rule for standalone models (`PACKAGE_WALLS.md`), not a new door.
- The below-floor rule is the least understood part. Test it by relationship (monotone in income, spending never above
  income) before replacing either version.
