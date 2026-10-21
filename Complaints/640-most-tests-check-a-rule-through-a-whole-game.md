# Most tests check a rule through a whole game, so a failure cannot say which rule broke

**Status:** open

A large share of `sim/tests/test_*.py` builds a whole game (`harness.sim()`, `opened()`, `close_years`) and reads a
value off it, to check a rule that is one function. Such a test passes only while the live game happens to hold the
condition it assumes, and when it fails it names a symptom, not the rule. Count them (a rough grep of how each file
builds its subject; a file can match several):

    cd sim/tests && for f in test_*.py; do grep -qE "(^|[^_a-z])sim\(|Sim\(|opened\(|close_years|resumed\(" $f && echo $f; done | wc -l
    ls sim/tests/test_*.py | wc -l

Examples that went red together with no rule of theirs changing on purpose:

- `strata_income_from_cohorts` "strata that earn the same per head tie in rank": it reads two strata of a live Rome
  game and assumes they earn the same. The subject is the tie-break in `stratum_rank`; the equality was an accident.
- `cargo_cost` "dearer money raises domestic freight": it swaps `market_rate` on a running game. The subject is the
  interest term of one freight formula.
- `player_log`, `state_surplus`, `rush_fiscal_controls`, `training_ledger_and_hazard_reports`, `workforce_spinup`,
  `mines_deposits_whole_game`, `one_default_rule`, `mod_effects`, `rome_slave_stratum`.

Measure: `python3 -m sim.tests --slow --only <topic>` for each.

Why it matters: a failing check should name the broken rule where it stands, with no bisect over merges. Whole-game
tests also make most of the slow suite's time (`python3 -m sim.tests --slow --timing`).

What it would take: each such check becomes a test that calls the function with inputs it builds itself, or is
deleted where another test already holds the rule. When the rewritten test fails, the rule is fixed. A whole-game test
stays only as a named scenario or smoke test. Where the rule is a `Sim` method that needs the whole game, pull it into
a plain function first (508). Start with the failing topics above, then the rest in batches.

## Applied: the settling and real-output topics

- `real_output_cheaper_entry`: deleted. Rule tests in `test_cheaper_entry_lowers_price.py` (cost of a halved-labour entry; a
  cheaper entrant past the margin lowers the cleared price and raises the quantity; one under the margin changes nothing).
- `real_output`: the arithmetic moved to `sim/engine/real_output_measure.py` and is tested in `test_real_output_measure.py`; the
  111 s "a technology that improves no entry" check is deleted (held by `test_engine_prices` gate tests); the file is the wiring
  scenario plus one named validation.
- `saving_finds_a_use`: the paired whole-run "lent share doubles" is deleted (the two runs no longer differ); the rule is the
  `goods_orders` test that an owner offers less idle cash. One validation remains.
- `baseline_fixture`, `real_output_baseline`: kept as baseline validations (4.2), named so, failing on 473 with that message.
- `spin_up_sensitivity`: now `simulator.py spin-up-sensitivity` (a measurement); its rules are `test_spin_up_sensitivity_rules.py`.

## Applied: audit batch 2 (test_capacity_remedies through test_complaint_147_project_materials)

Each file's rules are called on inputs the test builds (a stub game, a `Business`, a built reply) and the whole-game
checks are named scenario checks in a `_scenario` file next to it. Extractions: `sim/engine/shortage_sizing.py` (mine and
nitre-bed sizes), `sim/engine/territory_required.py` (the landless refusal), `compute_material_bill` in
`sim/engine/project_materials.py`. Deleted as held elsewhere: the two other `test_complaint_147_*` files (now
`test_complaint_147_project_materials`), the loss-making and creditor-seizure closures (`test_business_review`), the foreman
choice (`test_business_crew_rule`).

## Applied: audit batch 8 (test_labour_productivity through test_mod_actor_kind_in_a_game)

