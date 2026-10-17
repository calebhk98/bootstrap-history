# Dozens of slow topics exceed the runner's time limit on a cold cache

**Status:** open

The runner fails any topic still running after `TOPIC_SECONDS` (`sim/tests/__main__.py`). After an economy
edit (every price solve and spin-up cache key changes), a full `python3 -m sim.tests --slow --timing` on four
cores timed out dozens of topics and did not finish inside the background limit of the session that ran it.
Rerun one at a time with a much longer limit they mostly pass, so they are slow, not stuck; a topic over the
limit counts as failed whatever it would have answered.

Topics measured over the default limit on that cold rerun (shared machine, so the split is rough): `actor_treasury`, `affordability_and_credit`, `affordability_warning`, `allocate`, `automation_modes`, `built_ways`, `cli_in_process`, `cli_menu_options_and_pretty`, `complaint_147_project_materials`, `complaint_188_fuzzy_estimates`, `complaint_320_save_round_trip`, `complaint_45_forest_area_not_region_count`, `complaint_59_quote_matches_purchase`, `dashboard_history_cap`, `early_playtest`, `economy_bronze_market_price`, `engine_content_ids`, `failure_and_bounty_money`, `failure_roll_matches_display`, `farm_edges`, `fog_leaks_and_typed_wording`, `founder_death_and_victory_ending`, `full_length_opening_checks`, `gated_works_close_in_play`, `granary_persistence`, `growing_season_weather_correlation`, `guns_on_walls_need_powder`, `home_cargo_price`, `interface_honesty`, `knowledge_loss_warning`, `knowledge_risk_and_sacking`, `labour_market_town_pricing`, `live_state_ownership`, `living_stock_crops`, `living_stock_trade`, `living_stock`, `menu_seed_and_saves`, `menu_seed_choice`, `one_goods_market`, `opening_floor_and_thin_trades`, `options_from_settings_table`, `people_attrition_scholars`, `perf_optimizations`, `policy_auto_hire_and_closure`, `population_farm_technique`, `project_pacing`, `quote_matches_charge`, `real_output`, `refusal_cash_remedies`, `regional_weather_wiring`, `risk_precaution`, `round8g_display`, `run_reproducibility`, `seed_saved_both_modes`, `shipped_opening_game`, `spin_up_money_supply`, `staff_ledger_and_idle_trades`, `staffing_closures_explained`, `state_arrears`, `state_borrowing_gate`, `state_soldier_trade`, `stuck_matches_start`, `training_ledger_and_hazard_reports`.

Measure: `mkdir /tmp/cold && cp .cache/test_topic_seconds.json /tmp/cold/ && ROME_CACHE_DIR=/tmp/cold python3 -m sim.tests --slow --timing`
(the cold run 464 names), then the per-topic table at the end.

What it would take: find what these topics share (a full game built per topic, its own spin-up or cold price
solves, years stepped that the check does not read) and cut that once, then each remaining slow topic onto
`unopened_sim`, a shared stepped game, or fewer years, as 464 lists. `full_length_opening_checks` runs full
spin-ups whenever the shipped openings are stale; it is fast only when `openings/` matches the source.
Related: 464, 497.
