# Caches, port objects and invalidation points

**Status:** draft, task 1.5 (the inventory it asks for, feeding 1.2). Static scan of `e8b004c`; nothing run.

## Port objects

Adapters that hand a package or a caller the engine. Each one's members become a declared view list (packages) or stay as the UI/agent edge (`ui_port.py`).

| File(s) | Files | Lines | What it hands over |
|---|---|---|---|
| `sim/engine/labour_port.py` | 1 | 388 | `LabourWorld`: the labour package gets the engine member by member; the `labour` property caches `Labour` in `Sim.__dict__['_labour']` (`labour_port.py:387`) |
| `sim/engine/geography_port.py` | 1 | 71 | `geography` and `world_map` properties cached in `Sim.__dict__` (`geography_port.py:62,70`) |
| `sim/engine/disease_port.py` | 1 | 314 | the disease package, plus five per-year entries cached in `Sim.__dict__` (`disease_port.py:107,194,208,253`) |
| `sim/engine/economy_port.py` | 1 | 419 | the `economy` property; the `Economy` object cached in `Sim.__dict__['_economy_port']` (`economy_port.py:418`) |
| `sim/engine/economy_port_*.py` | 26 | 2390 | the economy package's inputs and outputs, year by year (seats, sites, cargo, bank, timber, cropland, trace, ...) |
| `sim/engine/agents_port*.py` | 21 | 1602 | the agents package's `SimWorld` adapter: each member is a read or a command for an actor |
| `sim/engine/goods_market*.py` | 4 | 647 | `GoodsMarket` and its party/pricing/offers/imports parts |
| `sim/engine/ui_port.py` | 1 | 237 | every engine name `sim/ui` uses, re-exported by name, plus public wrappers for the private `Sim` members the UI reads |
| `sim/engine/ui_data.py` | 1 | 71 | UI data loaders |
| `sim/engine/ui_commands.py` | 1 | 126 | command specs for the protocol |
| `sim/engine/mod_effects.py` | 1 | 160 | the supported ways a mod changes the world (pay, move goods, kill, move people, transfer tile, write store, record event) |

Hand-held ports on `Sim.__dict__` found by the scan: `_labour`, `_geography`, `_world_map`, `_economy_port`, `_actor_registry`, `_seat_facades`. A load rebuilds them; assembly's `rebind(state)` replaces that.

## Version counters and invalidation points

| Hook | Fires when | Call sites (excluding the definition) |
|---|---|---|
| `_done_changed` | finishing, forgetting or granting a technique (the `done` set) | 16: `sim/engine/node_rederive.py:38`, `sim/engine/society_hazards.py:610`, `sim/engine/core_step_phases.py:516`, `sim/engine/core_step_phases.py:590`, `sim/engine/core.py:547`, `sim/engine/core.py:1825`, `sim/engine/projects_staffing.py:753`, `sim/engine/economy_goods.py:424`, `sim/engine/economy.py:271`, `sim/engine/economy_materials.py:389`, `sim/engine/economy_production.py:333`, `sim/engine/economy_production.py:549` and 4 more |
| `_operating_changed` | a technique starting or stopping running | 6: `sim/engine/node_rederive.py:39`, `sim/engine/economy_goods.py:424`, `sim/engine/economy.py:233`, `sim/engine/economy_production.py:333`, `sim/engine/economy_production.py:556`, `sim/engine/opening_money.py:35` |
| `_active_changed` | a project starting, stopping or finishing | 2: `sim/engine/economy.py:245`, `sim/engine/economy_materials.py:389` |
| `_workforce_changed` | any change to `household.employees` | 1: `sim/engine/economy.py:254` |
| `_reset_economic_caches` | load and seat switch: wipes every transient economic cache | 3: `sim/engine/core.py:587`, `sim/engine/seat_handover.py:70`, `sim/engine/core_seats.py:51` |
| `bump_*_version` | the five counters on the household facade (`sim/agents/household.py:455-490`) | 6: `sim/engine/economy.py:223`, `sim/engine/economy.py:228`, `sim/engine/economy.py:237`, `sim/engine/economy.py:249`, `sim/engine/projects_ventures.py:258`, `sim/engine/projects_ventures.py:326` |

The counters are read as cache keys at: `done_version` 15, `operating_version` 17, `active_version` 2, `workforce_version` 14, `institution_units_version` 3 sites (`grep -rn <name> sim mods --include=*.py | grep -v /tests/ | grep -v 'def ' | wc -l`).

