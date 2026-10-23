# Most tests check a rule through a whole game, so a failure cannot say which rule broke

**Status:** partly - every test module that builds a whole game is declared a scenario, validation or smoke test or converted (the guard's leftover list is empty); open: rules still inside `Sim` methods whose checks can only run in a scenario until they are plain functions

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
  `goods_orders` test that an owner offers less idle cash. The one validation (some savings are lent to producers in a fixture economy) is deleted: it asserted only a positive share; `economy-check` measures it.
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

## Applied: deep extraction 3

The last scenario-heavy files of the audit. Rules now sit in plain functions and the quick files call them on inputs they
build; the scenarios keep wiring only. Extractions (behaviour unchanged):

- `sim/labour/founder_hours.py` (`hours_pool`, `hours_committed`, `hours_free`; `director_pool`, `director_hours_committed`
  and the standing job's `hours_for_sale` call them), `sale_at_a_loss_note` in `sim/labour/hours_sale_warning.py` (the cost
  note of `work_for_wages`), `sim/labour/buy_cap.py` (`over_room_refusal`, the cap `buy_slaves` shares with `hire`), and
  `sim/engine/staff_gate.py` (the scholar and craftsmen refusals of `start_reason`, sized by the people short): all in
  `test_founder_hours_rules`.
- `missing_when_opened` in `sim/engine/staffing_choice.py` (`staffing_missing_to_open`): `test_staffing_choice_rules`.
- `sim/engine/quote_figures.py` (`cost_if_started_now` behind `project_cost_now`, `upkeep_quote` behind
  `venture_upkeep_quote`): `test_quote_figures_rules`. `forest_price_per_hectare` is the one price `buy forest` charges and
  `quote forest` shows.
- The load refusals (`_validate_save`, `load_state` leaving the game untouched) over a built save: `test_save_refusal_rules`.
- Hazard hits on a country's strata and the home cohort shock, `transfer_tile`, the famine watch and the three yearly
  invariants over a stand-in game built from strata, actors, tile owners and a control store (the stand-in was not too large
  once built from those parts): `test_world_hazard_rules`.

Checks per scenario file, before and after: `ventures_saves_and_dice` 46 to 41, `workforce_advice_and_allocate_cap` 2 to 1,
`world_events_and_hazards` 13 to 8; `shut_for_staff` (3) and `start_and_upkeep_quotes` (5) keep their wiring checks.

Failing on the integration branch before these changes, and still open: `start_and_upkeep_quotes_scenario` (two checks: a
`start horse_collar` in an opened game is refused `people_exist` because the labour core holds about 0.001 smiths there,
against tens of thousands in an unopened game of the same civilisation). In `ventures_saves_and_dice_scenario` two fixtures had
drifted: `train optician` was unaffordable on the default purse (now given a purse, the subject being the save) and the
bound of 400 founder hours left after teaching no longer matched what teaching costs (now read from the pool and the hours
committed).

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

## Applied: deep extraction 2

Batches 7 and 8 had left their rules inside `Sim` and labour methods, so their checks stayed whole-game scenarios. The rules
now sit in plain functions in small modules, the methods call them, and the quick files below call the functions on inputs
they build. Extractions (behaviour unchanged):

- `sim/engine/mine_ceiling.py` (`mine_ceiling_tonnes`, `room_under_ceiling`, shared by `open_mine` and `buy_forest`):
  `test_mine_ceiling_rules`.
- `sim/engine/trade_absorption.py` (the years, the yearly step, the drift toward the literacy ceiling):
  `test_trade_absorption_rules`.
- `sim/engine/staffing_choice.py` (allowances, shortfalls, which concerns close) and `people_to_hire_for` in
  `sim/labour/labour_staff_controls.py` (the `keep ... staffed` hire): `test_staffing_choice_rules`.
- `sim/engine/closure_grace.py` (the grace window, the discounted fee, the note): `test_closure_grace_rules`.
- `sim/engine/credit_freeze.py` (`settlement_freeze`, the stall rule, the loss makers): `test_credit_freeze_rules`.
- `_staffing_standing_crew` (the `why` supervision block) on a stub game: `test_why_supervision_rules`.
- `sim/engine/industry_depth_rules.py` (the opening seed and the yearly accrual): `test_industry_experience_rules`.
- `sim/engine/adoption_share.py` (`state_military_diffusion`): `test_adoption_share_rules`.
- `sim/engine/bondage_workshop_rules.py` (`_step_bondage`, `workshop_output`): `test_bondage_workshop_rules`.
- `sim/engine/staff_phase_rules.py` (`_step_staff`: the room to hire and the move by whole people; the payroll trim,
  replacement and scholar target were pulled out in parallel by batches 9 and 12): `test_staff_phase_rules`.
- `sim/labour/staff_moves.py` (the literacy wall, `fire`, the spare hours of `commission`, what stops `work_for_wages`):
  `test_staff_moves_rules`; `sim/labour/staff_advice.py` (`_staff_advice`): `test_staff_advice_rules`.

The scenario files kept their wiring checks only. The determinism subprocess in `test_mines_scenario` now builds its game
the way the harness does, so it reuses the warm spin-up instead of paying a cold one that overran its sixty seconds.

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

## Applied: audit batch 13 (test_state_debases_coin through test_trade_shortage_kind)

Rules are called on inputs the test builds (stand-in games and worlds holding only what the rule reads); all of these topics
are now quick except three named scenarios. New or rewritten quick rule files: `test_state_debases_coin` (`Economy.strike_lighter_coin`,
the yearly `_strike_state_coin`), `test_state_headcount_home` (`state_hands`, `checked_army`), `test_state_repetition`
(`already_explained`), `test_state_revenue_forms` (the forms over a stand-in world, the lever on a rate), `test_state_taxes_in_kind_economy`
(units to tonnes, the held tiles), `test_state_serialization` (the cache reset, the save validation on a built save),
`test_state_soldier_trade` (the army line, the standing draw on the unskilled trade, the state's hiring pressing the market),
`test_state_strata_fiscal`, `test_state_weapon_relief` (the relief over a stand-in game), `test_step_problems`,
`test_strata_income_from_cohorts`, `test_stuck_matches_start`, `test_stuck_sees_training`, `test_tiles_replace_regions`,
`test_town_providers`, `test_trade_reach_transport`, `test_trade_school_rename`, `test_trade_shortage_kind`. Extractions, behaviour
unchanged: `score_total` (`sim/ui/proto/score_total.py`); the start money refusal (`_money_refusal`) now carries its cause
`cash_short` and facts `owed`, `price`, `ceiling`, `short`. Scenarios kept: `test_state_repetition_scenario` (`state` and `ventures`
mark an explanation as seen), `test_state_revenue_forms_scenario` (one played year of grain taken in kind),
`test_step_reply_severity_scenario` (the `step` command tags every event). Deleted as held elsewhere: the in-kind levy, price and stores
checks of `test_state_taxes_in_kind_economy` (`test_state_taxes_in_kind`); the strata's books over a year and the conservation of money
in `test_strata_income_from_cohorts` (`test_agents_strata`); the region-record land check of `test_tiles_replace_regions`
(`test_a_region_record_is_only_a_label`). `test_tariffs_and_embargoes` and `test_state_land_revenue` were already stand-in tests.

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


## Applied: audit batch 14 (test_training_ledger_and_hazard_reports through test_year_phases)

Rules are called on inputs the test builds (stand-in games holding only what the command reads, built replies, the real
tree); whole-game checks that remain are named `_scenario` files next to their rules. Extractions into plain functions,
behaviour unchanged: `assemble_ledger` (`sim/engine/revenue_ledger.py`), `hedge_wants` and `startable_first`
(`hedge_steps.py`), `capital_lost` (`capital_loss.py`), `staff_loss_toll` and `sack_toll` (`hazard_toll.py`),
`eminence_band_to_announce` (`eminence_warning.py`), `year_bill` (`project_funding.py`), `capped_to_useful` (`sim/ui/proto/allocation_cap.py`). Quick rule files: the training ledger,
`workforce_spinup`, `upkeep_quote_matches_ledger`, `whole_game_no_seller_no_price` (Complaint 642: no seller gives no
traded price and a named quote; import volume bounds), `why_foreman_and_remaining_floor`, `wild_stock_whole_game`,
`ui_anatomy`, `ui_figures_more`, `ui_goals_watch`, `ui_memory`, `ui_notes`, `ui_step_automation_line`, `wage_provider`,
`wage_work_ledger`, `wage_floor_and_coin_standard`, `workforce_advice_and_allocate_cap`, `world_events_and_hazards`,
`ventures_saves_and_dice` (the identity_cover prerequisites). Deleted as held elsewhere: the refund-cap, arrears-cause and
effective-hours checks (`test_arrears_hours`), the failed-attempt announcement (`test_completion_messaging`), the
tight-trade wage check (`test_wage_provider`). Found vacuous: the "every household material has a seller" check
(true by construction) and the import bounds in the Rome game (it opens with no partner-sold material); both dropped, the
bounds are now `import_tonnes_left` rule tests. Baseline validation: `test_whole_game_gold_silver_ratio_validation`
(Complaint 442). Still to pull out of `Sim` methods: load validation, the staffing gates of `open` and `start`,
`work_for_wages`, and the `Sim.start_reason` deficit sizing (all kept whole in `test_ventures_saves_and_dice_scenario` and
`test_workforce_advice_and_allocate_cap_scenario`). `test_two_seats_whole_game` is wholly a scenario and `test_year_phases`
already runs on a stand-in.

## Applied: audit batch 12

24 files (test_seat_state through test_state_debasement_prices): rule tests on stubs and built records, a few named
scenarios each; `sited_ore_price_over_cost` is a baseline validation naming 519. Extractions: `society_at_opening`,
`replacement_wanted`, `staffing_warning_rows`. Two vacuous checks fixed (a refused project that read nothing; a quote
compared against capital taken after it). `state_debasement_prices` was red after 625 (its hook no longer set the cut);
it now drives `Government.apply_debasement`. Still Sim-only: `project_cost_now`, `venture_upkeep_quote`,
`staffing_missing_to_open`.

## Applied: the guard, and the declaration of whole-game modules

New whole-game tests kept arriving as undeclared files. `python3 -m sim.tests --whole-game-checks` (`sim/tests/whole_game_checks.py`)
reads each `test_*.py` syntax tree and lists the modules that build a whole game (`sim`, `unopened_sim`, `build_unopened`, `Sim`,
the in-process CLI `proto` and `cli_in_process.run`, the `spin_up_*` helpers) and are not declared. A module is declared by a file
name ending `_scenario`, `_validation` or `_smoke`, or by a docstring opening `SCENARIO`, `BASELINE VALIDATION` or `SMOKE`. The quick
topic `whole_game_declared` fails on an undeclared builder that is not in `sim/tests/whole_game_leftovers.txt` and on a listed
module that has since been declared, converted or deleted, so the list only shrinks. Its rule checks call the detector and the
declaration test on source text built in the test.

Declared by marker in this pass (their subject is a whole game: scenarios, the opening and spin-up checks, save and resume round
trips, determinism, the CLI front end, baseline validations): 61 modules, found by reading each docstring against the checks in it.
Split, the rule checks staying quick and the game-building checks moving to a `_scenario` file beside them: `arrears_hours`,
`auto_hire_buys_room`, `bank_institution_gate`, `bearable_part_pure`, `complaints_17_24`, `completion_messaging`,
`concerns_that_pay`, `dynamic_wages`, `demography_history`, `alerts_staffing_finish`, `automation_audit`. `concerns_that_pay`
had been failing before this pass (its fake world lacked `plant_costs`, which the scan reads); the stub now has it.

## Remaining: rules still checked only through a game

The guard's leftover list (`sim/tests/whole_game_leftovers.txt`) is empty: `python3 -m sim.tests --whole-game-checks` lists no
undeclared module, and the quick topic `whole_game_declared` fails on any new one. Some modules were declared rather than converted
because their rule sits inline in a `Sim` mixin or a phase; their `_scenario` files hold rule checks until the rule is a plain
function. What is left, after the rules named in the list below were pulled out (each with a quick rule test):

- the state's year as a ledger: how a reserve finances a deficit and the rest is cut, and the founder paying the ordinary share
  and the need-driven levy (`Government.pay_standing_need`, `Sim._state_pressure`; `state_budget_scenario`); the requisition,
  office and confiscation reports that call the extracted functions stay as wiring in `state_notices_scenario`;
- the expected calendar years of a risky project and the calendar floor (`Sim.expected_calendar_years`, `calendar_floor`;
  `project_retry_and_risk_scenario`);
- the rest of `_step_staff`: the `_grow_to` closure and the per-trade replacement loop (the arithmetic around them is plain);
- the `Sim` methods that compose the domestic haul from prices (`_freight_mode_costs`, `_haul_route`), which only run in a game.

Converted in the second round (rule now a plain function with a quick rule test, its checks moved out of the scenario):
`state_notice_rules` (the notice line, the levy shares, protection bargaining, the confiscation chance and its mitigations,
military demand), `budget.military_ask_of`, `budget.sack_pressure` and `budget.army_goal` (the army the threat asks for,
shared by the home and country views), the standing lines (`test_state_budget_lines`) and the army, administration and army
size rules (`test_state_budget_rules`); `risk_rules` (control relief and the compounding of the multipliers of a retried
project); `haul_route.cargo_class_of`, `domestic_haul_mode` and `unjoined_haul_cost`; `colony_rules.best_settlement_work`,
`outfit_cost` and `colony_people`, with the settlement geography rule-tested on built inputs; `public_works_rules` (the free
press, the dole, the lit working day, schooling by group and printing); `industry_depth_rules.opening_seed` and the
once-only guard of the seed; `staff_phase_rules` (smoothing toward a target, the craft headcount, the hiring goals, the
deputies, replacement affordability); `labour/request_rules` (the preconditions of `train`, `fire` and `commission`, now
refusals with a `cause`, and the teaching fee); `staff_pay_rules.wage_for_hours_of` (`work_for_wages`). Load validation
(`test_save_refusal_rules`), the staffing gates of `open` and `start` and the hire advice sized to the deficit of
`start_reason` (`test_founder_hours_rules`) were already plain functions with rule tests.

Converted in this round (rule now a plain function with a quick rule test): `start_blockers` (`blockers.collect_blockers`), the
automation start rule (`auto_start_rule.judge_start_candidate`), auto-mine sizing (`shortage_sizing.auto_mine_order_tonnes`),
the colony rules (`colony_rules`), coverage and disease burden (`coverage_rules`, `disease_burden.burden_from_holdings`), route
dues and handling, settlement owed, halting projects on exhausted credit, non-labour upkeep, project throttles, the nitre deficit,
instantaneous projects, the eminence hazard rules, dependants beyond means, prerequisite names. `start_and_upkeep_quotes_scenario`'s
`people_exist` refusal is gone (659, closed).

The complaint closes when the rules above are plain functions and their checks have left the scenarios.

Test migration (rule-tests-05): the generic fog scanner over every command (`fog_and_command_scanners_scenario`, about 9 s, six commands scan the whole tree) is deleted; each command filters its own reply and no quick form exists. No simulator command runs it. The command-pointer half is now the static scan test_command_pointer_scan.

## Applied: rule-tests batch 12 (people_by_trade_cache_year through portfolio_scale_stuck_advice)

Rules called on stand-ins; the slow whole-game checks are gone or are SMOKE modules that build unopened games and run no years.
Extractions: `sim/engine/payroll_shed.py` (`shed_unpayable_staff`: staff a household cannot pay leave and the loss is logged),
`sim/labour/trade_supply_rules.py` (people who exist, the hours a market offers, when a hire leaves nobody), `sim/ui/proto/heard_paging.py`
(the "heard of" page). New rule tests: `test_payroll_shed`, `test_trade_supply_rules`, `test_labour_move_base_rule`, `test_heard_paging`,
`test_short_of_staff_marker`, `test_stuck_reasons`, `test_exclusion_rules`, `test_policy_screen_rules`, `test_start_gate_rules`,
`test_epidemic_seats_and_knowledge`, `test_port_sync_ways`. SMOKE modules: `game_port_and_portfolio_smoke`, `player_available_smoke`,
`player_report_and_path_smoke`, `player_commands_smoke`, `han_reply_words_smoke`, `population_per_region_smoke`.
Deleted as held elsewhere: `people_by_trade_cache_year_scenario` (every writer drops the cache), `perf_optimizations_scenario` (the
fingerprint tool itself), `physical_money_constants_scenario` (hours by deposit are held; the product with the wage is one line),
`plague_mitigation_realism_scenario` and `plague_no_double_count_scenario` (`spread_share`, `medical_relief` and the exposure tests),
`population_placeholder_marks_scenario`, `population_farm_technique_scenario` (see 513), `plagues_from_contact_validation` (see 490).
Not carried over: the start-refusal "training is a warning, not a refusal" check (dispatch `start` with a trade being taught), the
`available` speed-under-fog bound (a wall-clock assertion), and the whole-game tests of insolvency shedding and creditor seizure
(the plant rules are `test_business_review`). The founder-hours accounting identity and the refund proportionality of a three-year run
are `project_funding.fund_year` (`test_arrears_hours`); the hours summary itself has no test.

## Applied: rule-tests-17 (start_opening_warning through temperature_caps)

Rules are called on stand-ins, one function per test. New quick modules: `test_step_progress_hook` (`after_year`, `commit_and_report`, the played command clearing the hook, `demographic_emergency`), `test_cast_view_floor_costs`, `test_completion_opening_shortfall`, `test_state_owes`, `test_state_government_wiring` (`Government.employ_standing`, `seek_shortfall`, and the new `spend_on_lines` extracted from `pay_standing_need`, behaviour unchanged), `test_staff_reach_wiring`, `test_collection_view_staff`, `test_state_pressure_reports`, `test_budget_view_army`, `test_state_command_explains_once`, and a quick `test_suite_portability` (structural scans, one parse per topic file) with the renamed-root subprocess run kept as `test_suite_portability_smoke`. `state_ownership_enforcement` and `subsistence_staple_is_civilisation_data` are quick now (the first pre-filters files by text before parsing).

Deleted as held elsewhere: `state_debasement_prices_scenario` (`test_state_debasement_prices`), `state_arrears_scenario` and `state_borrowing_gate_scenario` (`test_state_arrears`, `test_state_borrowing_gate`), `state_corvee_game` (`test_state_corvee`, `test_levy_hours_per_worker`), `state_revenue_forms_scenario` (`test_state_taxes_in_kind`, `test_state_works`), `state_spending_scenario` (`test_state_budget_lines`, `test_state_budget_rules`, `test_country_patronage`, `test_state_works`), `temperature_caps` (`test_temperature_caps_rule`), `start_waits_for_trade_scenario` (`test_start_waits_for_trade`), `step_reply_severity_scenario` (`test_event_severity`).

Deleted with no replacement, because the claim lives only in a long dispatch or phase function or reads the unsettled opening, and no simulator command measures it: the `step` command calling the per-year hook and an interrupt keeping the saved years (`_agent_dispatch`); `_agent_state` adding the `demographic_emergency` field; `start` adding `today_you_could_not_open_this_when_it_is_done` and `waits_for_trades` to its reply; `ventures` shortening its staffing-share note on the second ask; `Sim._state_pressure` charging the founder the levy and its dice being gated on `events` and fog never leaking a node id; the save round trip of the state's books; the pre-modern diet bands of Rome's opening basket (Complaint 560: no command prints the opening's food shares). The remaining `Government.pay_standing_need` and `_state_pressure` flows are worth extracting further when 473 closes.
