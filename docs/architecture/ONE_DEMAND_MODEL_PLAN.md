# One household demand model, and the other duplicates Complaint 115 still lists

**Status:** done. The kernel is `sim/world/need_basket.py` (pure basket types and price functions, climate floors in
`climate_basket`, `basket_with_floors`, `mean_climate_basket`); `sim/economy/households_basket.py` re-exports it and
prices a basket from a market view; `NeedDemandModel.final_demand` takes the price index, floors and surplus split from
it; strata pay the floor of each need in turn (`stratum_year.run_year`). The agent-economy-off mode and its capital
market were deleted (owner decision recorded in `Complaints/closed/115-multiple-parallel-models-need-an-authoritative-one.md`).
Sections 1 and 2 describe the three models as they were compared; find the current owner of any name with
`grep -rn <name> sim`.

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

- `sim/markets/household_needs.py`: builds the model and its income bins for the year's household demand.
- `sim/actors/world_credit.py`: income bins to a savings flow.
- `sim/economy/households_cohort.py`: only `income_bins`, to cut a tile into income classes.
- `sim/labour/workforce_spinup.py`: `budget_weights_by_good`, `input_coefficients_per_unit_output`.

### 1.2 The agent economy's household baskets (`sim/economy/households_basket.py` and its orders)

What it computes. `make_basket` turns `needs.json` plus recipes into `NeedSpec` records; `need_prices` prices each need
on a tile from the market view, with a constant-elasticity mix inside the need, a price index per need unit, and a
price ceiling above which a buyer stops buying a good. `households_orders.goods_orders` then turns a cohort's cash,
income, expectations and savings target into orders: floors, plus the surplus split by need weight, limited by
satiation, thinned for durables already held (`_durable_ratio`), and routed to goods that are affordable.
`baskets_by_tile` (`sim/markets/port_setup.py`) replaces the floors of climate needs with each tile's climate floor
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

Inputs. The engine's own food cost (`subsistence_cost_per_person_year` (`sim/actors/world_people.py`): the dole material priced by
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

### 2.1 Stages

Stages 1 to 5 are done and stages 6 and 7 are recorded in Complaint 115 (closed). The kernel is `sim/world/need_basket.py`
(with `sim/world/climate_needs.py`); the aggregate model (`sim/world/need_demand.py`, `sim/world/need_final_demand.py`)
and the strata (`sim/agents/stratum_year.py`) read it. The agent-economy-off mode, its capital market and the engine's
merchant stand-ins were deleted by the owner's decision, so no staged work remains in this file. Find the current owner
of any name with `grep -rn <name> sim`.

## 3. Risks

- Stage 3 and stage 4 change behaviour on purpose: prices in the opt-out game and strata welfare move. Each records
  its fingerprint change and a ranged check (wage-to-grain ratio, urban share, grain more volatile than metals), not a
  dated event, before and after.
- Hiding a wall: the kernel is in `sim/world`, so the economy, engine and agents each import it directly. That is the
  existing rule for standalone models (`PACKAGE_WALLS.md`), not a new door.
- The below-floor rule is the least understood part. Test it by relationship (monotone in income, spending never above
  income) before replacing either version.
