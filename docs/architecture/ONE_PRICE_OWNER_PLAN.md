# One price owner: the agent economy

**Status:** plan; stage 1 built on branch `507-stage-1-solver-is-cost-only` (2026-10-14), the rest not built. Answers `Complaints/507-prices-and-traded-volumes-have-two-owners.md`
(owner decision: the agent economy is the only owner of prices and traded volumes; the engine's price solver
becomes a cost-of-making calculator). Sequel to `ONE_DEMAND_MODEL_PLAN.md` (one household demand kernel) and
Complaint 115 (one economy). Folds in the price-search half of Complaint 513 (stage 8) and the unsold-stock rule
(stage 7).

Rules this plan keeps (CLAUDE.md section 4): no hardcoded outcomes, no content ids in the engine, every
transitional shortcut labelled, no save migration. Behaviour changes on purpose in every stage, so the
fingerprint (`python3 -m sim.tests.fingerprint`) proves nothing here; each stage is proved by relationship tests
(CLAUDE.md 4.2: ranges and relationships, never dated values). Every list below was measured on this branch; the
command that produced it is under it. Re-run before acting.

## 1. What the solver is today, and who reads it

The solver is `prices.solved_prices` (`sim/engine/prices.py`, `solve_prices*.py`). It does three jobs:

1. **Cost of making**: a fixed point over the recipe graph (cheapest technique per good, plant charge at the
   interest rate, rent, capability grades, disposal cost of waste).
2. **Demand**: `joint_allocation.build_demand_anchors` builds a `need_demand.NeedDemandModel` (through
   `market_demand.py`) and uses its clearing prices to split joint costs, cap anchors, mark glutted outputs and set
   scarcity floors (`clearing_with_glut`).
3. **Rent**: ore rent from a fixed demanded quantity (`rent_hours_per_kg_by_ore_material`) and land rent from the
   margin of cultivation for the population (`land_rent_hours_per_hectare`). Both are demand-side prices.

Job 1 stays. Jobs 2 and 3 are deleted from the solver; rent is an input the caller supplies.

### 1.1 Readers of the solver's prices (and what each should read after)

Measure: `grep -rn "solved_prices(\|_price_tables()\|priced_goods_table\|calculated_goods_table\|_material_prices()" sim --include=*.py | grep -v tests`.
"Cost" = a comparison against the cost of making; "pay" = a price someone pays or is shown; "bridge" = code that
exists only to join the solver to the economy.

| Reader (file) | Needs | Reads after |
|---|---|---|
| `incumbent_prices._price_tables`, `_material_prices` (the table itself) | cost | the calculator's long-run table; renamed `making_cost_table`, never called a price |
| `goods_market_api.quote`, `purchase_cost`, `quote_buy`, `sale_proceeds` (every founder, project and actor purchase: `project_materials.material_purchase_cost`, `ui/proto/quote_purchases`, `economy_port.material_price`, `agents_port_budget.material_cost`, `agents_port_revenue.material_price`, `holdings_exposure`) | pay: today table cost times `price_index` times `material_price_factor` times `market_price_ratio` | the economy's price at the acting tile (`sim.economy.api` prices answer plus carriage), no ratio, no table |
| `goods_market_offers.household_prices`, `unit_price`, `_home_basis` (also `economy_materials._material_price_per_kg`, `agents_port_cast`, `agents_port_trade`, `ui_port`, `real_output._close_real_output`) | pay, and which seller (home or partner) | the economy's price; partner landed price stays for goods the economy has no market for |
| `market_clearing.market_price_ratio` and `price_ratio` (bridge; read by `goods_market_api`, `real_price_ratios`, `economy_production`, `ui/market_report`) | pay over cost | deleted; where a report wants price over cost it asks the economy's price and the calculator's cost |
| `economy_port.agent_price_ratio` / `economy_port_year.price_ratio` (bridge) | the economy's price over the solver's cost | deleted |
| `incumbent_prices._coin_metal_price` and `economy_port.goods_price_over_wage` (bridge; read by `trader_cargo`, `living_stock_trade`, `economy_port_year`, `foreign_economies`) | pay: the coin metal's price in coin, carried to the economy's level | the economy's price of the metal (it trades it; the mint already prices it) |
| `real_price_ratios` (`real_price_ratio`, `coin_value_ratio`) | pay, relative | already reads `agent_prices`; its fallback to `market_price_ratio` goes |
| `producer_costs` (`_reference_entry`, `_cost_book`, `entry_cost_ratio`, `concern_cost_ratio`, `founder_concern_offers`, `commodity_floor_ratio`), `entry_cost.CostBook`, `concern_volume`, `techniques_in_use` | cost: a concern's entry cost at input prices, over the incumbents' cost | the calculator at the economy's input prices; the "ratio over incumbents" becomes cost over the economy's price |
| `node_output_market_factor` (read by `economy_production`, `agents_port`, `economy_port.concern_takings`, `projects_venture_quotes`) via `node_revenue_market.market_factor` | cost: net sales this year over net at long-run cost | economy prices over the calculator's long-run table, one function in `node_revenue_market` |
| `node_revenue`, `node_rederive`, `node_output`, `energy_prices`, `data.calculated_goods_table`, `data.priced_goods_table` callers (tree load, node money, `rev` of every node) | cost: long-run value of a node's baskets | the calculator's long-run table (no demand); unchanged in meaning |
| `wage_schedule.build_schedule` (called from `data`, `labour_port`, `opening_money`, `node_rederive`) | cost: the coin metal's hours and the staple's hours, to anchor money per hour and the wage floor at the opening | the calculator, opening only; after the opening money per hour is the economy's unskilled wage (closed 115) |
| `economy_port_setup.opening_values` (`prices`) and `economy_port_late` (prices of goods a late technique allows) | the economy's seed prices | the calculator at the economy's own wages, stage 2 |
| `real_output.opening_prices_in_hours`, `base_basket` | opening prices to weigh output per head | the economy's opening prices (`economy_port_setup` values) |
| `foreign_economies._foreign_economy_facts`, `foreign_routes` (ox, mule), `foreign_capacity` | a partner's prices in home money; the home price of carriers | the economy's price for goods it trades; partner books not yet in the economy stay (see section 6, unclassified) |
| `view_share` | cache key only | the economy's price version |