Rules are called on inputs the test builds (a stub founder over the real mixin, a `HouseholdState`, a built reply); the
whole-game checks sit in a `_scenario` file next to each. Extractions: `sim/engine/freight_markup.py` (freight markup and
scarcity factor of a bought material, used by `economy_freight.py`), `sim/engine/diffusion_curve.py` (the leak of a
venture's edge and the knowledge half-life, used by `society_diffusion.py`). Deleted as held elsewhere:
`test_material_supply_whole_game` (the output of a made material is deposits plus producer capacity, held by
`test_material_supply_from_capacity`); the per-material grant and year checks of `test_living_stock_crops` (held by
`test_living_stock_scenario` and `test_living_stock_trade_scenario`). Kept whole as scenarios: `late_techniques_reach_economy`,
`market_state_is_economy_record`, `mod_actor_kind_in_a_game`, `menu_seed_and_saves_scenario`, `material_reach_whole_game`.

## Applied: audit batch 6 (test_fog_leaks_and_typed_wording through test_hire_reports_count_found)

Rules are called on inputs the test builds; whole-game checks that remain are named `_scenario` files next to them.
Extractions into plain functions: `scrub_hidden_ids` (`sim/engine/fog.py`), `sim/world/weather_pooling.py` (the cell correlation
factor and the pooled harvest multiplier), `remaining_floor_years` (`sim/engine/hazard_hedge_timing.py`), `patron_dies`
(`sim/engine/patron_death.py`), `dependants_not_carried` (`sim/engine/economy_debt_service.py`).
New quick rule files: `test_typed_front_end` (every typed-line check, taken from the fog, founder-sells and wording files),
`test_trader_routes_rules`, `test_losable_nodes`; the guns-on-walls, hazard-label and staff-survival rules are classes in
`test_defence_stores`. Deleted as held elsewhere: `test_hazard_messages_match_mechanics` (now `test_defence_stores`), the
harbour, voyage and failed-voyage checks of `gated_works_close_in_play` (`test_running_gates`, `test_held_and_running`,
`test_failed_voyage_loses_what_it_risked`), the magazine, crew and powder-stock whole-game checks of
`guns_on_walls_need_powder` (`test_defence_stores`). Baseline validation: `test_granary_persistence_validation` (the century
and nutrition bounds, failing on Complaint 44). Kept as scenarios, with no rule function to pull out: `founder_and_firm_agree`,
`founder_job_game`, `founder_research_shared_path`, `goal_leverage`, `forest_timber_whole_game`, `hire_reports_count_found`,
`hash_seed_order` (determinism).

## Applied: audit batch 5 (test_economy_reads_tile_yield through test_fog_leak3)

Rules now called on inputs the test builds, quick tier: `test_firm_borrows_to_enter` (`stake_split`, entry on credit, copy
budget), `test_firm_entry_market`, `test_firm_expansion` (`Firm.expand` on a return-per-step world, `rivals_of`),
`test_fog_leak3` (`missing_prereq_message` and `bounty_refusal` on a fogged stub, the parser's bare flags),
`test_typed_json_modes_parse`, `test_farm_clearing` (ladder and clearing), `test_farm_land_quality`, `test_farm_edges`,
`test_failure_needs_instrument` (`failure_teaches`, `note_failure`), `test_failure_and_bounty_money` (`bearable_part_of`),
`test_economy_crop_yields`, `test_economy_state_budget` (the budget's record round trip), `test_education_enrolment`
(`_enrolment`, `_limited_by`), `test_entry_cost_at_economy_prices` (`CostBook`), `test_every_posting_names_a_counterparty`
(source scan, edges), `test_explicit_starting_techs`, `test_figures_inspector` (`explain_figure`), `test_mechanics_documented`.
Extractions, behaviour unchanged: `hours_spent_clearing`, `cleared_hectares`, `quality_of_area` in
`sim/labour/labour_allocation.py`; `harmed_yields` in `sim/engine/economy_port_sites.py`; `declared_starting_techs` in
`sim/engine/starting_techs.py`. Whole-game checks stay as named `_scenario` files next to their rules. Deleted as held
elsewhere: the state budget's debasing, borrowing-first and hours-and-goods runs (`test_economy_agent_state`), the firm
count and expansion dynamics repeated across the firm scenarios (`test_firm_count_from_costs`, `test_firm_expansion`).
The state budget's runs over years on an opened England are `test_economy_state_budget_validation` (baseline validations,
4.2, naming Complaint 526); `economy_tin_dearer_than_copper` stays the slow validation naming Complaint 511.

## Applied: audit batch 10 (test_physical_money_constants through test_readouts_timing_power_mines_road)

Rules are called on inputs or stubs the test builds (quick tier); the whole-game checks that remain are named `_scenario` files
next to them. Extractions, behaviour unchanged: `mine_labour_hours_per_tonne` (`sim/engine/mine_labour_profile.py`),
`calendar_floor_years`, `payment_schedule_years`, `earliest_completion_years` (`sim/engine/completion_schedule.py`),
`payroll_means` and `staff_to_let_go` (`sim/engine/payroll_trim.py`), `paid_credit` (`sim/engine/project_funding.py`, now the one
place the credit for money already paid is worked out; `ui_port` re-exports it), `starving_warning` (`sim/labour/hours_sale_warning.py`).
Shared stand-ins: `sim/tests/disease_stand_in.py` (the disease model with no game), `sim/tests/labour_stand_in.py` (`Labour` over a
real civilisation and `Population`). Baseline validations (4.2): `test_plagues_from_contact_validation` (Complaint 490) and
`test_price_over_making_cost_band_validation` (Complaint 507; it reads only goods the economy traded, so the quote a market reports
where nothing traded, Complaint 642, is not in its band). Deleted as held elsewhere: the knowledge categories never abandoned
(`test_category_traits`), the loss rule and seizure closing a plant and keeping its knowledge (`test_business_review`), the cap on
work in hand (`test_start_money_rule`), the carriage and spin-up-key checks of the port's built ways (`test_economy_built_ways`),
the project bill as tonnes times the quote (`test_complaint_147_project_materials`), the working-age death share
(`test_sixth_step_pure_functions`). `quote_matches_charge` and `player_text_names_own_civilisation` are scenarios by nature (two paths
through the dispatcher agreeing; a leak across every reply builder).

## Applied: audit batch 7 (test_historical_events through test_labour_population_derived)

Rules now called on inputs the test builds, quick tier: `test_historical_events` (`hazard_given_condition`),
`test_home_cargo_price` (the quote's rules), `test_hot_path_caches`, `test_hour_pool_standing_is_live` (`hour_standing` and
the active-project builder on a stub game), `test_hours_by_trade_from_core` (`shares_from_people`),
`test_household_capacity_and_literacy` (`literate_capacity`, `household_room`, `_room_advice` on a stub labour),
`test_household_never_happened_fields`, `test_idle_capacity_view`, `test_idle_sized_suggestions`, `test_industrial_dashboard`
(the `changes` window checks, the typed front end), `test_invention_disclosure` (`disclose`, `copy_difficulty_of`,
`years_to_be_believed`), `test_keep_staffed` (the parser), `test_knowledge_loss_warning`, `test_knowledge_risk_and_sacking`
(`corpus_hedge`, `_sack_corpus_loss`, `_log_corpus_loss` on a stub game), `test_labour_allocation_wiring`,
`test_labour_follows_need`, `test_labour_market_town_pricing` (`LabourMarket` over a stub labour), `test_labour_population_derived`.
Extractions, behaviour unchanged: `hazard_given_condition` in `sim/engine/hazard_condition.py`; `shares_from_people` in
`sim/labour/labour_allocation.py`; `copy_difficulty_of` and `years_to_be_believed` in `sim/engine/visibility.py`.
Whole-game checks stay as named `_scenario` files next to their rules. `test_in_memory_civilisation`, `test_industry_depth_game`,
`test_home_floors_from_economy` and `test_labour_hiring_and_wages` are wholly wiring (screens, save round trips, the yearly
staff phases) and are now `_scenario` files; their rules sit in `Sim` methods that read much of the state
(`seed_opening_industry_experience`, `_step_staff`, `train`, `fire`, `commission`) and are still to be pulled out.
`labour_margins_whole_game` is now `test_labour_margins_baseline_validation` (a baseline validation, 4.2, naming Complaints 398
and 640) plus a scenario for the draught-animal recipes.

## Applied: deep extraction 1

`early_playtest`, `concern_volume`, `demographics_and_plague` and `economic_levers_inventory`, which batch 4 had left
mostly whole, now hold at most four named scenarios each; their rules moved to five quick files
(`test_early_playtest_data`, `test_civ_cost_and_hazard_relief_rules`, `test_concern_volume_rules`,
`test_mortality_shock_rules`, `test_material_throttle_rules`) over new plain functions (`material_throttle.py`,
`staff_loss_words.py`, `civ_cost.py`, `value_weight.py`). The `hazard_hit` log line now carries `defence` and
`national_toll_percent` as facts, so scenarios read values, not prose.

## Applied: audit batch 9 (test_mod_namespaces through test_perf_optimizations)

Rules are called on inputs the test builds (stand-in games that hold only what the method reads); whole-game checks that
remain are named `_scenario` files next to them. Extractions into plain functions: `founder_billed_growth`
(`sim/engine/stock_growth_billing.py`), `herd_units_kept` and `opening_herds` (`sim/engine/opening_herd_rules.py`),
`dice_for_play` (`sim/ui/play_dice.py`), `calendar_floor_note` and `free_hours_note` (`sim/ui/proto/parallelism_notes.py`),
`candidates_the_player_may_see` (`sim/ui/proto/name_candidates.py`), `borrowing_forecast` (`sim/ui/proto/credit_forecast.py`),
`scholar_target` (`sim/labour/staff_targets.py`), `nitre_bed_yearly_spend` (`sim/engine/shortage_sizing.py`). New quick rule
files or topics: `node_factor_is_economy_over_cost`, `one_living_cost_model`, `partner_quote_cargo`, `peek_resource_throttle`,
`opening_herd_growth_unbilled`, `opening_herds_follow_producers`, `opening_smelters_beside_ore`, `opening_basket_agrees`,
`options_from_settings_table`, `parallelism_note`, `mod_namespaces`, `names_and_fog`, `one_goods_market`, `one_labour_market`,
`people_attrition_scholars`, `perf_optimizations`. Deleted as held elsewhere: the afford-gate return-shape check (funding
arithmetic is `test_arrears_hours`), the source-text read of `_agent_state` for the free-hours field (the scenario reads the
reply), the whole-run 150-year attrition (`roll_trade`, also `test_complaint_585_staff_pay_retention`). Kept as scenarios:
`node_revenue`, `node_revenue_follows_research`, `node_revenue_per_civ`, `money_units_one_boundary`, `multi_year_step_log`,
`names_and_fog`, `one_goods_market`, `one_labour_market`, `one_living_cost_model`, `opening_herds_follow_producers`,
`opening_basket_agrees`, `opening_smelters_beside_ore`, `parallelism_note`, `partner_in_agent_economy`, `peek_resource_throttle`,
`people_attrition_scholars`, `people_by_trade_cache_year`, `perf_optimizations`.

## Applied: audit batch 11 (test_refusal_cash_remedies through test_seat_sight)

Rules are called on inputs the test builds (a stand-in game, the small fixture map, a built reply, the tree's own nodes);
the whole-game checks that remain are named `_scenario` files next to their rules. New stand-in:
`sim/tests/score_game.py` (what `score_report` and `final_report` read). Extractions, behaviour unchanged:
`routes_to_carry` (`sim/ui/replay.py`), `trade_demand_table` and `oversubscription_notes` (`sim/engine/trade_demand.py`,
used by `projects_progress.py` and `start`), `multi_year_hours_warning` (`sim/ui/proto/multi_year_warning.py`),
`route_money_warnings` (`sim/ui/proto/dispatch_inspection_path.py`), ventures paging (`sim/ui/proto/venture_paging.py`).
`research_filters` no longer sweeps `can_start` over the tree (Complaint 557): the filters run over the tree's nodes with a
stand-in game and the command keeps three checks on built nodes in `test_research_filters_scenario`. Deleted as held
elsewhere: the weather cell and pooled-draw checks of `regional_weather_wiring` (`test_growing_season_weather_correlation`
and its scenario), the housing sum of `reserve_staff_policy` (`test_auto_hire_buys_room`), the cheapest-route relocation
check (now a rule on the small fixture map). Found vacuous and rewritten: the two "does not claim nothing rests on it" checks of
`refusal_wording_and_screens` read the band from an unfogged game, where the field is empty, and passed whatever the rule
did; they now run on a fogged stand-in. Baseline validation: `test_regional_weather_century_validation` (slow-only, naming Complaint 46).
Kept as scenarios: `run_reproducibility` (determinism), the save round trips and two-game match of the weather, the
`again` command, the Options menu, the starting grants per civilisation.


## Applied: audit batch 12

24 files (test_seat_state through test_state_debasement_prices): rule tests on stubs and built records, a few named
scenarios each; `sited_ore_price_over_cost` is a baseline validation naming 519. Extractions: `society_at_opening`,
`replacement_wanted`, `staffing_warning_rows`. Two vacuous checks fixed (a refused project that read nothing; a quote
compared against capital taken after it). `state_debasement_prices` was red after 625 (its hook no longer set the cut);
it now drives `Government.apply_debasement`. Still Sim-only: `project_cost_now`, `venture_upkeep_quote`,
`staffing_missing_to_open`.