`_InvalidatingDict` (`sim/invalidating.py`, 347 lines) wraps `household.employees`, `projects.active` and `projects.business`/`done` so a mutation calls the hook; it is referenced at 20 sites. In the new design each of those mutations is a command and the wrapper goes.

## Channels proposed

The channels the views name, with the module that bumps them and the number of views that depend on each. A command bumps the channels of the views whose inputs it changes.

| Channel | Owner | Views depending on it |
|---|---|---|
| `active` | `projects` | `active_projects`, `project_cost`, `committed_cost`, `project_risk` |
| `actor_trade` | `foreign_trade` | `actor_trade` |
| `campaigns` | `campaigns` | `armies`, `campaign_sites`, `stability` |
| `capital_market` | `finance` | `market_rate`, `capital_market` |
| `cast` | `actors` | `cast`, `concern_counts`, `actor_staff` |
| `coin` | `coin` | `coin_stock`, `price_level`, `coin_metal` |
| `coverage` | `disease` | `coverage` |
| `dealings` | `seats` | `dealings` |
| `debt` | `finance` | `spending_power`, `credit_limit`, `debt_status`, `debt_interest_rate` |
| `demand` | `materials` | `material_demand`, `resource_throttle`, `project_materials` |
| `deposits` | `resources` | `deposits` |
| `diffusion` | `diffusion` | `diffusion_index` |
| `disclosure` | `diffusion` | `disclosure` |
| `disease` | `disease` | `disease_burden`, `epidemic_forecast` |
| `done` | `knowledge` | `techniques_held`, `visibility` |
| `done` | `mechanics` | `effect`, `corpus`, `patronage` |
| `done` | `production` | `revenue_estimate`, `techniques_in_use` |
| `done` | `projects` | `project_cost`, `rebuild` |
| `farm` | `agriculture` | `farm_holdings`, `farm_sites`, `wild_stock` |
| `food` | `demography` | `food_eaten` |
| `forest` | `resources` | `forest_and_nitre` |
| `founder` | `seats` | `founder` |
| `freight` | `freight` | `carrier_models`, `trader_economics`, `route_dues` |
| `goal` | `seats` | `goal` |
| `goods` | `markets` | `household_prices`, `others_trade`, `market_state`, `goods_category_factors`, `household_demand`, `market_absorption`, `agent_economy` |
| `groups` | `polity` | `interest_groups` |
| `hazards` | `hazards` | `hazard_figures`, `hazard_relief` |
| `herds` | `living_stock` | `stock_status`, `garrison` |
| `hours` | `workforce` | `hours_available`, `hour_commitments` |
| `income` | `finance` | `credit_limit` |
| `indicators` | `reporting` | `real_output`, `price_ratios` |
| `lift` | `foreign_trade` | `lift` |
| `literacy` | `diffusion` | `literacy` |
| `log` | `reporting` | `event_log` |
| `map` | `land` | `tile_facts` |
| `mines` | `resources` | `mine_catalogue`, `mine_output` |
| `money` | `finance` | `spending_power` |
| `money` | `ledger` | `balance`, `acting_balance`, `cash_book` |
| `operating` | `mechanics` | `effect` |
| `operating` | `production` | `running`, `revenue_estimate`, `upkeep`, `institution_units`, `techniques_in_use`, `industry_depth` |
| `operating` | `projects` | `running_gates` |
| `operating` | `ventures` | `venture_crew`, `venture_quote`, `closures` |
| `partners` | `foreign_trade` | `partners`, `foreign_supply` |
| `people` | `demography` | `population`, `people_by_tile`, `food_eaten`, `yearly_record` |
| `power` | `materials` | `generation` |
| `prices` | `prices` | `material_prices`, `material_price`, `cost_ratios` |
| `revealed` | `knowledge` | `visibility` |
| `seat` | `seats` | `acting_seat` |
| `seats` | `seats` | `seat_list`, `seat_party` |
| `shocks` | `hazards` | `output_factor` |
| `standing` | `polity` | `standing` |
| `state` | `polity` | `patronage_funding`, `state_reach`, `state_treasury`, `state_account` |
| `stock` | `ledger` | `goods_stock`, `goods_stock_opening` |
| `stock` | `materials` | `resource_throttle` |
| `stores` | `stores` | `store` |
| `supply` | `materials` | `material_supply` |
| `tiles` | `land` | `tile_owner`, `tiles_owned_by`, `colonies` |
| `tree` | `knowledge` | `tree` |
| `tree` | `mechanics` | `mechanic`, `capability_sets` |
| `wages` | `workforce` | `wage`, `wage_index`, `labour_market`, `living_cost`, `wage_bill` |
| `ways` | `land` | `transport` |
| `weather` | `agriculture` | `farm_weather` |
| `workforce` | `ventures` | `venture_crew`, `closures`, `staffing_shortfalls` |
| `workforce` | `workforce` | `staff`, `hours_available`, `trade_spread`, `labour_market`, `living_cost`, `literacy_capacity` |
| `works` | `land` | `works` |

