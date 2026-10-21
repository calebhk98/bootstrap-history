# Slow-suite checks that are red on main

**Status:** open

A red slow suite on the default branch means every branch's slow run starts red and its own regressions are read against
noise. This file is the current list: one entry per failing topic, naming the complaint that owns the fix. Where the subject
is an open design issue, that complaint leaves the check failing on purpose; it is never loosened to go green. Older entries
are in `Complaints/reports/558-history.md`.

Measured: the full slow run on main 3cb9c9a0, 2026-10-21, `python3 -m sim.tests --slow --jobs 3 --timing` in a checkout pinned to
that commit. Re-run the same command for the current list; this section is replaced, not appended, each time.

## Honest validations of open problems (stay red until the owner closes)

- `baseline_fixture` (rate not settled), `baseline_rome_full_length` (rate not settled; the mint replaces a small share of the
  coin that wears), `spin_up_money_supply_full_length` (money stock falls against wear; mint replacement negative),
  `real_output` (output per head after a population fall), `real_output_baseline` (goods far from baseline carry much of the
  basket), `economy_money_regimes_norse` (weighed-metal price level): 473, the opening that never settles.
- `economy_state_budget_validation` (a balanced budget keeps the state's coin share; printing raises prices): 526 and 473.
- `economy_tin_dearer_than_copper`: 511 (GitHub #65).
- `economy_bronze_market_price`: passes at the owner's bound (an order of magnitude; 502 closed).
- `occupational_distribution` (agriculture share below its band; services and state the largest non-farm group): 619 (GitHub #64).
- `sited_ore_price_over_cost_validation`: the ratio bound holds for every common ore; the red line is the not-vacuous guard,
  because Rome's cassiterite market holds the opening stock unsold with no buyer (its smelters have not bought yet): 473.
  Silver and gold stay 519's.
- `farm_surplus_intake` (a food technique raises no intake): 513, see its finding on fully worked opening land.
- `full_length_opening_checks_{england,han,mexica,norse,rome}`: the shipped openings are stale, by design until the opening
  settles (473); regenerate with `python3 sim/simulator.py openings --prune` then.

## Being fixed on `complaints-triage-and-slow-measurements`

- `concerns_that_pay`: a stand-in world lacked `plant_costs` (fixed).
- `engine_prices_civilization_rent`: pinned a recorded rent figure that moved with the sourced wheat labour; now checks the
  rule (fixed).
- `firm_borrows_to_enter_scenario`: compared against the first year's firm count, which now fills every niche at once; now
  compares against the opening's (fixed).
- `one_goods_market_scenario`: asked a scenario to show a founder's sale lowering a price that sits at the producers' floor;
  the rule test holds the price rule, the scenario keeps the wiring (fixed).
- `scenarios_batch3`: the cash-book check ignored the ledger's own rule for a small gap from the saturating revenue ceiling
  (fixed).
- `population_farm_technique_scenario`: honest, 513 (a technique releases no farm hands on fully worked opening land).
- `foreign_actor_trade_scenario` ("...and no longer swings from year to year"): honest, 672.
- `subsistence_staple_is_civilisation_data`: expected the staple's labour to move the floor more than wheat's, but land rent is
  priced in wheat (`solve_prices.land_rent_hours_per_hectare`), so wheat's sourced labour reaches every grain; now a rule test
  of the floor schedule (fixed).

## Timed out at the default topic limit

- `plagues_from_contact_validation`: passes alone (`--only <topic> --jobs 1`); timed out only under the three-job load.
- `farm_edges_scenario`: alone it runs past the default limit and then fails honestly on the farm share (619). Speed: 497, 557.
