# Economy and labour have no single source of truth, and several plain code mistakes bias producers and hiring

**Status:** partly - most of A, B, C, D fixed on branch economy-labour-single-source-cleanup; a re-audit of that branch (below) lists what is left

Found by a read-only audit (one orchestrator, six reviewers), every item opened in code. Re-run the audit with
`Complaints/reports/economy-labour-audit-prompt.md`. Complaints 962 and 963 were diagnosed by ablation on code that
had the mistakes below, so their conclusions ("the opening is low-employment by construction") are not settled
until these are fixed.

## A. Plain code mistakes (the code contradicts itself)

1. **Expected sales are learned in output units but used as runs.** `runs_sold` (`sim/economy/year_close.py`)
   divides quantity sold by `per_run` without `yield_factor`; everything else (`opening.py` seeding,
   `opening_basket.left_for_households`, `producers.plan`, `labour_state.producers_hours_needed`) treats
   `expected_sales` as runs to work. A producer with yield y plans y times the runs demand needs. The stock gap in
   `producers.runs_for_stock` (`stock / made`) and the unmet term of `expected_sales.demand_seen` have the same slip.
2. **The labour core re-offers hours that bondage and the levy took.** `clearing.py` supplies
   `workers * hours_per_worker_year * share_at(wage)`; `share_at` (`labour_supply.py _share_over`) is a ratio over
   the offers already cut by `bondage_hours.place_held`/`place` and the levy (`year_labour.labour_offers`), so cut
   hours come back. Market supply follows the core's head count, not the households' offers.
3. **Respend rounds overwrite the first round's market results.** `ledger.clearings` holds respend results too;
   `close_agents` builds `traded` and `clearing_prices` by (good, area) with last-wins, and `learned_prices` the same,
   so producers and merchants learn the respend's sliver instead of the year's trade.
4. **Respend never lowers unmet demand.** `goods_respend_year._settle` adjusts `record.volumes` and `record.unsold`
   only; `record.unmet` and `ledger.unmet_demand` keep the first round's figure, feeding `market_size`,
   `demand_seen` and entry.
5. **Unmet demand is evaluated at the sellers' mean price** (`unmet_quantity(bids, result.price, result.quantity)`
   in `year_goods.py` and `entry.py`), while buyers chose at each seller's ask; it subtracts traded, not delivered.
6. **`record.volumes`, `unsold` and `unmet` are never reset** for a market that had no orders this year (written only
   inside the cleared-markets loop of `year_goods.py`); `memory.volume_weights` is zeroed for the same keys.
7. **Employer pay premiums are computed and never paid.** `Clearing.paid_by_employer` has no reader; every fill is
   paid `average_wage` (`year_labour.py`).
8. **A save drops between-year changes.** `flush_record` (`sim/markets/port_year.py`) exports only when
   `_record_stale`; `move_goods` and `found_bank_from_outside` (`sim/markets/commands_applied.py`) mutate the live
   economy without setting it, so under `--session` the change is lost.
9. **`output_by_tile` is not saved** (absent from `EconomyRecord.to_record`) but is read between years by state
   revenue (`port_year.output_tonnes_by_tile` -> `actors/world_revenue.py`). The save lists fields by hand.
10. **`Economy._own_options` is cached forever**, so recipes admitted mid-game (`late_recipes.admit_recipes`) never
    reach household plots in a live game, while a loaded game sees them.
11. **The ask floor values the plot as if every worker held land** (`labour_ask_floor.ask_floor_by_tile`), while the
    hours schedule uses land actually held (`household_hours_year`).
12. **Wage mirror keeps opening seeds forever** (`labour_state.mirror_wages` writes only positive wages, never
    deletes), read by carriage and state bids.
13. **Missing prices read as zero in decisions**: `producers.offers` `expected.get(good, 0.0)`, `year_goods` state
    surplus `or 0.0`, `land_bid_year` crop margin, `carriage_fleet_book` opening-price substitution.

## B. Facts with more than one owner