### 1.2 Readers of the solver-side volumes

Measure: `grep -rnE "_follow_cleared_volumes|traded_ratio|reference_tonnes|_material_market_tonnes|market_available_tonnes|base_basket|household_demand_by_material|market_state\(" sim --include=*.py | grep -v tests`.

| Reader | Needs | Reads after |
|---|---|---|
| `real_output` (`base_basket`, `traded_ratio`, `real_output_lines`, `opening_output_hours`, `_close_real_output`; read by `labour_port.real_output_per_head`, `economy_port` money-income figure, `event_causes`) | volume: tonnes sold now over the opening's, per commodity | `economy.api.traded_volumes` against `opening_quantities` (the economy's own opening basket, `record.opening_basket`) for every good; no reference from the demand model |
| `market_clearing._follow_cleared_volumes` (only late-recipe goods follow the economy, 478) | volume | deleted: every good follows the economy (the reason it did not, see stage 4) |
| `market_demand.household_demand_by_material` (builds `base_basket` units, the static book's demand, `foreign_capacity`) | volume: opening demand | deleted for home; `foreign_capacity` uses the economy's partner opening where the partner is inside it |
| `goods_market_api.quote["market_available_tonnes_per_year"]`, `economy_materials._material_market_tonnes` (limit on a founder buy or sale) | volume the market takes | the economy's offered and bid quantity at the tile (needs a new api read, stage 4) |
| `market_clearing.market_state` (read by `goods_market_api.state`, `agents_port_groups`, `agents_port_stakes`) and the static book `_market_outcome`, `_market_conditions`, `sim/world/market.py` | volume sold, displaced producers, unsold | the economy's record: sold, unsold and unmet per good and area (`record.volumes` and the books) |
| `economy_goods` category model (founder side) | `output_per_head` only | unchanged; follows stage 4 |

## 2. The cost calculator

What it keeps (this is the physical part of the solver):

- recipe cost: inputs, labour at wages, rent, plant charge at the interest rate (`recipe_cost_and_allocation`,
  `unit_cost`-style), energy carriers and capability grades (`capability_*`, `band_prices`), the cheapest
  technique per good under a held technology set (`techniques_available_to`, `chosen_recipe_by_material`), cycles
  and the reachability pass (`compute_resolvable_materials`), disposal cost of waste as a physical cost
  (`disposal_cost.py`), joint cost shared by the value of the outputs at reference prices handed in (the mass split
  stays as the fallback where none is given, labelled).

What is deleted:

- demand anchors (`joint_allocation.build_demand_anchors`, `cap_anchors`, `NeedDemandAnchors`, scarcity floors);
- clearing and glut handling (`clearing_with_glut`, `glutted_materials`, the glut branch of `allocate_joint_cost`,
  the surplus-at-disposal branch); a waste with no buyer is the economy's business (a seller offers it below zero,
  ECONOMY_AGENTS.md "Sellers' reservations");
