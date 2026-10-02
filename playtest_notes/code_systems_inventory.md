<!-- Written by a code-reading agent that did not see the playtest notes or Complaints/; it edited nothing. -->
# Code inventory of simulated systems (bootstrap-history/sim)

Built from code only (module docstrings, call sites, grep). Complaints/, playtest notes and reports were not read.
Paths are relative to /home/user/bootstrap-history/sim unless noted. "step" = `Sim.step()` in engine/core.py (line ~2143), which calls the 14 phases in engine/core_step_phases.py in order: apprenticeships, staff, money (incl. demography, society, actors, win conditions), dated shocks, teach trades, standing work directive, start projects, materials, progress, wage fallback, reputation, bondage, founder mortality, random events, then year += 1.

Wiring vocabulary: WIRED = reached from step()/play/CLI. PARTIAL = runs but only a slice is reached, or reached only in one mode, or its output feeds nothing back. UNUSED = no live call site.

Global notes
- ~885 constants are registered with `declare(...)` (sim/constants.py); ~714 are `kind="temporary_heuristic"`, 3 are `kind="hardcoded_outcome"` (WAGE_SCARCITY_ELASTICITY in engine/core.py, SLAVE_BASE_PRICE_DENARII in sim/labour/labour_bondage.py, GENERIC_OUTPUT_PRICE_EXPONENT in engine/economy_materials.py). Heavy heuristic files: labour_capacity, society_state_pressure, core, economy_goods, projects_completion, economy_credit, economy_mining.
- Explicit "placeholder" wording appears in: economy_credit (~457), economy_goods (~684), economy_materials (~391, ~547), economy.py (~296), labour_population (~319-394, ~642), projects_starting (~71), society_state_pressure (~302), world/transport (cart/vessel service lives), world/agriculture (weather/hydrology terms), world/deposits (~211, ~372), world/land (~535), world/military_logistics (~644, ~770).
- Engine special-cases content ids despite CLAUDE.md 4.7: `patron_imperial`, `patron_senatorial` (core_step_phases eminence branch, economy_credit living cost), `sanitation_antisepsis` (founder mortality), `workshop_first` (auto_buy_people), `corpus_dispersed`/`corpus_written` (core.corpus_hedge), `citizenship`, `DISEASE_BURDEN_TECH_IDS` list, `identity_cover`.
- Save format carries `SAVE_VERSION = 3` / `state._version = 3` (sim/engine/saveload.py), a version stamp CLAUDE.md 4.6 says not to keep.
- Only a handful of functions in engine/ and world/ have zero live references (list at end).

================================================================
## A. WIRED

1. **Year step orchestration** - engine/core.py `Sim.step`, `run`; engine/core_step_phases.py `StepPhasesMixin`. One call = one year; fixed phase order; seeded `self.rng`. Wired: it is the loop. Notable: `manual` flag flips defaults of many auto_* policies (optimizer vs human).

2. **Demography (age cohorts)** - world/demography.py `Population` (children/working/elderly, fertility, mortality, nutrition ratio, disease burden); engine/core.py `_demographic_recovery`, `_apply_population_mortality_shock`, `_adult_equivalent_population`, `pop_scale`, `wage_index`. Wired: `_step_money` -> `_demographic_recovery` -> `Population.step` every year. Notable: hazards inject mortality shocks; population shortfall feeds a wage premium via WAGE_SCARCITY_ELASTICITY, labelled hardcoded_outcome (fitted to post-1348 English wages).

3. **Agriculture, harvest and granary** - world/agriculture.py (+ agriculture_yield.py, agriculture_labour.py, agriculture_storage.py): Cobb-Douglas yield from land, labour, technique, weather; `Storage.step` sow/grow/harvest/eat/spoil/retain; granary cap. engine/core.py `_demographic_recovery` builds the year's `Storage` from `farm_stock_kg`. Wired. Notable: granary carried over via persisted `farm_stock_kg`; several agri terms are labelled placeholders.