- **Labour: two systems.** The economy's core (`record.workforce`, cleared by `sim/labour/market/`) and the engine's
  staff books (`sim/workforce` seat `employees`, slaves, freedmen; agents' workforce and army) never meet:
  `AgentOrders.labour_bids` is never filled from outside the economy; the core-reservation views of Complaint 556
  (`staff_book.free_core_people*`, `reservations_over_core`, `unreserved_people`) have no production caller.
- **Wages:** core `MarketState.wages` and `entry_wages`, `memory.wages` mirror, the engine `WageSchedule` with its own
  tightness rule (`sim/labour/wages.py`, stepped by `UpdateWages` from `demography/recovery.py`), founder
  `quote_annual` with its own pressure record, `port_year.wage_per_hour` for unhired trades, `notional.mean_wages`
  (unweighted), `country_figures.wages_per_hour`, `api.wages_by_trade`, `_outcome`'s `rows[0][0]` fallback.
- **Training premium:** `sim/labour/market/premium.py` (multiple, continuous) and `sim/economy/labour.py` (extra share,
  annuity) give different wages for the same trade.
- **People by trade:** core workforce, `labour_population.national_trade_population` (density heuristics and pool
  fallbacks), demography, `country_figures`, `api.people_by_trade`, port copies. Migration in the core is never
  written back to cohorts or demography; `YearInputs.working_age_share` is read nowhere.
- **Hours hired:** `Clearing.hours_hired`, `MarketState.hired_hours`, `LabourResult`, `record.hours_hired`,
  `ledger.hours_hired` (paid only, plus bonded), `YearOutcome.hired_hours`, founder head counts.
- **Army and levy:** agents' army and soldier workforce, corvee hours, `actor_staff_nationwide`, `standing_draw`,
  economy state bids; no soldier leaves the core's workers.
- **Prices:** `memory.prices` (smoothed, called "traded"), `cleared_prices`, `usual_prices`, producers'
  `expected_prices`; national price by `national_prices.py`, `country_figures.scan_prices` and `api._port_share`.
- **Cost of making:** `notional.making_costs`, `seller_offers.unit_cost`/`entry_trial`, the solver cost tables
  (`sim/prices/tables.py`, read by `goods_offers._home_prices` as a silent fallback), `unit_cost.py`.
- **A second price model:** `sim/markets/rules.category_ratios` (supply to a power) drives actor entry and capacity
  beside the economy's cleared prices; `sim/markets/clearing.py` mixes the old `world.market` ratio with economy
  volumes.
- **Food:** demography's farm year (`world/farm_year.run_farm_year`, seat farm stock) beside the economy's farms and
  plots (Complaint 537).
- **Running a business:** Complaint 514.

## C. God objects, hacky access, caches

- `EconomyRecord` (every function takes it whole; `producers`, `cohorts`, credit fields written from many modules)
  and `EconomySetup` (documented as fixed, mutated by `late_recipes`, `sites`, `port_cropland`, `port_year`).
  `sim/markets/port*.py` reads `economy.setup`/`economy.record` directly.
- Caches kept in other objects' `__dict__`: `workforce_version` in labour's `MarketState` (missed by
  `flight_year.move_back`), `country_figures` memos (not keyed on tile owners), `api._port_shares`,
  `port_year` `_seat_offered`, `labour_population`/`labour_settlement` memos.
- `getattr(record, "tenancies", {})`-style reads of fields that always exist (titles*, lending, mint,
  household_work_year, carriage_hours).
- `labour_wages.wage_schedule()` writes the cached schedule's `money_per_labour_hour` on every read.
- `legacy_economy` view read by string in non-test code.

## D. Dead code

`notional.thin_market_prices`, `labour_state.hold_back`/`give_back`, `year_labour.held_share_by_area`,
`Clearing.paid_by_employer` (or wire it), `YearInputs.working_age_share`, `AgentOrders.labour_bids` (or wire it), the
core-reservation views of 556.

## E. Measures that cannot fail

`tools/done_check.sh` excludes `sim/economy` from "money writes outside owners" and reports zero legacy reads while
`view("legacy_economy")` is read outside tests; `tools/check_module_reads.py` checks only `view(...)`/`send(...)`
names, not attribute reach-through.

## F. Documentation that describes the code wrongly

- `STATE_OF_THE_PROJECT.md` and `ECONOMY_AGENTS.md` name `sim/engine/economy_port*.py` (now `sim/markets/port*.py`);
  `STATE_OF_THE_PROJECT.md` describes the opening rate as unmerged and reasons from a deleted savings wish;
  `ENDOGENOUS_COSTS_AND_DOMAINS.md` names `sim/prices/solve_prices.py`.
- `ECONOMY_MODEL_SURVEY.md`'s Lengnick and Eurace wage rules match neither model's code; the engine's tightness rule
  (`sim/labour/wages.py`, "in the manner of Lengnick and EURACE") rests on it.
- Code citing Eurace's `Firm_hire_workers` (does not exist) and "a wage fixed at hire" (Eurace indexes existing
  wages): `labour/market/clearing.py contracted_wage`, `labour/market/DESIGN.md`. Fixed (2026-11): `contracted_wage` is gone and
  the design note says there is one market wage per trade and area, paid to retained hours too; the five reports
  (`model-run-bam`, `model-run-jmab`, `model-run-lengnick`, `research-labour-models`) carry a note saying the same.
