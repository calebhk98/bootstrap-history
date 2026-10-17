# Dozens of slow topics exceed the runner's time limit on a cold cache

**Status:** partly - the shared cost is cut (every game build re-opened a whole economy for the coin's margin); re-measure the rest

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

## Shared cause found

Every `Sim` build, spin-up cached or not, ran `priced_at_the_margin` (`sim/engine/economy_port_coin.py`), which
opened a whole blank economy (`settled_income_per_head`, two passes) only to read the backing good's marginal
cost. That is most of a game build when the spin-up is on disk, and it was not cached. It is now kept in
`.cache/backing_margin`, keyed like the spin-up (setup digest and the spin-up's source), and
`test_backing_margin_cache.py` shows the kept margin equals a fresh opening's. Profile (cold, one `sim()`):
the opening 150 s of 225 s profiled, 62 s the spin-up; warm, 66 s of 68 s profiled was the margin. Measure:
`ROME_CACHE_DIR=<dir with only test_topic_seconds.json> python3 -m sim.tests --slow --only <topic> --jobs 1`,
a second run in the same directory being the warm one a topic sees after the runner's warm start.
Warm game build: about 24 s before, about 2 s after. A fresh clone's first game still pays the margin once
unless `openings/` is regenerated (`simulator.py openings`), which now ships `backing_margin` entries too.

Topics (warm start, one at a time, `--jobs 1`): `actor_treasury` 178 s to 18 s, `state_arrears` 139 s to 13 s,
`one_goods_market` 260 s to 34 s, `living_stock` over 95 s to 71 s, `early_playtest` 54 s after. `allocate`
cold 141 s of which a variant game (farm changed before the first step, so its own spin-up) is about 54 s; its
check needs the unopened start, so it stays. Not re-measured: the rest of the list.