4. **Farm weather** - engine/core.py `_farm_year_weather_seed`, `_compute_farm_weather_cells`, `_cap_pooled_farm_weather_cells`, `_compute_farm_weather_correlation_cholesky`, `_pooled_farm_weather_multiplier`; world/agriculture `draw_weather_multiplier`. Wired via `_demographic_recovery`. Correlated regional cells, deterministic per-year seed, not a scripted event.

5. **Farming technique from held technology** - world/farming_technique.py; sim/labour/labour_allocation.py `_farming_technique`. Wired (core and labour_allocation import it). Technique is a mix weighted by adoption of technologies that name agriculture-table entries; data-driven.

6. **Disease burden from technology** - engine/core.py `_disease_burden`, `DISEASE_BURDEN_TECH_IDS`, `_tech_effects` (population weights). Wired: passed into `Population.step`. Hardcoded list of eight tech ids (violates dynamic-over-enumerated).

7. **Farmland and land clearing** - world/land.py `territory_farmland`, `RegionLand`; engine/core.py (sizes `farm_land`), sim/labour/labour_allocation.py `_apply_land_clearing`, `_set_farm_area`, `_clearable_hectares`. Wired (called end of `_demographic_recovery`). Land RENT half of land.py is used only by the price solver (see 21).

8. **Labour allocation between farm and trades** - sim/labour/labour_market.py (`Workforce.step`, hours by trade responding to need), sim/labour/workforce_spinup.py (starting split by spin-up), world/need_demand.py (demand from needs), sim/labour/labour_allocation.py (`_allocate_farm_workforce`, `_food_balance_step`, `_hours_needed_by_trade`, `reallocate`). Wired: `_allocate_farm_workforce` in `_demographic_recovery`; spin-up at start. Notable: workforce_spinup splits each need's budget equally (temporary_heuristic).

9. **Wage schedule and tightness** - sim/labour/wages.py `WageSchedule` (floor from subsistence basket, training premium, tightness adjust), sim/labour/wage_provider.py `build_schedule`, sim/labour/labour_wages.py (`wage_per_hour`, `annual_wage`, `wage_cost_factors`, `update_wages`, `wage_bill`). Wired: `update_wages()` each year (core.py ~1555), wage_bill in living_cost. `adjusted_tightness_factor` has no live caller.

10. **Money units / coin standard** - engine/money_units.py, sim/labour/wage_provider.py `coin_standard`, core `book_money`. Wired. Book denarii -> labour hours -> civ coin; civ must declare `coin_standard` material and mass.

11. **Credit, interest, arrears, insolvency** - engine/economy_credit.py (`credit_limit`, `committed_spend`, `funding_capacity`, `debt_interest_rate`, `charge_interest`, `warn_near_the_limit`, `enforce_credit_limit`, `shed_loss_makers`, `stall_diagnosis`, `spending_power`); engine/purchase_rule.py; step `_step_money` (staff bleed, abandonment of loss-making works, creditor seizure). Wired. Many placeholder-labelled thresholds.

12. **Living cost, tax and status spending** - engine/economy_credit.py `living_cost` (subsistence, household, tax = revenue x civ `starting_tax_share`, status by citizenship/patrons/capital). Wired. Content-id special cases for patrons.

13. **Founder practice income and concerns** - engine/economy_production.py (`revenue`, `revenue_sources`, `practice_attention`, `venture_ramp`, `still_ramping`, `workshop_output`, `capability_factor`, `upkeep`, `institution_upkeep`, `state_funding`). Wired: `_step_money`. Concern takings ramp up over years after opening; consumes founder attention hours.

14. **Goods market saturation and income effect** - engine/economy_goods.py (`goods_market_factor`, category state/elasticity/tau per category, cross-elasticity between own concerns, `income_factor`, `essential_price_ratio`, `goods_reach_factor`, `invest_farm`, `build_worker_housing`). Wired via revenue. ~13 near-identical per-category `declare`d tau/elasticity blocks (heuristic). `invest_farm` / `build_worker_housing` are player commands only (proto/dispatch_money.py).