- the fixed demanded quantity behind ore rent and the population-sized margin behind land rent: rent comes in as
  an argument (the economy's land rent per hectare, `economy.api.land_rent_per_hectare`; for ore, the mine's
  own marginal cost, with the scarcity premium left to the market);
- the in-game warm start and its tolerance only if the fixed point is no longer needed at runtime (stage 5
  decides: the long-run table needs it, the entry decision does not).

New signature (a pure function in the engine now, a `sim/world/` kernel later so `sim/economy/unit_cost.py` and
`notional.cheapest_cost` can share it, since the economy already holds two live-price copies of this arithmetic):

    cost_of_making(
        good,                     # material key
        techniques,               # frozenset of held gate nodes (or one recipe id)
        input_price_of,           # function good -> money per unit, or None (a missing input makes the cost infinite)
        wage_of,                  # function trade -> money per hour
        rate,                     # interest rate for the plant charge
        rent_of=None,             # function land/ore key -> money per unit; None means rent is not charged
        reference_price_of=None,  # function good -> price, used only to split a joint run's cost by value
        include_plant=True,       # False: the running cost of a built plant
    ) -> MakingCost | None        # unit cost, chosen recipe id, per-input and per-trade shares

and a closure form for the long-run reference (tree load, node money, the opening's seed):

    long_run_costs(techniques, wage_of, rate, rent_of, civilisation) -> {good: cost, chosen recipe, basis}

It reads no population, no income, no demand. Both are deterministic in their arguments and cached on them
(`solve_cache`).

## 3. Stages

Order: 1, then 2, then 3, 4 and 5 in parallel (disjoint files), then 6, then 7, then 8. Stage 7 needs only the
economy and may start after stage 1; stage 8 needs stages 3 and 4.

Relationship tests named below exist today unless marked (new). Run all with
`python3 -m sim.tests --slow --only <names>`; the whole-game checks are `python3 sim/simulator.py economy-check`
(staple price over labour cost, wage over floor) and the baseline ensemble (`sim/engine/baseline_ensemble.py`,
`test_baseline_ensemble.py` for the harness; a real run is slow and manual).

### Stage 1: the solver loses its demand model

**Done** (branch `507-stage-1-solver-is-cost-only`): the demand model, clearing, glut handling and the fixed-quantity
rent are out of the solver; `making_cost.cost_of_making` and `long_run_costs.long_run_costs` are exposed; readers
untouched. Learned, for later stages: (1) a joint run's default split values an output at its sole-output route's price this round, else at
nothing if it is a recorded waste (`UNPRICED_WASTE_VALUE`, `retire` stages 3 and 7), else by mass
(`UNPRICED_OUTPUT_VALUE_PER_KILOGRAM_SHARE`, `retire` stage 2); mass for tar made the retort undercut the sole
charcoal route and emptied the charcoal nodes' lines, so the data's waste list stands in for the glut verdict; a
caller's `reference_price_of` wins, and one below zero marks a waste priced at no less than minus its disposal
cost, so the waste rule and sink services reach a price only once the economy hands in such a reference
(stages 3 and 7); the Rome, Han and Mexica tables equal the old ones to four figures bar the tar, the England and
Norse silver rises to its mining cost because population no longer sizes its demand (stage 2 sees it in the coin); (2) rent is an argument; the stand-in
is `rent_standin.py` (`STAND_IN_ORE_DEMAND_SHARE_OF_OPENING_OUTPUT`, `retire` stage 5), and `farmed_hectares` stays
an input of that stand-in only; (3) `DERIVED_DEMAND_MAX_SWEEPS` stays: `NeedDemandModel.total_demand` still serves the
static book and `base_basket`, so it goes with them in stage 4 or 6; (4) `supply_per_year` left the needs schema with
the scarcity floors; (5) `joint_floor.py` and `need_trial_fast.py` are deleted; (6) every engine source change stales
the price-solve and agent-economy caches and `openings/`, which stage 2 regenerates.

Moves: job 2 deleted; the table becomes pure cost; the calculator functions of section 2 are exposed. Readers are
untouched (they still read a table, now of cost), so the stage merges alone.

Proof (relationships):
- cost rises with each input price, wage and rate, and falls when a cheaper technique is held (new
  `test_making_cost_relations`, built on `price_solver_helpers.py`);
- a good made by one recipe costs exactly that recipe's bill (extend `test_engine_prices.py`);
- a joint run's outputs together recover the run's cost, split by the reference prices given (rewrite
  `test_joint_allocation.py`, `test_joint_byproduct_floor.py`; delete the glut and anchor checks);
- era gating and reachability unchanged (`test_price_solver_era_gate.py`, `test_price_solver_cycles.py`,
  `test_price_solver_unreachable_material.py`, `test_prices_at_reachable_techniques.py`).

Files: `sim/engine/prices.py`, `solve_prices.py`, `solve_prices_core.py`, `solve_prices_round.py`,
`solve_prices_reach.py`, `joint_allocation.py`, `entry_cost.py`, `solve_cache.py`; `sim/world/need_demand.py` and
`need_final_demand.py` lose the anchor classes only (the household kernel stays, other readers remain in
`market_demand.py`, `labour/workforce_spinup.py`); tests `test_joint_*`, `test_price_solver_*`, `test_engine_prices*`.

Deletes (`python3 sim/constants.py --burndown`): `MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR`
(`joint_allocation`), `DERIVED_DEMAND_PRICE_ELASTICITY`, `TECHNOLOGY_LOOKAHEAD_DEPTH`, `DERIVED_DEMAND_MAX_SWEEPS`
(`need_demand`).

### Stage 2: the opening seeds the economy from the calculator

The economy's first prices still have to come from somewhere, and now they come from one place: the calculator at the
opening wages, rates and rent, in the economy's unit, then the hidden spin-up lets markets move them.

Moves:
- `economy_port_setup.opening_values` takes `prices` from `long_run_costs` (partner goods from the partner's own
  calculator run, as `economy_port_partners` does now);
- `economy_port_late` seeds a late good at the calculator's cost at the economy's live input prices and wages
  (not at the engine table), which is also what `notional.cheapest_cost` would show;
- `wage_schedule.build_schedule` anchors money per hour and the wage floor on calculator costs (coin metal hours,
  staple hours); this is the last use of the solver for wages;
- `opening_money`, `data.py` (`_STARTING_SCHEDULE`, `schedule_of_civilisation`) follow;
- land and ore rent at the opening are computed from the physical margin (`sim/world/land.py`, `deposits.py`) once,
  here, and handed in as `rent_of`; this is labelled `temporary_heuristic` (opening only) because the margin's
  quantity is a stand-in until a settled economy exists to read rent from;
- regenerate the shipped openings: `python3 sim/simulator.py openings --prune` (Complaint 497).

Proof:
- opening price of a staple, over its cost of making at the opening wages, is within a band around one, and the
  opening price level does not depend on any demand constant (new `test_opening_seeds_are_costs`);
- the spin-up price level settles instead of cycling (Complaint 473: `test_labour_core_opening.py` fixture and
  `economy-check`), since the capacity and income mismatch named there came from seeding with anchors;
- `test_start_opening_warning.py`, `test_shipped_openings.py`, `test_shipped_opening_game.py`,
  `test_wage_floor_and_coin_standard.py`, `test_wage_provider.py`, `test_port_opening_stores.py`,
  `test_economy_opening_stores.py`, `test_opening_floor_and_thin_trades.py`.

Files: `sim/engine/economy_port_setup.py`, `economy_port_late.py`, `economy_port_partners.py`, `wage_schedule.py`,
`opening_money.py`, `data.py`, `labour_port.py` (schedule call), `node_rederive.py`, `shipped_openings_build.py`.

**Done** (branch `507-stage-2-opening-from-costs`, 2026-10-15). What was built, and what it showed:

- Seeds. `economy_port_costs.opening_costs` takes the opening prices from `long_run_costs` at the opening wages, the
  market rate and the labelled rent stand-in (`long_run_costs.opening_rent_of`); a late good is seeded by
  `making_cost.cost_of_making` at the economy's live prices and wages (`economy_port_late.late_goods_costs`). Both agree
  with the old engine table to a few per cent (the rate band and the farmed-area band differ). `wage_schedule`, `data.py`
  and `opening_money` are untouched: the schedule's money per hour is still the coin metal's table cost, and the game's
  money is still repriced to the economy's wage when the economy opens.
- One final demand sizes the opening (`sim/economy/opening_income.py`, `opening_runs.py`, `opening_metal.py`): household
  income is the fixed point of income and the demand it pays for (workers paid alike out of the labour share, owners
  by what they own); each producer's plant is the runs it is to work divided by the share of plant that works at the
  opening prices; the workforce is placed for the runs producers expect to sell, not for full plant; producers open holding
  the inputs of their planned runs; processors are held to the supply of a good only deposits make; each good is made by
  its cheapest recipe up to what deposits allow, then the next; a joint run's co-product counts only up to the demand
  for it; the metal the money loses a year is a final demand (the mint's).
- Coin worth. `economy_port_coin.priced_at_the_margin`: the coin standard fixes the metal's price in coin, and the metal
  the money needs is made at the margin, so the other prices and wages are scaled by the marginal over the table cost
  (`coin_worth_scale` in the saved opening). The money stock is what the transactions it carries need, in a coin worth
  what that metal costs.
- `spin_up_money_supply` passes without being loosened. The chain behind the coin metal exists from the opening and
  the mint replaces what wear takes. Measure: `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

What it showed (the hypothesis that seeding from costs stops the cycling is only partly borne out):

1. The price level no longer cycles with a period of decades, but it does not settle either: over sixty years it falls by a
   large multiple, the unskilled wage falls with it and the hired share of hours climbs. `game.economy.spin_up_result()`
   says not settled for every civilisation and the openings command prints it.
2. Cause: the labour market clears at the households' outside option, a small share of the wage the cost table
   assumes, from the first year. Prices follow wages down slowly and employment grows into the gap. Realised income in
   year zero is therefore a small share of the opening figure whatever the opening income is. Seeding the wage at the
   outside option does not remove it: prices and the outside option both scale with the wage, so only the money stock
   fixes the level. This needs a model of that adjustment (stage 5 rent, stage 7 price search), not a different seed.
3. The income fixed point lands at subsistence for a household that saves part of any surplus: with a propensity to
   spend below one the only income at which a household spends all it is paid is the cost of its floors. The opening
   is therefore a stationary subsistence economy and the surplus the old opening gave (and the growth it started) is gone.
   Fixtures that need a household with a surplus say so (`economy_fixture.households_with_a_surplus`).
4. The opening costs about twice what it did to build (several openings of one economy; `python3 -m sim.tests --slow
   --only shipped_opening_game`), not a year's step.

Acceptance measure (`python3 sim/simulator.py opening-checks`, before and after on the full-length openings): the money
against wear passes for Rome and England now, the English wage over floor passes, and the sited ores of Mexica and the Norse pass.
The coin metal over making cost is worse everywhere it fails, the Roman wage over floor and the English sited ores newly
fail, and no spin-up settles. The coin metal's price is fixed by the coin standard while its cost follows a wage that
keeps falling, so that check waits on the wage settling, not on the seed. `test_full_length_opening_checks.py` lists
what is still expected to fail and why.

Later stages: stage 3 and 7 should hand the calculator reference prices (a joint run's split used mass or the sole
route's price; the opening now uses demand); stage 5's rent replaces the stand-in; stage 7's unsold-stock search meets the
input stocks the opening now seeds. The 519 ratios: full-length openings put every sited ore within an order of magnitude
of its cost; the suite's short spin-up still shows some above it (523).

### Stage 3: prices to pay come from the economy

Moves: the buyer-side rows of 1.1. `goods_market_api.quote/purchase_cost/sale_proceeds` read the economy's price at the
acting tile (`sim.economy.api`; add a `price_at(good, tile)` read if `shown_prices_of` is too coarse), keeping
carriage and the partner landed price. The climb of price as an order is filled (`_price_factor_across_purchase`)
becomes `api.price_response` (it already clears the book again with an extra bid). `_coin_metal_price` and
`goods_price_over_wage` are deleted. `market_price_ratio` and `agent_price_ratio` are deleted; their report readers
(`ui/market_report`, `real_price_ratios`) read price and cost directly.

Proof:
- a founder buying a tonne pays the economy's tile price plus carriage, and the project bill equals tonnes times that
  price (new `test_purchase_reads_economy_price`; extend `test_demand_answers.py`, `test_state_demand_answer.py`);
- a larger order costs more per tonne (monotone) and a good with no seller has no price
  (`test_no_seller_no_price.py`, `test_whole_game_no_seller_no_price.py`);
- the coin metal in the mint and in trader cargo prices at one number (`test_home_cargo_price.py`,
  `test_foreign_prices_follow_goods.py`, `test_economy_bronze_market_price.py`);
- a technique that lowers a good's cost lowers what the founder pays within some years, in a whole game
  (extend the 478 test family).

Files: `sim/engine/goods_market_api.py`, `goods_market_offers.py`, `project_materials.py`, `incumbent_prices.py`
(`_coin_metal_price` only), `economy_port.py`, `economy_port_year.py` (`price_ratio`), `economy_materials.py`,
`agents_port_budget.py`, `agents_port_revenue.py`, `agents_port_cast.py`, `agents_port_trade.py`,
`holdings_exposure.py`, `real_price_ratios.py`, `trader_cargo.py`, `living_stock_trade.py`, `foreign_economies.py`
(price lines), `sim/ui/market_report.py`, `sim/ui/proto/quote_purchases.py`, `sim/economy/api.py` (new read only).

Deletes: bridge `goods_price_over_wage`, `price_ratio`/`market_price_ratio`, `MATERIAL_TRADE_SELL_SHARE_OF_BUY` if
the sell price becomes the economy's bid (decide in the stage; it is a `temporary_heuristic`).

### Stage 4: traded volumes come from the economy

Moves: `real_output` measures every commodity as the economy's `traded_volumes` over `opening_quantities`, weighted
by the economy's opening prices; `_follow_cleared_volumes` and the `reference_tonnes` split are deleted;
`market_available_tonnes_per_year` is the economy's offered quantity at the tile; `base_basket` no longer calls
`household_demand_by_material`.

Why 478 stopped at late goods: wiring every good swung output per head because the engine's reference volume and the
economy's cleared volume disagree for the opening goods. With one owner the reference is the economy's own first
settled year, so the ratio starts at one by construction. The stage records that baseline in `stored["volume_baseline"]`
for all goods (today only `late_goods`).

Proof:
- output per head is one at the baseline and no commodity ratio is far from one in a no-intervention run
  (`test_real_output.py`, new guard over `economy-check`);
- a productivity technique raises output per head; a population fall without one does not
  (`test_real_output.py`, `test_population_farm_technique.py`);
- the founder cannot buy more than the market offers (new `test_purchase_limited_by_offered_volume`).

Files: `sim/engine/real_output.py`, `market_clearing.py` (`_follow_cleared_volumes`, `traded_ratio` callers only),
`economy_port.py` (`agent_cleared_ratio`), `economy_port_year.py` (`cleared_ratio`, baseline), `goods_market_api.py`
(`market_available_tonnes_per_year`), `economy_materials.py` (`_material_market_tonnes`), `labour_port.py`,
`event_causes.py`, `sim/economy/api.py` (offered quantity read).

### Stage 5: cost comparers use the calculator at the economy's prices

Moves: `producer_costs`, `entry_cost.CostBook`, `concern_volume`, `node_revenue_market`/`node_output_market_factor`,
`techniques_in_use` read `cost_of_making` with `input_price_of` and `wage_of` from the economy; the long-run table
stays the reference for node `rev`. Rent for live calls is the economy's land rent (`land_rent_per_hectare`) and the
mine's cost. The in-game warm start in `prices.py` is dropped if no runtime call needs the closure.

Proof:
- a concern's takings equal its baskets at economy prices (new `test_node_factor_is_economy_over_cost`; extend
  `test_engine_prices_civilization_rent.py`, `test_price_solver_rent.py`, `test_price_solver_land.py`);
- a plant that exists offers at its running cost, a new one is judged at full cost
  (`test_economy_expansion_price.py`, `test_economy_input_price_expectations.py`);
- price over making cost in a settled economy stays in a band for traded goods (`economy-check`).

Files: `sim/engine/producer_costs.py`, `entry_cost.py`, `concern_volume.py`, `node_revenue_market.py`,
`economy_production.py` (factor), `projects_venture_quotes.py`, `agents_port.py` (takings), `techniques_in_use.py`,
`prices.py` (cache and warm start).

Deletes: `ENGINE_SOLVE_TOLERANCE` and `INTEREST_RATE_BAND` if the closure is no longer iterated at runtime.

### Stage 6: the engine's static commodity book goes

The static book (`market_clearing._market_outcome`, `_market_conditions`, `sim/world/market.py`, `market_demand.py`)
is the last clearing the engine owns. After stages 3 to 5 its readers are `market_state` (groups, stakes) and the
partner books.

Moves: `market_state` reads the economy's record (sold, unsold, unmet, displaced); `market_clearing.py` and
`market_demand.py` are deleted for home goods; `agents_port_cast.household_basket` reads the economy's basket
(`ONE_DEMAND_MODEL_PLAN.md`); `foreign_actor_trade` keeps `sim/world/market.py` only for partners outside the
economy (listed in section 6).

Proof: `displaced_producers`, `tithable_sales_value` and the interest groups' stakes equal the economy's sold and
unsold figures (new `test_market_state_is_economy_record`); `test_foreign_actor_trade.py`, `test_trader_cargo_book.py`.

Files: `sim/engine/market_clearing.py`, `market_demand.py`, `goods_market_api.py` (`state`), `agents_port_groups.py`,
`agents_port_stakes.py`, `agents_port_cast.py`, `foreign_capacity.py`, `core.py` (mixin list), `sim/world/market.py`.

Deletes: `MEAN_INCOME_HOURS_PER_CAPITA`, and the book's constants in `sim/world/market.py`
(`DEFAULT_DEMAND_PRICE_ELASTICITY`, `SHORT_RUN_SUPPLY_PRICE_ELASTICITY`, `STOCK_FLOOR_RATIO`, `DEFAULT_CEILING_RATIO`,
`CAPACITY_ADJUSTMENT_RATE`, `CAPACITY_MAXIMUM_STEP`, `STOCK_RETENTION`) unless partner books still use them.

### Stage 7: price search for unsold stock

Independent of the solver; it needs only the economy and can run in parallel with stages 2 to 6, but its tests are
cleaner after stage 3 (no ratio in the way).

Today a seller's ask falls by `UNSOLD_ASK_MARKDOWN_SHARE` of the expected price per year (`seller_offers.py`,
`producers.py`), so a good priced far too high needs many years to find buyers (the thin-market and 502 cases).
Change: within one clearing, a seller left holding unsold stock lowers its ask and the market clears again, repeating
until the stock sells or the ask reaches the seller's floor, which is what a unit is worth to it unsold: its
replacement cost or holding value, never below the cost of making it (`seller_offers` already computes `unit_value`).
Rounds are bounded by a convergence rule (no seller moves), not a count, and only sellers with unsold stock are
revisited, so the cost stays near one clear per market (Complaint 497: measure with `step 3` from a saved game).
The raise rule (`ask_raise.py`) stays for sold-out sellers, with the between-year markdown replaced by this search.

Proof:
- a seller with unsold stock sells it the same year when buyers exist at any price above its floor (new
  `test_unsold_stock_sells_within_year`);
- no ask ends below the seller's floor (`test_asks_follow_sales.py`, `test_economy_producer_stale_ask.py`);
- a good opened far above its making cost reaches it within a year, not a decade (new, replaces the thin-market
  blend's reason: `test_economy_thin_market_price.py`);
- staple prices do not oscillate more than before (`economy-check`, `test_economy_store_usual_price.py`).

Files: `sim/economy/seller_offers.py`, `seller_pricing.py`, `year_goods.py`, `producers.py`, `ask_raise.py`,
`sim/labour/market/asks.py` (comment only).

Deletes: `UNSOLD_ASK_MARKDOWN_SHARE`, `UNSOLD_PROBE_SHARE_OF_CAPACITY`, `IDLE_SALE_SHARE`; then
`notional.thin_market_prices` and `THIN_MARKET_SHARE_OF_OPENING_DEMAND` (a thin market no longer holds an
unreasonable price for years).

### Stage 8: farm effort follows the food price (Complaint 513)

Needs stage 3 (one food price) and stage 4 (one traded volume). Not a solver reader today: `LabourAllocationMixin.
_allocate_farm_workforce` sizes farm hands to `farm_workers_needed`, so nutrition sits at need.

Moves: farm hours are chosen by households and farms against the price of food and the wage elsewhere (both from the
economy); a cheaper calorie raises intake toward `limit_satiation` (`sim/world/need_basket.py`), and past satiation
the surplus is stored, sold, fed to animals or wasted; farmers leave farming when food is cheap and the price
recovers. The satiation level is a declared biological limit with a source (513 owner decision).

Proof: with spare land a food technology raises nutrition and then population, up to the satiation limit and no
further (the two checks in `test_population_farm_technique.py` change meaning on purpose: write the new relationship
first); farming share of labour falls when the food price falls relative to the wage (new
`test_farm_effort_follows_price`); no input to the allocation is the engine's food need.

Files: `sim/engine/labour_allocation` mixin (`LabourAllocationMixin`, find with
`grep -rn "_allocate_farm_workforce" sim`), `sim/world/need_basket.py` (limit declaration), `sim/world/agriculture.py`
call sites.

Deletes: the exact-fit allocation and `farm_workers_needed` as a rule; `HOUSEHOLD_FARM_PRICE_RATIO_FLOOR` and
`FARM_LABOUR_HOURS_PER_HA` in `economy_goods.py` where the household farm choice replaces them (check
`python3 sim/constants.py --burndown`).

## 4. Parallel plan

| Stage | Files owned (no overlap with a concurrent stage) |
|---|---|
| 1 | `prices.py`, `solve_prices*.py`, `joint_allocation.py`, `entry_cost.py`, `solve_cache.py`, `need_demand.py` (anchors) |
| 2 | `economy_port_setup.py`, `economy_port_late.py`, `economy_port_partners.py`, `wage_schedule.py`, `opening_money.py`, `data.py`, `labour_port.py`, `node_rederive.py` |
| 3 | goods market, purchase and port-price files listed in stage 3 |
| 4 | `real_output.py`, `economy_port.py` (volume lines), `economy_materials.py` (volume), `event_causes.py` |
| 5 | `producer_costs.py`, `concern_volume.py`, `node_revenue_market.py`, `economy_production.py`, `techniques_in_use.py` |
| 6 | `market_clearing.py`, `market_demand.py`, `agents_port_groups.py`, `agents_port_stakes.py`, `foreign_capacity.py`, `sim/world/market.py` |
| 7 | `sim/economy/seller_offers.py` and neighbours |
| 8 | farm allocation and `economy_goods.py` farm constants |

Stages 3 and 4 both touch `economy_port.py`, `goods_market_api.py` and `economy_materials.py`; give them different
functions and say so in each prompt, or run them in sequence. Stage 6 follows both.

## 5. Risks

- **Speed (Complaint 497).** Stage 1 and 5 shrink the runtime solve (no demand model, no fixed point for an entry
  decision) and should make a year cheaper; stage 7 may add clears. Measure `echo "step 5" | python3 sim/simulator.py
  play --session FILE` before and after each stage; a stage that makes a year slower says so in its commit.
- **Save and load (CLAUDE.md 4.6).** Stages 2 to 6 change what is saved (opening values, `volume_baseline`, the
  static book's `market_book`, `stored` keys). Drop fields; no shim, no `if "old_key"`. Round trip must still hold:
  `test_saveload*` and `--session` every command.
- **Shipped openings.** Any change to economy or engine source stales `openings/`; stage 2 regenerates them
  (`python3 sim/simulator.py openings --prune`) and every later stage that changes the opening's inputs must too,
  before a PR (`python3 -m sim.tests --slow` checks they load).
- **Opening quality.** Seeding from costs gives an opening in which every price equals cost, with no scarcity rent.
  The spin-up must find it (Complaint 473); if it cannot, the fix is in the economy, not a seeded premium.
- **Rent without a demand model.** Ore and land rent are the two places the solver used demand for a physical-looking
  number. Until the economy supplies them (stage 5) the opening carries a labelled stand-in.
- **Joint products without anchors.** The split uses reference prices from the economy where known and mass where not;
  a co-product with no market may price oddly. Keep the labelled fallback and count it in `--burndown`.
- **Baseline drift (CLAUDE.md 4.2).** Each stage may worsen the baseline; judge it on the ensemble's distributions
  (population range, urbanisation share, wage-to-grain ratio, technology windows), not on dated events.
- **Three copies of cost arithmetic.** `solve_prices_core`, `sim/economy/unit_cost.py` and `notional.cheapest_cost`.
  Left as is through stage 8; merge into one `sim/world/` kernel afterwards (not a stage because it changes no
  behaviour and its proof is the fingerprint).

Heuristics each stage deletes are under each stage. Count what is left after each:
`python3 sim/constants.py --burndown` (this plan states no totals; they go stale).

## 6. Unclassified or deferred readers

- Partner economies outside the agent economy (`foreign_economies`, `foreign_actor_trade`, `foreign_capacity`):
  their prices come from the solver for the partner's techniques and their volumes from `sim/world/market.py`.
  Unclassified until the partners are inside the economy (`partners_in_agent_economy`); they keep a calculator
  call and the static book for now, which is why stage 6 keeps `sim/world/market.py`.
- `economy_goods` category model (founder side): reads only `output_per_head` today; not classified as a price owner,
  but the number of `temporary_heuristic` constants it holds (`python3 sim/constants.py --burndown | grep GOODS_`)
  suggest it is a second demand model for the founder's goods and should be audited after stage 4.
- `labour/workforce_spinup.py`: uses the household kernel's budget weights, not the solver; unaffected.
- `notional.thin_market_prices`: measured, it is not a solver reader. It blends toward the economy's own cost
  (`unit_cost`, `cheapest_cost`) and the economy's `opening_basket`. Complaint 507 lists it as a bridge; it is a
  patch for slow markdown, deleted by stage 7, not by moving a reader.
