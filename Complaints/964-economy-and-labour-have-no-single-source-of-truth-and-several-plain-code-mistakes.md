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
  `ENDOGENOUS_COSTS_AND_DOMAINS.md` names `sim/engine/solve_prices.py`.
- `ECONOMY_MODEL_SURVEY.md`'s Lengnick and Eurace wage rules match neither model's code; the engine's tightness rule
  (`sim/labour/wages.py`, "in the manner of Lengnick and EURACE") rests on it.
- Code citing Eurace's `Firm_hire_workers` (does not exist) and "a wage fixed at hire" (Eurace indexes existing
  wages): `labour/market/clearing.py contracted_wage`, `labour/market/DESIGN.md`.
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

Left, each confirmed in code by the reviewer and checked by the orchestrator:

- **Labour.** Seat staff are rounded to whole people while the hours are paid (`sim/markets/port_staff.py`), actors'
  are not; a seat with no affordable bid keeps its staff unpaid while an actor loses its own. The levy is hours per
  person of demography's working age subtracted per worker of the core (`sim/markets/port_levy.py`), with a cliff at a
  full year. The core's workers and the cohorts are both rescaled to the engine's tile population while the core adds
  its own entrants and leavers, so the two people stocks drift. `hire_check` still reads the heuristic
  `national_trade_population`. Per-employer contract wages are kept in the clearing though everyone is paid the mean.
  Hours offered are counted at the pre-round wage and settled at the entry wage.
- **Goods and prices.** Unmet demand subtracts all rounds' deliveries from the first round's demand; the remembered
  price, cleared price and trade age follow the first round while volumes follow all rounds. Three cost-of-making
  calculations disagree (the sellers' ask band charges no interest). Missing prices still read as zero in carriage
  wear, the carriage fleet book, taxes in kind and one opening line. Two firm-equity definitions (with and without stock).
  `INVESTMENT_INERTIA` is 2 from a Eurace unit test where Eurace's shipped state uses 10.
- **Structure.** `bash tools/done_check.sh` passes; the `legacy_labour` view is read only by tests (they reach the live
  labour object through it). Functions still take the whole record and reach across its parts; `tools/done_check.sh` prints counts
  but never fails; no tool checks the package walls (three imports past an `api.py`); `YearInputs.working_age_share`,
  `api.wages_by_trade`, `market_floor_ratio` and `port_world._price_tables` are dead; pyflakes lists many unused imports.
- **Documentation.** `ONE_PRICE_OWNER_PLAN.md`, `STATE_OWNERSHIP_MAP.md`, `ECONOMY_AGENTS.md`, `PACKAGE_WALLS.md`,
  `sim/ARCHITECTURE.md` sections 8-9, `sim/labour/market/DESIGN.md` and the `sim/engine` and `sim/world` package
  docstrings describe deleted code; open Complaints 507, 513, 537, 556, 613 and 657 describe mechanisms this branch
  removed or fixed; most of the 960 and 961 parked patches no longer apply.
