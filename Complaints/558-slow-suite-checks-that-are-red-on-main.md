# Slow-suite checks that are red on main

**Status:** open

A red slow suite on the default branch means every branch's slow run starts red and its own regressions are read against
noise. This file is the current list: one entry per failing topic, naming the complaint that owns the fix. Where the subject
is an open design issue, that complaint leaves the check failing on purpose; it is never loosened to go green. Older entries
are in `Complaints/reports/558-history.md`.

Measured: the full slow run on main 3cb9c9a0, 2026-10-21, `python3 -m sim.tests --slow --jobs 3 --timing` in a checkout pinned to
that commit. Re-run the same command for the current list; this section is replaced, not appended, each time.

## Full run on 35396164 (2026-10-22)

`python3 -m sim.tests --slow --jobs 3 --timing --topic-seconds 1500` in a checkout pinned to 35396164: the topics that failed
against the run on 3cb9c9a0 are listed by `comm` of the two runs' failing topics. Ten earlier reds are green (among them
`baseline_fixture`, `economy_bronze_market_price`, `real_output`, `scenarios_batch3`, `one_goods_market_scenario`); the new reds
came with this branch's merges and are being fixed in four groups: founder pay and affordability (crashes in
`estimated_revenue` and `venture_real_earnings` after the merge that pays the founder from the clearing), state budget and
actors, merchants that stopped shipping with the wage and firm checks, and soils, farm and the package and unit guards. Each
entry below is updated as its group lands.

## Left red after the four fix groups (2026-10-22)

- `firm_expansion_scenario` "a firm ends larger than it was founded" (bound: more than one and a half founding sizes): after a
  tenfold market, eight firms end at one and a half (one expansion step) and the rest at one. Since 679 an added step weighs
  the site rent and manager hours it carries, so no firm takes a second step and entry serves the rest. Whether one step is
  right is not measured; the bound is kept. Command: `python3 -m sim.tests --slow --only firm_expansion_scenario --jobs 1`.
- `complaint_467_trades_open_to_the_jobs`: green since seeded trades are bounded by their hirers' hours (556).
- `staff_closure_reopening_scenario` (auto_hire reopens every closure that free staff could run): improved by the wage bound
  and the joint bids (more concerns open) but some stay shut because the founder's household runs out of cash in the first
  years; its input bill reads making costs that sit far above the engine's table while some outputs' prices carry surpluses
  worth thousands of coin an hour to an employer (473). Command: `python3 -m sim.tests --slow --only staff_closure_reopening_scenario --jobs 1`.
- `state_debasement_prices_scenario`: green again on fc5ef363 (after households read a perceived price level, 473 Update 14).
- `hot_path_caches_scenario` CPU budget: an early year measured just over its budget on a loaded machine (three slow jobs and
  agents); under the budget alone after the fetch-cost search was made fast (678). Re-measure alone before treating it as red.
- `purchase_limited_by_offered_volume_scenario` "the economy offers the staple on the founder's tile": no wheat grown at Rome's
  opening (473 Update 15).
- `real_output_validation`: not new; the same output-per-head check `real_output` failed on 3cb9c9a0 (473).

## Honest validations of open problems (stay red until the owner closes)

- `baseline_fixture` (rate not settled by a hair; since the wage bound, 678, the quiet fixture's ore output runs a cycle of
  about seven years and the first-to-last stock comparison lands peak against trough), `baseline_rome_full_length` (rate not settled; the mint replaces a small share of the
  coin that wears), `spin_up_money_supply_full_length` (money stock falls against wear; mint replacement negative),
  `real_output` (output per head after a population fall), `real_output_baseline` (goods far from baseline carry much of the
  basket), `economy_money_regimes_norse` (weighed-metal price level): 473, the opening that never settles.
- `price_over_making_cost_band_validation` (the typical traded good sells at no less than its cost of making): it reads one
  year of the unsettled cycle (473 Update 11), so it flips with the cycle's phase; red again after the planning-price cap
  (473 Update 12) at a median just under one. Earlier: red since the
  sourced household work hours (645, merge e72b36c0) took about two thirds more of each household's day; the median good opens
  at about nine tenths of its making cost at year 4. Traced (473 Update 11): the data change alone does it, the opening
  (year 0) is unchanged and both sides read the same wages; the sourced day moves the unsettled cycle's phase, so year 4 lands in a
  dip of a median that otherwise hovers about one. Owner: 473 (the cycle). Measured with
  `python3 -m sim.tests --slow --only price_over_making_cost_band_validation --jobs 1`.
- `economy_state_budget_validation` (a balanced budget keeps the state's coin share; printing raises prices): 526 and 473.
- `economy_tin_dearer_than_copper`: 511 (GitHub #65).
- `economy_bronze_market_price`: passes at the owner's bound (an order of magnitude; 502 closed).
- `occupational_distribution`: reads people by main occupation since 619's fix; agriculture is inside its band, textiles,
  building, food processing, transport and crafts are far below theirs (the non-farm trades are under-built; 609 to 618, 645).
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
- `one_goods_market_scenario` (again, after the opening moved off the floor): the check assumed the opening's iron price sat at the
  producers' floor; it now states the rule: the sale displaces producers, and what it does not displace comes with a price fall
  that stops at the floor (fixed).
- `one_goods_market_scenario` (earlier): asked a scenario to show a founder's sale lowering a price that sits at the producers' floor;
  the rule test holds the price rule, the scenario keeps the wiring (fixed).
- `scenarios_batch3`: the cash-book check ignored the ledger's own rule for a small gap from the saturating revenue ceiling
  (fixed).
- `population_farm_technique_scenario`: honest, 513 (a technique releases no farm hands on fully worked opening land).
- `foreign_actor_trade_scenario` ("...and no longer swings from year to year"): was red until 672 (closed: idle capacity is no longer stock); green now.
- `subsistence_staple_is_civilisation_data`: expected the staple's labour to move the floor more than wheat's, but land rent is
  priced in wheat (`solve_prices.land_rent_hours_per_hectare`), so wheat's sourced labour reaches every grain; now a rule test
  of the floor schedule (fixed).

- `firm_count_whole_game_scenario` ("entry does not overshoot", largest market only): fixed, filed as 679 (closed). The count
  fell after the entrants because their plants ran at a pilot adoption share while the site was charged whole, and because
  firms expanded without weighing the rent and management a step adds. Command: `python3 -m sim.tests --slow --only firm_count_whole_game_scenario --jobs 1`.
- Baselines re-run on this branch (`--only baseline_fixture,baseline_rome_full_length,spin_up_money_supply_full_length,real_output_baseline,real_output_validation,occupational_distribution,farm_edges_scenario --topic-seconds 3000`):
  the same reds as above, all 473 or 619; a population fall still raises output per head well above the undisturbed run.

## Timed out at the default topic limit

- `plagues_from_contact_validation`: passes alone (`--only <topic> --jobs 1`); timed out only under the three-job load.
- `farm_edges_scenario`: alone it runs past the default limit and then fails honestly on the farm share (619). Speed: 497, 557.