- Docstrings: `YearView.price` ("traded price" is a smoothed blend), `notional.py` ("never feed back"), `Clearing`
  (`paid_by_employer`), `labour_supply.py`, `year_labour.py`, `record.py` `unsold`/`unmet`.
- Reports: `research-short-run-supply-elasticity.md` (0.225 is not in the code), `labour-models-compared.md` (Rome
  row unsourced), `model-run-lengnick.md` and `model-run-bam.md` (headers say not run), `research-reference-economy-
  models.md` (Eurace credit rate from the manual, not the C), `economy-research-price-stability-and-entry.md`
  (Mark-0 replacement and inventory pricing contradicted by source), `research-labour-models.md` (`vacancy_raise`).
- Complaint 556 claims hires are taken out of the core and names files that do not exist.

## Questions for the owner

Answered by the owner:

1. The founder, governments and businesses hire from one labour market; every employee is in the economy's labour
   core, and a seat's staff book is a view of its hires.
2. Food has one model: the economy's farms and plots; demography's farm year is retired.
3. One wage per trade and area for every employer. Different rates for different kinds of employer (a player, a
   country, the public market) are a later enhancement, since the spread within a trade is small next to the spread
   between trades; `paid_by_employer` and the per-employer premium are removed.

4. A seat's goods purchases and sales are orders that settle at the year's clearing, as hiring does (owner's answer):
   one trade path for seats and actors; a purchase arrives at the year's end at the cleared price.

## Re-audit of the cleanup branch

Six reviewers ran `Complaints/reports/economy-labour-audit-prompt.md` on the branch after the cleanup round (nothing was
run but compile and import checks, by the owner's rule for that round). Fixed and confirmed in code: A1, A2, A3, A4, A6,
A7, A8, A9, A10, A11, A12; one training premium; the engine wage tightness rule; the analytic category price model, the
static market book and partner books; demography's farm year and the engine farm allocation; seats', firms' and states'
staff hired through the labour core; `workforce_version` and the other economy caches; the frozen setup; the dynamic
save. The re-audit found two crashes the round introduced (a seat's staff bids called a renamed function; a missing
import in `sim/markets/port_bondage.py`), fixed at once, and found with `python3 -m pyflakes sim` that no other
undefined name remains.

Everything that re-audit listed as left has since been fixed on the branch except the whole-record functions and the
unused imports. Seats' goods trades and project materials are now orders settled at the clearing (owner answer 4),
commissions and herd labour are one-year labour orders, and each record part names its writers
(`tools/check_record_owners.py`, failing in `tools/done_check.sh`).

## Audit pass 3 (commit 2701295)

Six reviewers ran the audit prompt again; the orchestrator opened a citation from each. Left:

- **Project materials.** `settle_project_materials` (`sim/materials/project_bill.py`) cuts the bill by the orders' money at
  their limits whether or not they fill, and the gate in `sim/projects/progress_phase.py` releases the project when no
  order is outstanding without checking the materials arrived. The limit includes carriage and the project factors, but
  the clearing charges the market price and refunds the rest, so those costs vanish. Orders are checked against cash one
  by one (`goods_market.post_order`), staff bids are funded first, and an order that cannot be paid is dropped silently.
  The gate also holds on a player's own buy of the same good.
- **Labour.** The founder's own wage work is paid from `EDGE_EMPLOYERS` at the quote plus a reputation bonus, outside the
  core (`sim/labour/labour_wages.py work_for_wages`, `labour_job.py` and `wage_fallback.py` (both since deleted)). Plague survival rounds
  fractional staff to whole people (`sim/workforce/rules.py surviving_people`). `labour_market_api.in_current_money`
  scales the cleared wage again by the civilisation's static wage and price indices, and `wage_index` is still a second
  wage level (screens, score, demography's wage event). Founder-trained apprentices and granted staff are added to the
  staff book, not to the core, and vanish at the next settlement. The core's migration is rescaled back to demography's
  tile totals each year and demography runs its own migration; the working-age share stays the opening's. Staff are
  funded at a multiple of the wage, so a seat that cannot fund the ceiling loses all its staff for the year. A
  commission for a trade the economy lacks is dropped while the reply says it was posted. Herd labour hired two years
  earlier can be reused. Living cost nets an estimated wage bill, not what the clearing paid. Hours per person differ
  between lit works and the economy's fixed working year.
- **Goods and prices.** Missing prices still read as zero in revenue ranking (`producers.py paying_output`), the opening
  (`opening.py`, `opening_runs.py`, `opening_income.py`, `opening_stationary.py`) and a missing interest rate
  (`notional.making_costs`, `market_memory.interest_rate`). Unsold is measured against the first round's offer. A seat
  can buy and sell the same good with itself. Dues are priced at the opening wage.
- **Bankruptcy.** The debt write-off target counts stock; Eurace's `Firm_bankruptcy_rescale_loans` uses capital and
  cash only (`Financial_Management/Firm_Financial_Management_Functions.c`), so a bankrupt firm with stock gets too small a
  write-off.
- **Structure.** `tools/check_record_owners.py` misses writes through unannotated `memory` parameters
  (`market_memory_asks.py`, `opening.py`, `opening_plans.py`), loan rows changed by `secondary_trade._move_loan`,
  `Contracts` methods, and tables passed to the owner's helpers from many modules; `book` has no owner. `Labour`
  (eleven mixins) and the markets port `AgentEconomy` are still god objects; the port keeps unsaved state read across
  years (`outcomes`, health figures reset on each load). `getattr` on always-present setup fields remains. The
  `legacy_labour` view exists only for tests.
- **Documentation.** `PACKAGE_WALLS.md` and `ECONOMY_AGENTS.md` say nothing checks the walls; `STATE_OWNERSHIP_MAP.md`,
  `sim/markets/state.py` and `sim/ARCHITECTURE.md` section 9 still describe seats' trades outside the clearing;
  `sim/ARCHITECTURE.md` section 7 and CLAUDE.md section 3 omit the new checks; several docstrings name
  `economy_port*.py`; five reports and this complaint's earlier text still describe per-employer contract wages;
  Complaints 962 and 963 were diagnosed before the A1/A2 fixes and need re-measuring, as does
  `Complaints/reports/rome-unemployment-audit.md`.

## The one run of the suite (after audit pass 3's fixes)

`python3 -m sim.tests --slow` was run once on commit 70a6d6b: most failures were tests whose stand-ins or expectations
the branch had outdated (fixed or deleted by reading, since the owner allowed one run). It exposed real bugs, fixed:
the workforce read an undeclared economy view in every hire check; a state's surplus works read a field the work no
longer has; an actor's copying cleared the crew the labour core had hired, so firms never found staff; the
unused-import pass had removed imports kept for what importing does (figures, commands, kinds, seat state, constants);
and with the core's entrants deleted no trade could start or grow (the young now weigh a whole career against the
unskilled wage, `sim/labour/market/switching.py`).

Left, for the next run to settle:

- The suite has not been run since those fixes; tests were fixed by reading only.
- `sim/tests/protocol_golden/*.json` need re-recording (`python3 -m sim.tests.test_protocol_golden --record`).
- `religion_mod_smoke`, `urbanisation_mod_smoke`, `mod_kernels_smoke`, `pollution_mod_smoke` and `hash_seed_order`
  timed out at the topic limit; read as slow, not hung.
- In a sloped-demand fixture of the labour core a trained trade's wage falls below its workers' reservation while
  supply matches demand (seen by the agent fixing the inflow, from a scratch script): a clearing or wage-stickiness
  problem to measure.
- Shipped openings need regenerating (the port split changed the spin-up cache keys).
- God objects: every module class derives from `Module` alone and holds its behaviour as parts (`PARTS`,
  `sim/assembly/module.py`; `sim/ARCHITECTURE.md` section 2). `Labour`, `ActorWorld`, `CountryWorld`, `Government`,
  `Firm` and `GoodsMarket` hold plain parts. Audit pass 4 lists what is left.
- Two runtime breaks this round were found only by reading (a reader called methods its object lacked); a static
  check of `self.<part>.<method>()` against the part's class would catch these without a run.
- `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 20` on commit 70a6d6b printed nothing and was
  stopped by a two-hour timeout (exit 124) while building the opening from cold (the port split changed the spin-up
  cache keys). Slow or stuck is not known; the next run should dump the stack periodically
  (`python3 -X faulthandler -c "import faulthandler,sys; faulthandler.dump_traceback_later(300, repeat=True); ..."` or
  an equivalent wrapper) to show where the opening spends its time.

## Audit pass 4 (commit e8a29ba)

Six reviewers ran the audit prompt again; the orchestrator opened a citation from each. Fixed at once: the markets port's
reader (`PortWorld`) was called with `view` and `draw_deposit`, which it lacks, so every economy year would have raised
(`sim/markets/port_year_inputs.py`, `port_staff.py`, `port_goods_orders.py`, `port_sites.py`). Being fixed:

- **Hubs.** `WorkforceWorld` (`sim/workforce/world.py`) forwards every view the labour parts read; `EconomyPort` and
  `PortWorld` (`sim/markets/port*.py`) are facades, and `PortWorld` exposes private names (`_material_prices`,
  `_material_tag`, `_material_market_tonnes`, `_pooled_farm_weather_multiplier`). `SharedPart.__getattr__`
  (`sim/agents/country_part.py`) forwards any missing name to the home part. `Actor`, `RecordedActor`, `ActorRegistry`
  and `Business` are large classes.
- **Private reaches.** Parts reach other parts' private members (`grep -rnE "parts\.[a-z_]+\._[a-z]" sim`), and
  several modules reach private fields of objects they do not own (`registry._research_costs`, `titles._held`,
  `merchants._candidate_routes`, `goods_market._crossing`, `economy._own_plot_options`, `instance._world`,
  `labour_market._dominant_output_key`). The registry keeps caches in its `__dict__` (`_tile_owners`, `_patent_index`).
- **Assembly.** A declared name that clashes with a `Module`/`Part` helper binds silently; a mod layer method that is not
  declared is a silent no-op; mod overrides do not reach part-to-part calls.
- **Labour.** The working year changes between posting staff and settling them (`port_year.run_year` posts, then the
  economy applies the year's hours), so staff come out scaled by the ratio of the two years. Newcomers placed before the
  step are scaled down by `_follow_population` with everyone else. The young of a trade cannot choose that trade, so a
  trained trade that pays best is drained (`switching.py`). A refused staff funding is silent and the whole staff goes.
  The founder's wage work for a trade the economy lacks is dropped while the log says it was offered; a sale that warns
  does not reduce the hours left (`wage_fallback.py`). Plague losses and pool writes are undone by the next clearing or
  resync. The scholar and craft hands gates count commissions differently. `pay_book` mixes lifetime and yearly sums.
- **Goods.** `joint_labour_ceilings` gives a trade with no wage seen a ceiling of zero while another trade has one.
  Missing values still read as zero in `rates.charged_rate`, `opening_stationary`, `year_accounts`,
  `households_store`, `land_bid` and seat concern revenue. Three price records coexist in market memory and the
  smoothed one is labelled traded. Route dues scale the toll with the wage. Self-trade wash counts as unmet demand. The
  opposite-order refusal tells the player to cancel an order no command cancels. Carriage and the cost factor on a
  seat's goods order may reach no carrier. Refused project material orders are forgotten, `reconcile` matches by
  material, and a reorder with no price holds a project for ever.
- **Citations.** `goods_respend.py` quotes a sentence Eurace does not contain; `runs_for_stock` and the firm write-off
  differ from the Eurace rules they cite without saying how.
- **Checks.** No permanent check catches a call to a method the receiving object lacks, a private part reach, or a
  multi-base class outside five packages.
- **Documentation.** Docstrings name deleted files and removed mixins; `ACTORS.md`, `MOD_HOOKS_PLAN.md`,
  `MODULE_MIGRATION_TASKS.md`, `mods/README.md` and `sim/labour/market/DESIGN.md` describe code that is gone; many
  older complaints cite paths that no longer exist.
