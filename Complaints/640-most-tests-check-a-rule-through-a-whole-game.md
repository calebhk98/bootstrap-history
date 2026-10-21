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