15. **Local labour market for hiring (depth, saturation)** - sim/labour/labour_population.py (`labour_pressure`, `labour_price_factor`, `market_supply`, `trade_available`, `found_trade_school`, `reachable_trade_population`, `population_report`). Wired: used by hire/train/teach and auto-train. Town size and trade density labelled order-of-magnitude placeholders.

16. **Staff: hire, fire, train, teach, commission, attrition** - sim/labour/labour_training.py, sim/labour/labour_bondage.py `_resync_pools`, core_step_phases `_step_apprenticeships`, `_step_staff`, `_step_teach_trades`. Wired. Attrition rolled per person on `self.rng`; auto_hire / auto_train / auto_commission policies; staff let go when payroll cannot be met after credit.

17. **Slavery, purchase of people, manumission** - sim/labour/labour_bondage.py (`slave_quote`, `buy_slaves`, `manumit`), step auto_buy_people / auto_manumit. Wired. `SLAVE_BASE_PRICE_DENARII` is flat and labelled hardcoded_outcome; rising congestion surcharge.

18. **Founder hours, deputies, supervision and household room** - sim/labour/labour_capacity.py (`director_pool`, `directors_extra`, `staff_capacity`, `supervision_room`, `household_room`, `headcount`, `hired_cap`, `literate_capacity`, `director_hours_committed`). Wired. 87 heuristic constants in this file (largest concentration).

19. **Wage work, standing hour directives, wage fallback** - sim/labour/labour_wages.py `work_for_wages`; core_step_phases `_step_standing_work_directive`, `_step_wage_fallback`; proto `allocate`, `work`. Wired.

20. **Bounties** - engine/projects_starting.py `bounty_eligible`, `post_bounty`; proto `bounty`. Wired (player command; also `bounty_set` in path search). Money converted to someone else's hours; conversion rate labelled placeholder.

21. **Projects: legality, progress, risk, completion** - engine/projects_starting.py (`start_reason` and ~15 `_check_*` gates, `start_project`), projects_progress.py (`effective_risk`, retries, `calendar_floor`, hired-trade draw), projects_completion.py (`_complete`, tech effects, scandal, goal snapshots), core_step_phases `_step_start_projects`, `_step_progress`. Wired. Substitution groups (`req_any`), state opposition, social approval all inside `start_reason`.

22. **Ventures and institutions (open/close/units/mothball/restore)** - engine/projects_ventures.py, projects_capability.py, projects_staffing.py (`close_unstaffed_ventures`, `reopen_restaffed_ventures`, `auto_open_ventures`, `mothball_work`, `restore_work`). Wired via `_step_money`. Includes foreman/staff accounting per venture and warnings.

23. **Materials supply, stock and resource throttle** - engine/economy_materials.py (nine curated commodities + generic fitted fallback for other keys, `annual_material_demand`, stock/flow, `resource_throttle` inputs), engine/economy_electricity.py `resource_throttle`, `project_resource_throttle`; step `_step_materials`. Wired: throttle scales work done each year. GENERIC_OUTPUT_* fit is hardcoded_outcome.

24. **Freight and material price factor** - engine/economy_freight.py (`material_freight_cost_per_kg`, `material_price_factor`, `material_market_factor`, `shortage_remedy`); physics from sim/geography/transport.py (ox + cart + dirt track only). Wired via project_cost.

25. **Mining, depletion, forests, nitre** - engine/economy_mining.py (`open_mine`, `commission_mines`, `_advance_mine_depletion`, `mine_land_ceiling`, `buy_forest`, `mothball_mines`, `mine_operating_cost`), world/deposits.py (`load_deposits`, `Deposit`, build and extraction labour), economy_freight `build_nitre`; step `_step_materials`, `_step_money`. Wired. Auto_mine, auto_forest, auto_mothball policies. Stock/land ceilings depend on standing and state capacity.

