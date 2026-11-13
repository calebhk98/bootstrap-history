# Economy and labour have no single source of truth, and several plain code mistakes bias producers and hiring

**Status:** partly - most items fixed on branch economy-labour-single-source-cleanup after audit passes 3 to 14 and sweeps 1 to 6 (below); what remains is the open owner decisions and the Left items

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
  check of `self.<part>.<method>()` against the part's class would catch these without a run. (Done: `tools/check_attribute_calls.py`, `check_constructor_calls.py`, `check_class_names.py`, `check_getattr_names.py`, `check_imports_alone.py`.)
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

## Audit pass 5 (commit 439135d)

Six reviewers ran the audit prompt again; the orchestrator opened a citation from each. Of audit pass 4's list, the
hubs are split into topic readers and parts (`sim/workforce/world_reads.py`, `sim/markets/port_world_reads.py`,
`sim/agents/actor_*.py`, `business_parts.py`, `registry_*.py`), the private part reaches and `__dict__` caches are gone,
the assembly refuses a name clash and a dead layer method, and new checks gate `done_check` (`tools/check_parts.py`,
`tools/check_attribute_calls.py`, `tools/check_class_bases.py` over all of `sim`). New this pass, and being fixed:

- **Crash** (correctness reviewer): the workforce `trade_registry` view read a field the module's state does not have
  (`sim/workforce/views.py`); fixed. No check looked at `self.world`/`self.seat` in a part.
- **Checks** (architecture, goods, labour reviewers): `check_attribute_calls` missed local aliases, protocol-typed
  actor worlds and `SharedPart` forwarders; `check_parts` missed `self._parts`; fixed, and the widened check found a
  protocol that lacked a method a caller uses (`sim/agents/authority.py`).
- **Goods** (goods reviewer): entry and expansion compare demand from the first round's bids with volumes of every
  round; plant takings treated an unpriced input as free and an unpriced output as an error, and several production and
  world figures read a missing price as zero (fixed); three definitions of "traded"; a producer's first expectation
  and the state's reservation take a bare quote without the band guard; `getattr` on view fields that always exist.
- **Labour** (labour reviewer): the UI explains the wage with factors that stop entering it once the economy opens;
  two stores both called hours hired, one before payment and without bonded hours; wages written by two writers;
  the working year written twice a year; the young of an underpaid trade cannot fall back to unskilled work; a refused
  staff payment zeroes the whole staff; `wage_signature` ignores the clearing.
- **Projects** (correctness reviewer): a project's material result is matched by material and tonnes, not by the
  order, so the player's own buy can be credited to a project; cancelling goods orders also cancels a project's.
- **Actors** (architecture reviewer): Business parts read Business's private index (fixed); `FounderReview` was a
  forwarder class (deleted); `holdings` meant both shares held and concerns run (the record's is now `shares_held`);
  a country part silently answered with the home country's figure for any protocol member it did not define (each part
  now lists its home-country members, and a member neither defined nor listed fails at class creation).
- **Citations** (external reviewer): the index-price clamp is daily in Eurace, not monthly; the manual's initial
  household is misread in `opening_resting.py` and a research report; "Peters 2020" is a 2022 paper with a different
  price rule; Eurace's own rule tally has two failures the report omits.
- **Documentation** (docs reviewer): `MULTI_ACTOR_STATE_PLAN.md` section 4 names classes and data switches that do
  not exist; plan stage and complaint status disagree on mods; about fifty comments name `core.py`, `economy.py` or
  `society.py` for logic that lives elsewhere.

## Audit pass 6 (commit 3c64559)