Channels that today are version counters: `done`, `operating`, `active`, `workforce`, `institution_units` (the five on `Household`). Everything else on this list is currently recomputed on demand or keyed by a stamp built where it is read.

## Caches found by the scan

138 attribute stores whose name says cache, memo, sequence, stamp, version, signature, epoch, scope or facade, or that write `__dict__[...]`, in `sim/` outside tests. File:line is the first store.

| Where | Name | Module of the file |
|---|---|---|
| `agents/collection_world.py:57` | `__dict__[_collection_memo]` | function module |
| `agents/household.py:253` | `_annual_mat_demand_cache` | function module |
| `agents/household.py:262` | `_demand_by_emp_key_cache` | function module |
| `agents/household.py:261` | `_demand_by_tag_cache` | function module |
| `agents/household.py:247` | `_done_seq` | function module |
| `agents/household.py:256` | `_goods_cat_state_cache` | function module |
| `agents/household.py:257` | `_goods_category_ratios_cache` | function module |
| `agents/household.py:259` | `_goods_mkt_op_factor_cache` | function module |
| `agents/household.py:258` | `_income_factor_cache` | function module |
| `agents/household.py:260` | `_material_demand_cache` | function module |
| `agents/household.py:255` | `_practice_cache` | function module |
| `agents/household.py:254` | `_rev_up_candidates_cache` | function module |
| `agents/household.py:251` | `_revenue_cache_key` | function module |
| `agents/household.py:252` | `_revenue_cache_val` | function module |
| `agents/household.py:263` | `_stock_throttle_sig` | function module |
| `agents/patent_index.py:65` | `__dict__[_patent_index]` | function module |
| `agents/registry.py:306` | `__dict__[_tile_owners]` | function module |
| `agents/registry.py:59` | `concern_set_version` | function module |
| `assembly/views.py:20` | `memo_epoch` | function module |
| `assembly/views.py:21` | `memo_signature` | function module |
| `economy/api.py:305` | `__dict__[_port_shares]` | function module |
| `economy/country_figures.py:84` | `__dict__[_area_tile_sets]` | function module |
| `economy/country_figures.py:97` | `__dict__[_country_price_memo]` | function module |
| `economy/country_figures.py:130` | `__dict__[_country_volume_memo]` | function module |
| `economy/market_memory.py:150` | `_memory` | function module |
| `engine/agents_port.py:45` | `_memo` | function module |
| `engine/campaign_year.py:25` | `__dict__[_campaign_sites]` | `campaigns` |
| `engine/coin_carriage.py:54` | `__dict__[_home_carriage_cache]` | `coin` |
| `engine/core.py:592` | `_material_demand_cache` | `core` |
| `engine/core.py:468` | `_seat_facades` | `core` |
| `engine/disease_port.py:107` | `__dict__[_disease_entry]` | `disease` |
| `engine/disease_port.py:194` | `__dict__[_epidemic_deaths_by_tile]` | `disease` |
| `engine/disease_port.py:253` | `__dict__[_epidemic_forecast]` | `disease` |
| `engine/disease_port.py:208` | `__dict__[_epidemic_names]` | `disease` |
| `engine/domestic_haul.py:56` | `__dict__[_material_haul_routes]` | `freight` |
| `engine/economy.py:262` | `_annual_mat_demand_cache` | `projects` |
| `engine/economy.py:270` | `_demand_by_tag_cache` | `projects` |
| `engine/economy.py:221` | `_done_seq` | `projects` |
| `engine/economy.py:265` | `_goods_cat_state_cache` | `projects` |
| `engine/economy.py:266` | `_goods_category_ratios_cache` | `projects` |
| `engine/economy.py:268` | `_goods_mkt_op_factor_cache` | `projects` |
| `engine/economy.py:267` | `_income_factor_cache` | `projects` |
| `engine/economy.py:269` | `_material_demand_cache` | `projects` |
| `engine/economy.py:264` | `_practice_cache` | `projects` |
| `engine/economy.py:263` | `_rev_up_candidates_cache` | `projects` |
| `engine/economy.py:260` | `_revenue_cache_key` | `projects` |
| `engine/economy.py:261` | `_revenue_cache_val` | `projects` |
| `engine/economy_electricity.py:349` | `_electricity_load_ids_cache` | `materials` |
| `engine/economy_electricity.py:431` | `_material_demand_cache` | `materials` |
| `engine/economy_electricity.py:514` | `_stock_throttle_cache` | `materials` |
| `engine/economy_electricity.py:511` | `_stock_throttle_sig` | `materials` |
| `engine/economy_freight.py:424` | `_demand_by_emp_key_cache` | `materials` |
| `engine/economy_freight.py:125` | `_demand_by_tag_cache` | `materials` |
| `engine/economy_freight.py:228` | `_land_freight_inputs_cache` | `materials` |
| `engine/economy_goods.py:359` | `_goods_cat_state_cache` | `markets` |
| `engine/economy_goods.py:440` | `_goods_category_ratios_cache` | `markets` |
| `engine/economy_goods.py:695` | `_goods_mkt_op_factor_cache` | `markets` |
| `engine/economy_goods.py:646` | `_income_factor_cache` | `markets` |
| `engine/economy_goods.py:394` | `_nodes_by_cat_cache` | `markets` |
| `engine/economy_materials.py:78` | `__dict__[_coppice_increment]` | `materials` |
| `engine/economy_materials.py:407` | `_annual_mat_demand_cache` | `materials` |
| `engine/economy_materials.py:186` | `_commod_ledger_cache` | `materials` |
| `engine/economy_materials.py:210` | `_done_memo_store` | `materials` |
| `engine/economy_materials.py:199` | `_material_commod_map_cache` | `materials` |
| `engine/economy_materials.py:223` | `_producers_memo_store` | `materials` |
| `engine/economy_materials.py:450` | `_standing_terms_cache` | `materials` |
| `engine/economy_mining.py:454` | `__dict__[_running_kept_tables]` | `resources` |
| `engine/economy_port.py:418` | `__dict__[_economy_port]` | `markets` |
| `engine/economy_port_year.py:265` | `__dict__[_sale_index]` | function module |
| `engine/economy_port_year.py:365` | `__dict__[_seat_inputs]` | function module |
| `engine/economy_port_year.py:364` | `__dict__[_seat_offered]` | function module |
| `engine/economy_port_year.py:98` | `_capacity_cache` | function module |
| `engine/economy_production.py:526` | `_practice_cache` | `production` |
| `engine/economy_production.py:601` | `_rev_up_candidates_cache` | `production` |
| `engine/economy_production.py:188` | `_revenue_cache_key` | `production` |
| `engine/economy_production.py:187` | `_revenue_cache_val` | `production` |
| `engine/foreign_capacity.py:110` | `__dict__[_foreign_can_make_cache]` | `foreign_trade` |
| `engine/foreign_capacity.py:134` | `__dict__[_foreign_demand_cache]` | `foreign_trade` |
| `engine/foreign_economies.py:69` | `__dict__[_partner_civs]` | `foreign_trade` |
| `engine/foreign_economies.py:159` | `_commodity_materials_cache` | `foreign_trade` |
| `engine/foreign_economies.py:130` | `_foreign_facts_cache` | `foreign_trade` |
| `engine/foreign_routes.py:101` | `_carrier_models_cache` | `freight` |
| `engine/geography_port.py:70` | `__dict__[_geography]` | `land` |
| `engine/geography_port.py:62` | `__dict__[_world_map]` | `land` |
| `engine/goods_market_api.py:63` | `_stock_throttle_sig` | function module |
| `engine/goods_market_offers.py:83` | `_home_prices_cache` | function module |
| `engine/held_works.py:19` | `__dict__[_held_running_cache]` | `land` |
| `engine/incumbent_prices.py:57` | `_incumbent_table_cache` | `prices` |
| `engine/incumbent_prices.py:77` | `_material_prices_cache` | `prices` |
| `engine/incumbent_prices.py:65` | `_price_tables_cache` | `prices` |
| `engine/interest_groups.py:80` | `__dict__[_banned_materials_cache]` | `polity` |
| `engine/labour_port.py:387` | `__dict__[_labour]` | `workforce` |
| `engine/legitimacy.py:64` | `__dict__[_staff_reach_memo]` | `polity` |
| `engine/legitimacy.py:44` | `__dict__[_state_reach_memo]` | `polity` |
| `engine/living_stock_yearly.py:76` | `_stock_throttle_sig` | `living_stock` |
| `engine/market_clearing.py:132` | `_market_outcome_cache` | `markets` |
| `engine/market_demand.py:159` | `_household_demand_cache` | `markets` |
| `engine/mechanics.py:36` | `__dict__[_mechanics_index_cache]` | `mechanics` |
| `engine/mine_deposits.py:61` | `__dict__[_deposit_base_cache]` | `resources` |
| `engine/mine_deposits.py:44` | `__dict__[_modelled_sizes_cache]` | `resources` |
| `engine/producer_costs.py:79` | `_cost_book_cache` | `prices` |
| `engine/projects_completion.py:83` | `__dict__[_goal_closure_by_goal]` | `projects` |
| `engine/projects_rebuild.py:31` | `__dict__[_dependents_index_cache]` | `projects` |
| `engine/projects_running_gates.py:73` | `__dict__[_running_gate_cache]` | `projects` |
| `engine/real_output.py:43` | `_base_basket_cache` | `reporting` |
| `engine/saveload.py:33` | `_game_version` | function module |
| `engine/society_diffusion.py:465` | `__dict__[_foreign_institution_cache]` | `diffusion` |
| `engine/society_diffusion.py:479` | `__dict__[_foreign_only_cache]` | `diffusion` |
| `engine/society_diffusion.py:273` | `_diffusible_ids_cache` | `diffusion` |
| `engine/state.py:126` | `__dict__[_account]` | function module |
| `engine/state.py:202` | `__dict__[_local_capital]` | function module |
| `engine/state.py:126` | `__dict__[_purses]` | function module |
| `engine/static_book_basket.py:37` | `_static_book_basket_cache` | `markets` |
| `engine/techniques_in_use.py:42` | `_techniques_in_use_cache` | `production` |
| `engine/techniques_in_use.py:59` | `_techniques_spread_cache` | `production` |
| `engine/tile_ownership.py:67` | `__dict__[_owned_tiles]` | `land` |
| `engine/tile_ownership.py:53` | `__dict__[_owner_map_seen]` | `land` |
| `engine/tile_ownership.py:85` | `__dict__[_tile_transfers]` | `land` |
| `engine/ui_port.py:169` | `_founder_death_cache` | function module |
| `engine/urban_share.py:33` | `__dict__[_urban_ceilings_cache]` | `demography` |
| `sharing/module.py` | `_standalone_scope`, `_scope` | `sharing` |
| `geography/endemic.py:34` | `__dict__[_endemic_cache]` | function module |
| `geography/food_productivity.py:18` | `__dict__[_food_cache]` | function module |
| `geography/reach_bands.py:59` | `__dict__[_reach_ladder]` | function module |
| `geography/resources_catalogue.py:26` | `__dict__[_resource_cache]` | function module |
| `geography/resources_district.py:39` | `__dict__[_resource_cache]` | function module |
| `geography/resources_endowment.py:65` | `__dict__[_resource_cache]` | function module |
| `geography/routes_compile.py:60` | `__dict__[_route_skeletons]` | function module |
| `geography/routes_graph.py:236` | `__dict__[_route_graph]` | function module |
| `geography/routes_rates.py:147` | `__dict__[_route_rates]` | function module |
| `geography/tile_layers.py:44` | `__dict__[_layer_cache]` | function module |
| `labour/labour_allocation.py:158` | `_need_shares_cache` | function module |
| `labour/labour_population.py:315` | `__dict__[_labour_hours_seen]` | function module |
| `labour/labour_settlement.py:123` | `__dict__[_reachable_tiles_cache]` | function module |
| `labour/labour_wages.py:55` | `__dict__[_labour_market]` | function module |
| `labour/labour_wages.py:245` | `_wage_schedule_cache` | function module |
| `labour/market/training.py:52` | `enrolled_cache` | function module |

Caches in `sim/agents`, `sim/economy`, `sim/geography` are inside their packages and become module internals when the package does; those in `sim/engine` are the ones that move to view versions.