26. **Electricity** - engine/economy_electricity.py (`generation_capacity_kw`, `_electricity_demand_kw`). Wired: part of `resource_throttle`. Heuristic-labelled duty cycles.

27. **Geography and reach** - sim/geography/geography.py (`region_reach`, `material_reach`, `material_cost_factor`, `mineral_scale`, `_compute_home_centroid`); data/world/geography.json. Wired (used by material supply and freight).

28. **Settlement, town and moving base** - sim/geography/settlement.py, sim/labour/labour_settlement.py (`base_tile`, `move_base`, tile population share); proto `move_base` (costs founder hours: `relocation_hours_this_year`). Wired (town population feeds hiring market). Tile share of nation = share of cultivable capacity (temporary_heuristic).

29. **Society values** - `value_weights` (w_magic_fear, w_religious_rigidity, w_military, adaptation_rate, bribability, ...), engine/society_hazards.py `_shock_values` (values drift across a hazard's window); read by alarm, state interest, familiarity. Wired. Weights come from civ data.

30. **Dated hazards and shocks** - engine/society_hazards.py (`_shocks`, `_shock_staff_loss`, `_shock_sack_chance`, `_shock_output_factor`, `_shock_real_erosion`, `hazard_relief`, `hazard_timeline`, `hazard_advice`), engine/hazard_window.py, projects_completion `HAZARD_COUNTERS`. Wired: `_step_dated_shocks`. Data-driven from `civ["hazards"]`; built defences reduce effects; output_factor recovers each year scaled by military leverage.

31. **Random events (fire, banditry, patron death)** - engine/society_hazards.py `_random_events`, constants FIRE_*, BANDITRY_*, PATRON_DEATH_*. Wired only when `events` is on (end of step). All labelled invented frequencies; auto_court_heir policy.

32. **Knowledge loss** - engine/society_hazards.py `_sack_site`, `_sack_corpus_loss`, `projects.forgotten`; engine/core.py `corpus_hedge`; step `_step_founder_mortality` dissolution (forget a fraction per year after founder dies with no deputy); fog.py `knowledge_risk` report. Wired. Hedges are hardcoded ids `corpus_written`/`corpus_dispersed`.

33. **Suspicion: alarm, familiarity, protection, scandal, bribery** - engine/society_state_pressure.py (`alarm_of`, `update_protection`, `withdraw_from_public_life`), projects_starting `bribe`, core_step_phases `_step_reputation` (scandal decay, denunciation roll, auto_bribe). Wired. Weights per trait are invented (ALARM_WEIGHT_*).

34. **Reputation and standing** - `standing_floor`, `rep_factor` (engine/economy.py), reputation decay toward floor in `_step_reputation`. Wired.

35. **Eminence / prominence** - society_state_pressure `eminence_report`, `prominence_hazard`; `_step_reputation` roll: confiscation, patron loss, or run-ending "too eminent". Wired (needs events on for the roll).

36. **State pressure: notice, requisition, office, confiscation, military demand** - society_state_pressure `household_scale`, `state_notice`, `requisition_report`, `office_report`, `military_demand_eligible`, `confiscation_risk`, `state_pressure_report`, `_state_pressure`. Wired from `_step_reputation`. Heuristic-heavy (68 labelled).

37. **Patronage** - patron_* nodes (imperial, senatorial, local); protection and living-cost effects; patron death and heir courting in `_random_events`; `_patron_advice` in projects_starting. Wired; hardcoded node ids.

38. **Literacy and schooling** - engine/society_adoption.py (`literacy_ceiling_general/elite`, `_schooling_flow`, `_advance_literacy`); literacy bounds LITERATE_TRADES in labour_capacity. Wired: `advance_society` each year.

39. **Trade absorption / naturalisation of taught trades** - society_adoption `_trade_absorption_years`, `_advance_trade_absorption`, `_grow_endemic_trade` (trade headcount drifts to literate ceiling). Wired (`advance_society`).

40. **Technology effects on the civ** - society_adoption `apply_tech_effects` (from `_TECH_EFFECTS.json`), called at completion. Wired; data-driven.

41. **Diffusion (within venture and across civilisations)** - engine/society_diffusion.py (`diffusion_share`, `diffusion_index`, `civ_diffusion`, category indexes food/medical/information/state-military, `medical_diffusion_relief`, `_is_foreign_only`, `needs_first`, `civ_cost_factor`, `world_diffusion_report`). Wired: cost factor in project_cost, relief in hazards, reports. Category pace values are heuristics.

42. **Military leverage** - society_state_pressure `military_leverage`, `military_equipment_burden_kg_per_soldier_per_year` -> world/military_logistics `annual_iron_and_ammunition_burden_kg_per_soldier`. Wired for the one crossing (see 51 for the unused rest).

43. **Founder mortality, succession, dissolution** - core_step_phases `_step_founder_mortality`; `cfg["immortal"]`. Wired. Sanitation extends life via hardcoded id.

44. **Debt bondage of the founder** - `_step_bondage`, `bondage_years_left`, `bondage_debt`; entered from `enforce_credit_limit`. Wired.

45. **Run end and goals** - society_hazards `_catastrophe`; core `_check_win_conditions`, `_win_condition_value` (threshold goals completed by measurement, e.g. literacy); mods_goals. Wired (`_step_money` phase 2c).

46. **Fog of war** - engine/fog.py (`reveal_from`, `is_visible`, `fog_scrub`, `strip_self_play_advice`, `fog_summary`); proto `fog_hidden` commands. Wired in play/agent protocol (fog flag saved). `reveal_from` called at project completion.

47. **Policies / automation (auto_*)** - `state.founder.policy` dict; keys: auto_hire, auto_train, auto_commission, auto_open, auto_shed, auto_mine, auto_forest, auto_mothball, auto_bribe, auto_buy_people, auto_manumit, auto_court_heir; proto `policy` command. Wired; defaults depend on `manual`.

48. **Trade registry / trade families** - engine/data.py `trade_family`, `load_trade_registry`, data/world/trades.json; consumed by wage schedule and step context. Wired.

49. **Mods** - engine/mods.py, mods_base, mods_civ, mods_goals, mods_ids, mods_remove; used from engine/data.py load paths; also need_data.py and topic_tags.py. Wired at load. Three sample mods in /home/user/bootstrap-history/mods. Namespaced ids, dependency/conflict checks, removal reference checks.

50. **Needs and goods data** - engine/need_data.py, data/world/needs.json; consumed by world/need_demand via workforce_spinup. Wired at start-up.

51. **Save / load** - engine/state.py (typed state owners, auto-detected fields), sim/engine/saveload.py, cli_interactive_saveload.py, settings.py. Wired (`save` command, `--session` saves and loads every command). RNG state and fog saved.

52. **Protocol, CLI, rendering, help, score** - sim/ui/proto/* (command registry ~40 commands, dispatch_*, typed parser, render_*, help, score.py, techtree.py), engine/cli*.py (menu, play, agent, validate, path, costs, run, compare, sensitivity, sweep, goals, plan, search, why). Wired. Some proto/help.py `_topic_*` functions look unreferenced by name but are dispatched through a table.

53. **Settings / config** - engine/settings.py (saves dir, remembered menu choices). Wired in CLI.

================================================================
## B. PARTIALLY WIRED

54. **Price solver** - solve_prices.py, solve_prices_core.py (recipe cost, SCC-based fixed point, capability grading), solve_prices_report.py, joint_allocation.py (joint costs split by demand), engine/prices.py, engine/solve_cache.py, world/deposits.py (Ricardian ore rent), world/land.py (land rent), world/demand.py. Evidence: wage schedule always calls `solved_prices` (engine/wage_provider.build_schedule) and `data.load` fills materials missing from prices.json; but `load(use_solved_prices=False)` is the default and every play/CLI caller uses `load()` with defaults, so node costs and goods come from data/prices.json. Notable: prices.json still the live price source; several mod paths force solver.

55. **Military logistics** - world/military_logistics.py: only `annual_iron_and_ammunition_burden_kg_per_soldier` and `MODERN_SERVICE_RIFLE` are called by the engine (society_state_pressure.py ~286). Rest is standalone/test-only; `foraging_corridor_width_km` has no caller; two CALIBRATION_LEGION_* constants unreferenced.

56. **Transport physics** - sim/geography/transport.py: engine reads only the ox/cart/dirt-track draught-freight inputs (economy_freight ~227). `required_tractive_force_newtons`, `distance_per_day_km` unreferenced; other vehicles/surfaces reachable only from tests/tools.

57. **Commodity ledger** - engine/commodities.py: `CommodityLedger` used by economy_materials for national output/market share and `propagate_demand` in `wire_chain_report`. The stock class `Ledger` (and `on_hand`) are not used by the engine ("Sim has no inventory" per its docstring). Sim keeps its own Counter stock.

58. **Actors: Government and Firm** - sim/agents/*, engine/society_actors.py `advance_actors` (called every year in `_step_money`); governments accrue discretionary money, firms are founded by `consider_entry`, copy proven concerns via imitation, operate, and exit after loss years. Evidence of no feedback: `self.actors` / `ActorRegistry` is referenced only from society_actors.py; nothing in economy/revenue/labour/proto reads firms or governments, so their results do not change founder revenue, prices or reports. State is persisted. `Household` (actors/household.py) itself is fully wired as the founder's state facade.

59. **Need-based and household demand** - world/need_demand.py, world/demand.py: used for workforce spin-up (wired) and joint-cost allocation in the solver; `aggregate_household_demand_all_goods` unreferenced; `goods_attributes` unused outside module.

60. **Invariant checks** - engine/invariants.py: run in `step()` only when `self.debug` (defaults to `__debug__`, i.e. on unless python -O). Not simulation behaviour.

================================================================
## C. PRESENT BUT UNUSED / OFFLINE ONLY

61. **Offline planners and strategies** - planner.py (CPM/backward plan), path_search.py, strategies/*.json; reached only from CLI `plan`, `search`, `sweep` (not the play loop); they drive Sim through `bounty_set` and ordered project lists.
62. **Dead functions/classes with no live caller (from an AST reference scan of engine/ and world/)** - sim/agents/household.py `MineWorking` (TypedDict); economy_materials `capacity_reserves`; state.py `add_reputation`, `add_scandal`, `deduct_reputation`, `done_keys_sorted`, `operating_keys_sorted`, `record_spend` (used only by tests or nowhere); commodities `on_hand`; world/demography `working_age_population`; world/demand `consumers_of`, `joint_output_value_shares_for_recipe`, `aggregate_household_demand_all_goods`; world/military_logistics `pack_animals_required_for_daily_delivery`; world/deposits `shafts_needed_fractional`; world/wages `adjusted_tightness_factor`; engine/cli_analysis `granary_projection`.
63. **Unused constants** - `MINE_OPEX_PER_T_*` per-metal constants are referenced once (probably assembled via a table); military_logistics CALIBRATION_LEGION_MARCH_RATE_* and demand HOUSEHOLD_FOOD_BUDGET_SHARE_HIGH, SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL are declared but read only in tests.

================================================================
## Counts
Total distinct systems listed: 63 (items 1-63; item 63 is a residue entry, so 62 real systems if you exclude it).
- Wired: 53 (items 1-53)
- Partially wired: 7 (items 54-60)
- Unused/offline: 3 (items 61-63)