Six reviewers ran the audit prompt again; the orchestrator opened a citation from each. No crash was found. Since the
pass, every game had failed to start (a view part in `sim/materials/readings.py` had taken the name of the per-seat
memo class `demand.py` builds; restored as `seat_readings.py`), found by the first test run and not by five passes of
reading; `tools/check_constructor_calls.py` and `tools/check_class_names.py` now gate `done_check` against that kind of
error. Fixed this pass: a respend bid in the same market counted a buyer's want twice in unmet demand, entry and
expansion; a clearing with no price read as 0; "traded" now means delivered; a crew with no wage was paid nothing in
merchants' fees; a refused staff payment let a seat keep staff the clearing hired out to others; an unpayable edge
payment raised instead of refusing; eight pairs of same-name classes; a broad `except` that silently stopped
auto-commissioning; research-report lines on the Eurace manual and the Peters model.

Left:

- `tools/check_attribute_calls.py` does not follow `self.world` inside `sim/actors/world_*.py`.
- Every `act_as` into another seat replaces the seat's `active` and `employees` containers (`sim/projects/applied.py`,
  `sim/workforce/staff_watch.py`), so a reference held across an inner `act_as` writes to a detached dict; no such
  holder was found.
- `purses.cover` draws on the facility before `book.transfer` can refuse, so a refused payment can leave a draw behind. (Fixed, checked in `sim/agents/purses.py`: `cover` refuses before anything moves and answers an undo.)
- The cold opening of a full civilisation solves its opening twice (once to price the coin metal at the margin). The
  income root find now starts from the last root and stops at a relative tolerance of 1e-3, and the share of hours
  producers hire starts from its last value (`sim/economy/opening_income.py`, `opening_own.py`). On Rome the spin-up
  years after the opening now take most of a cold build, and the spin-up does not settle (`python3 sim/simulator.py
  openings --civs rome_100ad` refuses to ship on `spin_up_settled`).
- `RESPEND_APPORTIONED_WANTED_SHARE` (`sim/economy/goods_respend_year.py`) retires when `_wanted_adding` takes each adding bid's own wanted quantity (its demand at the ask it faced in the round) instead of a pro rata share at one price.

## Audit pass 7 (commit a622b5d)

Findings are in the scratch file `audit7_findings.md`. Reviewers ran the audit prompt with a new brief: look for
`getattr`/`hasattr` calls whose literal name the receiver's class does not define while another class does, since two
silent breaks had just been found by running (`government_of` and `active_firms` moved into registry parts, so every
country had no government and no taxed firms; fixed in 7b5552b). Findings were mostly in that class: defaulted
`getattr` on fields that always exist, a handler wrapper that turns a renamed attribute into "invalid command", an
in-band zero for a missing credit figure, and the point that `tools/check_getattr_names.py` (new in this commit) only
catches names defined nowhere. Fixed in the fix10 merges (689e466, 6a3bbbc, 4a0d8d3): one wage and supply scope for the
seat, one rule for the wage of a trade its market has not paid (`sim/economy/trade_wages.py`), the getattr probe check
resolved, an unpaid PayEdge no longer free, `purses.cover` giving back its draw.

## Audit pass 8 (commit 1277cf8)

Findings are in `audit8_findings.md`. The brief asked for readers of values that had just become `None` or a `Refusal`
and still did arithmetic on them. Found: four rules for the wage of an unpaid trade; payments that practically never
refuse because `Purses._draw` always covers a shortfall; half effects (a step noted before the payment, a result
dropped, goods taken then a refusal returning 0); every settled fill charged at the market mean instead of its seller's
ask; a missing minimum price leaving an ask unfloored (ZeroDivisionError); a price-table cache that never hit; in-band
zeros for missing prices and wages. Fixed in the fix12 merges (de435d3, 1f8a41e): one rule for an unpaid trade's wage,
supply in hours and people, derived offered hours, dead code out. The credit question was left for the owner, and was
settled later (below).

## Audit pass 9 (commit 5d8abb6)

Findings are in `audit9_findings.md`. The per-fill settlement matched Eurace for sellers only: `pair_fills` re-matched
buyers to sellers greedily in sorted order and ignored the logit allocation, so a buyer paid the greedy partner's ask
(repros by the reviewers). Also: a second unpaid-wage rule in the labour schedule, a latent crash when a location's
variable cost is `None`, unregistered event kinds, `or` zero reads of wages, freight refusal destroying goods, and the
`RESPEND` apportioning heuristic that had lost its `declare()`. Fixed in the fix13 merges (ce1cdd8, 31109f6, c1c1d36);
`RESPEND_APPORTIONED_WANTED_SHARE` is declared again with a retire target (it retires when each adding bid's own wanted
quantity replaces the pro rata share; see Left below).

## Audit pass 10 (commit 39554e8)

Findings are in `audit10_findings.md`. Buyer-side settlement now matched Eurace, and a reviewer measured it end to end.
Left-behind readers: the buyer's proceeds netted out when it also sells, mint wash and top-ups computed on pairing
quantities rather than settled ones, and about fifteen agents and actors readers that raise `NoCountryEconomy` for the
home country once the economy has no wage for a trade. The architecture reviewer proposed one total wage rule (home
never `None`, `None` only for a partner with no unskilled wage, guards deleted) and the other reviewers' findings
pointed at the same rule. Fixed in the fix13 and fix16 merges (2aa4fad, c67fa5a, 6ad0a53 "the home country's wage rule
always answers", 739bf37 "one wage rule for home and partner areas").

## Audit pass 11 (commit 11ca3b0)

Findings are in `audit11_findings.md`. The docs reviewer found nothing worth fixing. Remaining: the opening wages table
silently dropping a non-positive unskilled quote, a partner priced at the home wage through a fallback, quiet zeros in
mine cost, the home state's wage budget spread over foreign cohorts, a real-wage index mixing money vintages after a
rebase, and `PayExchange` never returning a refusal. Reported fixed in the fix16 merge (6b7927c, 709a36b). The
`wage_index` item fed the open question below.

## Audit pass 12 (commit 92e8004)

Findings are in `audit12_findings.md`. Two trade registries: the economy's setup read raw `data/world/trades.json`
while the labour side used the mod-applied registry, so a mod trade raised KeyError from every wage read; a content id
default for the servant trade in the engine (4.7); content-id literals in campaigns and coin; a late good starting in
opening-year money; a partner with an empty wage table raising `NoCountryEconomy` in many readers. Fixed in the fix17
merges (eb19d77 one trade registry, f07f3e6 partners always answer, trade ids from roles, one home rule). While merging
the round the orchestrator found import cycles in `sim/economy` and two stand-in failures, carried to the next pass.

## Audit pass 13 (commit f07f3e6)

Findings are in `audit13_findings.md`. Two import cycles (`state_budget` and `mint_labour`; `trade_wages` and
`year_labour`) made many `sim.economy.*` modules fail as a first import, found by importing each module in a fresh
interpreter; the reviewers' own import check had loaded everything in one process and missed it. Also a numeraire trade
literal in the price solver, four definitions of the unskilled wage, stand-ins missing fields, and the never-hired trade
wage question (below). Fixed in the fix18 merges (abaabbb "every module imports alone (checked)", 7b3650f unskilled
trade required, roles in place of trade literals). `tools/check_imports_alone.py` is the new gate and is slow under
load.

## Audit pass 14 (commit 4fd6918)

Findings are in `audit14_findings.md`. One fact with three discount rates: the household time preference, the
civilisation's starting rate used by the opening schedule, and a reference rate default, so an opening wage could carry
a different training premium from the household rule. Also trade literals ("scholar", "artisan") and three "generic
staff" sets, many docstrings citing sections of `agriculture.py` that live in `agriculture_core.py`, duplicate
constants (`KEY_SEPARATOR`, `HOME_SELLER`, `EDGE_EXCHANGE`, the two wage ceiling multiples), a `has_partners` cache whose
premise was false, and dead fields. Fixed in the fix19 merges (80f41b9 one training premium, fc99588 trade accessors and
one owner per shared constant, 293d05a facades, caches and dead fields). Listed as tool gaps and not fixed:
`check_record_owners` matches by parameter name; `check_module_reads` is a regular expression.

Themes that recurred in passes 7 to 14, said once: a round that turned "0 means missing" into `None` or a refusal left
readers behind; each fix to the unpaid-trade wage rule left a second rule beside it until pass 12; checks that look at
names cannot see a name on the wrong object. `docs/architecture/CHANGE_CHECKLIST.md` (eb75604) lists these classes for
every editing agent.

## Startup bugs a real game found

Two breaks were found by starting a game, not by any audit or sweep, and both survived many rounds of reading and the
quick tier, which never builds a game.

- 03538c1: the economy's wage asked before the game's money was priced reopened the economy, and opening prices the
  money from that wage, so a new game recursed. The wage answers `None` without opening the economy.
- 7ee15f2: `step_market` lost its `seats` parameter, so no year could run. The market phase takes the seats every world
  phase is given.

Lesson: the quick tier proves functions, not that a game starts. A change to a signature or to the order of opening
needs one real start-up.

## Full sweep 1 (commit cb668cd)

After the failing-topic rounds (fix21) a sweep replaced the diff audit: one reviewer per slice read every file of the
slice (`sweep1_findings.md`, slices L, E1, E2, E3, M, P+W). Findings: a crash in a hire refusal (a `Refusal` is a string
and has no `.message`), `household_room` subtracted in `hire_check` but not in training, slave purchase or staff
controls, a crash in `trim_people` mutating a dict it iterated, two reservation-wage formulas, crop labour priced at the
servant wage, many dead functions, and a duplicated Dijkstra. Reported fixed by sweep 2 in the fix22 and fix23 merges
(5825552 actors borrow only from the economy's lenders, 8e7fa6d, 9b995a1, 4419ec4, 15e0831, e006921), except the
training-row progress slot and the credit helpers move.

## Full sweep 2 (commit 995f569)

Findings are in `sweep2_findings.md`. Manumission scaled the training queue's row so a trained slave's value went to
zero (a reviewer's repro), training ignored pending rows when computing household room, a clearing read same-year and
last-year wages depending on sort order, a tax assessment overdrew a payer liable to two forms, and a never-hired
trade's wage came from the frozen opening. Fixed in the fix24 and fix25 merges (fd03b7b, d9f26f6, 09be128, 83e0a3b,
b184d85); sweep 3 reported them fixed except the pre-open `_annual` report, the `MINT_ALLOY` marker and the settling
module (since deleted, f808ada).

## Full sweep 3 (commit b184d85)

Findings are in `sweep3_findings.md`. Latent disposal cost dropped in the joint split of the solver (no civilisation sets
it today), trained slaves lost when pools shrink, the scholar family counted as scholars for the hands gate, a trade
school path that never reached the core, and the in-training figure counting rows instead of people. Fixed in the
fix26, fix27 and fix28 merges (c11ec21, 67601e5, 002b59e, f808ada, 4cf600e: a seat's draw beyond its credit line
refuses). Sweep 4 reported them fixed except the MINT marker owner call and the seat floor after lenders' room.

## Full sweep 4 (commit 1676af3)

Findings are in `sweep4_findings.md`. Merchants routed held stock but dropped it from offers so it sat out of every
market; carriage fees used a plain mean of quotes rather than traded prices; a seat could not draw the line it was
granted (the room was removed from capacity twice); a bond issuer defaulted holding cash because interest was never
paid from the purse; seat bank dividends were read as concern-sale proceeds; and import duty had no payer. Fixed in
the fix29 merges (5f05af6, 33bff8e, 9c19101) and 3f12572 for dividends. Sweep 5 reported them fixed.

## Full sweep 5 (commit fb9effd)

Findings are in `sweep5_findings.md`. Landing cargo taxed twice (verified by the orchestrator), unsold actor goods
destroyed by moving them to `EDGE_LEGACY`, store prices cached by tile instead of by basket, an exiting producer leaving
bonded people for a re-entrant of the same id, a part-paid bonded lot moving unpaid people, and a shared price history
list copied by reference. Fixed in the fix30 to fix32 merges (a10a805, d48bd35, 6f341ac, 27c170b). The owner questions
that sweep 5 only repeated are below.

## Full sweep 6 (commit 5bcd678)

Findings are in `sweep6_findings.md`. Nothing crashed or gave wrong numbers commonly; the one wrong figure reached was a
tenancy rent vintage, small. Loan ids collided across working-capital and ordinary clearings (fixed, 2fff26e); the
rest (a dead settlement shortfall report, merchant stock valued at zero when unpriced, a price floor in opening money,
home and partner coin stock rules, household-work hard path, tenancy asks before rents are posted, loan asks keyed by
borrower) were fixed in the final merges (819aff7, ec413ed, ac71e3a). Not fixed: the prices module's tree nodes per
process (the content loader is per process by design). Two owner questions came out of it: the `wage_index` quote and
the state's bond gate.

## Owner decisions

Settled:

- Actors (firms, states, seats) borrow from real lenders inside the economy, within a limit and at interest; a draw
  beyond the limit refuses instead of creating money (fix20-one-credit-limit, fix22-real-lenders-refusal;
  `EDGE_SAVERS` is gone). Every payer caps to what it can pay or answers a refusal.
- A trade nobody has hired is paid the labour core's area wage nationally too, not a frozen opening wage
  (fix20-one-wage-source, b4f4115); the unpaid-trade rule is `sim/economy/trade_wages.py`.

Open, for the owner:

- **Two treasuries per state.** The economy's state account and the agents' government purse are separate (sweep 5,
  round 23 hand-backs). Does the state keep one?
- **Price tables at opening wage ratios.** Decide whether the solver's price tables keep the opening's wage ratios or
  follow the wages the labour core pays later.
- **How the state's deficit is funded.** `state_finance.py` issues "state deficit" money (fiat issue or debasement),
  which is a real mechanism and not a leak; decide whether it stays beside borrowing.
- **Freight refused after sellers were paid.** `markets/port_goods_orders.py` moves goods to `EDGE_LEGACY` before the
  freight payment, so a refused freight leaves the sellers paid and the goods gone (sweeps 4 and 5).
- **Fixtures in the production package.** `sim/economy/fixture_setups.py` and `opening_stationary.py` are test setups
  that live in the production package.
- **`wage_index`.** The pre-priced quote `LabourMarket._annual` (`sim/labour/labour_market_api.py`) multiplies by the
  civilisation's `wage_index` and cost factors, while `WageScheduleReader.wage_per_hour`
  (`sim/labour/labour_wage_schedule.py`) does not. This matters in the open window only; decide which is right.
- **Commissioned hours.** `Hands.hours_you_can_call_on` adds commissioned hours on top of `market_supply`; a comment in
  `dispatch_ventures` says it is deliberate, the docstrings say the hours are part of the supply. Additive or not?
- **Credit limit and bookkeeping.** `set_net` and `DebitSeat` reset purse balances for bookkeeping and are exempt from
  the credit limit, labelled so. Confirm that exemption.
- **Bonds without the bond market.** `Government.advance` (`sim/agents/government.py`) calls `set_bond_terms` and
  `redeem_bonds` with no gate, while `Borrower.prepare_bonds` checks `may_issue_bonds`. Does the state need the
  `bond_market` mechanic to issue bonds?

Left from the passes and sweeps above, not owner questions:

- `RESPEND_APPORTIONED_WANTED_SHARE` (`sim/economy/goods_respend_year.py`) retires when each adding bid's own wanted
  quantity replaces the pro rata share at one price (its retire text names this complaint).
- `pay_up_to` (now the function in `sim/agents/ledger.py`, not a `Purses` method) still has callers (`bonded_sale.py`, `country_money.py`, `government.py`; `stratum_year.py` no longer calls it); sweep 4 found its retry path broken and no
  later sweep re-checked it.
- Tool gaps: `check_record_owners` matches by parameter name and `check_module_reads` by regular expression.
- The slow tier (`python3 -m sim.tests --slow`), the protocol goldens, the shipped openings and the Rome spin-up trace
  were not re-run after the fix rounds above; run them before trusting the branch.
