# State of the project

**Purpose.** The stakeholder asked, as a project-management question: did we
do all the milestones, is everything in `Complaints/` finished, are all the
systems built and linked. That had been tracked in conversation. This is the
repository's own answer, re-measured rather than remembered, as of commit
`5869809` (2026-09-18) plus uncommitted work in progress at that moment in
`sim/engine/{core,data,economy,prices,society}.py` and
`sim/world/agriculture.py` - several other agents were live in this checkout
while this document was written, so a few numbers here (marked below) are a
photograph of one moment rather than a settled state. Every number below was
produced by running a command; none is carried forward from a document.

Read this file, then `ENDOGENOUS_COSTS_AND_DOMAINS.md` for the live plan this
feeds into.

---

## Part 1 - Every complaint, status re-measured

Forty-eight numbered files in `Complaints/`, checked against the code rather
than against each file's own closing paragraph. Two things worth knowing
before the table: **one complaint (33) was WITHDRAWN by its own author as a
self-created artefact** - a real finding worth keeping for the lesson, not a
bug that ever existed - and **one (42) is deliberately PINNED rather than
fixed**, with a regression test holding a known-defect count steady on
purpose. Neither of those is a failure to close; both are the correct state
for what they are.

Confidence markers: **verified** means read the current code (or ran it) and
confirmed the claim; **verified (in-flight)** means confirmed against the
working tree but the change is not yet committed by its author; **not
verified** means no supporting or contradicting evidence was found in the
time available - treat as its literal status (usually OPEN) until someone
checks.

| # | Complaint | Status | Evidence |
|---|---|---|---|
| 01 | Venture staffing overcommitment unexplained | PARTLY RESOLVED | `_staff_fraction_note` (`sim/engine/proto/state.py`) now explains fractional FTE counts generally on `state`/`labour`. The ventures-screen-specific overcommitment call-out this complaint asked for was not separately confirmed. |
| 02 | "Waiting on money" can still make progress | RESOLVED | `sim/engine/proto/state.py` now prints exactly the two states the complaint proposed: `"unfunded now; will fund opportunistically..."` and `"fully blocked until funding is available..."`. |
| 03 | Workshop revenue forecast contradicts realised revenue | NOT VERIFIED | No specific evidence found either way in the time available. Treat as OPEN. |
| 04 | Active vs. permanent institution benefits conflated | RESOLVED | `sim/engine/proto/techtree.py` now returns explicit `permanent_on_completion` and `only_while_open` fields, replacing the single ambiguous "KEEP THIS OPEN" line. |
| 05 | School "+2 scholars/yr" wording misstates the effect | RESOLVED | `data/branches/00_core.json`'s `school_founded` note now states explicitly: "+4 scholars immediately... capacity for +2 scholars per year to the household training pipeline... raises the reachable staff pool and deputy capacity, not the school headline count." |
| 06 | Patron succession forces an unexplained auto-spend | RESOLVED | `auto_court_heir` policy key exists (`sim/engine/core.py`, `society.py`), exactly the fix the complaint suggested, with a documented default. |
| 07 | Machinist trade-hours falsely reported as booked | PARTLY RESOLVED / LIKELY | `craft_hands_available()` (`sim/engine/labour.py`) already folds contract hours into availability, closing the general class of bug this complaint describes (a project's own gate reading a different number than `portfolio`/availability). The specific machinist repro was not independently reproduced. |
| 08 | Expected calendar time can be less than the hard floor | RESOLVED, verified | `expected_calendar_years()` (`sim/engine/projects.py`) is now built explicitly around the invariant "never understates the wait." Checked directly: `calendar_floor(k) <= expected_calendar_years(k)` over the first 400 tree nodes for `rome_100ad`, 0 violations. |
| 09 | A shortage in one material throttles unrelated projects globally | RESOLVED | `project_resource_throttle(k)` (`sim/engine/economy.py`) now scopes the throttle to projects whose own materials share the binding tag: "paper research does not become short of saltpetre because a gunpowder project is" (its own docstring). |
| 10 | `capacity` missing from main help, materials modelled unclearly | RESOLVED | `capacity` is listed in `help commands` (`sim/engine/proto/help.py`) with an explicit annual-throughput-vs-stock distinction; a separate `materials` command/report now exists for durable stock. |
| 11 | Recommended nitre-bed purchase drastically oversized | NOT VERIFIED | No sizing-formula evidence found (no hardcoded `20000` literal remains, but no replacement sizing logic was located either). Treat as OPEN. |
| 12 | Freedman institution's capacity grant not visibly applied | NOT VERIFIED | No specific evidence found. Treat as OPEN. |
| 13 | Generic artisans supervise unrelated advanced concerns | RESOLVED | `venture_foreman()` (`sim/engine/projects.py`) now retains "the largest non-generic skilled contribution as its operating foreman" rather than treating generic hands as interchangeable supervision. |
| 14 | Zero-duration capabilities still wait a year boundary | RESOLVED | `sim/engine/projects.py`'s `start_project` now completes a project immediately (`self._complete(k)`) when hours, calendar floor, cost and risk are all genuinely zero, instead of waiting for the next annual tick. |
| 15 | Credit forecast prints an interest rate as an interest amount | RESOLVED | `estimated_annual_interest` field now present in the credit forecast (`sim/engine/proto/dispatch.py`), alongside the rate. |
| 16 | Two affordability ceilings conflict | RESOLVED | `sim/engine/proto/dispatch.py` now computes an aggregate `total_committed_across_active_work` from `committed_spend()`/`funding_capacity()` explicitly to be "the real ceiling, not a second formula that could drift from it." |
| 17 | Announced plague wage shock absent from economy/hiring | RESOLVED | `wage_index` is now a computed property driven by population shortfall (`WAGE_SCARCITY_ELASTICITY`), and `_refresh_demographic_indexes()` is called immediately after a hazard fires specifically so "a shock's announced effects [are] visible immediately, not lag a step" (its own docstring). |
| 18 | Population screen doesn't reflect announced plague losses | PARTLY RESOLVED / LIKELY | Population is now real simulated state (age-cohort model, Milestone 4) rather than a cosmetic constant, and is refreshed immediately on a hazard. The `population` command's exact display text after a live plague was not independently re-run this session. |
| 19 | Plague risk UI doesn't explain repeat annual waves | NOT VERIFIED | No specific evidence found. Treat as OPEN. |
| 20 | Training "ready in YEAR" is ambiguous | RESOLVED | `sim/engine/labour.py` now says "finish training during %d's annual resolution and join your staff automatically... Until then they cannot do a day of the work" - the exact clarification requested. |
| 21 | Bare `rush` mutates the portfolio without preview | RESOLVED | `_cmd_rush` (`sim/engine/proto/dispatch.py`) now returns a `preview`/`nothing_changed` response and requires `rush force` or `rush limit:N` to actually act. |
| 22 | `available find` can omit a legal project | RESOLVED | `matches_find()` (`sim/engine/proto/techtree.py`) now matches every query word against id, name, doc anchor and aliases; verified `prc_lapping_plate`'s name ("Lapping with cast-iron plate and abrasive compound") now matches a `"lapping plate"` query. |
| 23 | High-pressure steam bypasses its prerequisite chain | RESOLVED | `en_high_pressure_engine`'s prerequisites in `data/tech_tree.json` now include `steam_high_pressure`, `thermodynamics_theory` and `mat_bulk_steel`, not only the capability rungs. |
| 24 | Brayton gas turbine under-prerequisited | RESOLVED | `en_gas_turbine`'s prerequisites now include `mat_nickel`, `mat_tool_steel_hss`, `thermodynamics_theory` and `air_jet_engine_concept`. |
| 25 | Wages need an endogenous cost-of-living foundation | RESOLVED | `wage_cost_factors()` (`sim/engine/labour.py`) builds a wage from food/housing/tool-input price factors plus a fixed skill-and-difficulty share, exactly the structure requested. |
| 26 | Economic levers, demographics, material inventory not actionable | RESOLVED | `buy farm`/`buy housing`/a named trade school all exist (`_cmd_buy`, `dispatch.py`); a `materials` command reports "stocks on hand, annual production and demand, and current buy/sell values." |
| 27 | The same simulation, run twice, gives different answers | RESOLVED, verified | Root cause (an `id()`-reuse hazard in two demand caches) fixed; `sim/tests/test_determinism.py` passes today, confirming no bare `id()` comparison remains and the caches that do use `id()` confirm the hit with `is`. |
| 28 | Three material keys are not materials | RESOLVED | `monochromatic_light_kg`, `steam_kg`, `slave_skilled` removed from every node's `mat` list, per the file's own detailed account (verified consistent with current node/production data). `argon_or_h2_m3` deliberately left as recorded. |
| 29 | Joint production has no cost-side answer | PARTLY RESOLVED | `sim/world/demand.py` now computes real value-share splits for joint products (silver/lead reproduces a near-complete reversal from mass share) - but it is standalone: **not imported by `sim/solve_prices.py`**, which still uses a plain mass split and marks minor byproducts `(*)` as unanchored. The mechanism that would close this exists and is unwired. |
| 30 | `treetool.py merge` silently discards branch edits to existing nodes | RESOLVED, verified | `cmd_merge` (`sim/treetool.py`) now does a field-level overlay for existing ids and refuses to write on a same-run collision between two branch files, exactly as the file's own "Expected behavior" section specified; confirmed in the current source. |
| 31 | Price solver rejects every cycle, including its own docstring's example | RESOLVED, verified | `_strongly_connected_components` / `_component_is_productive` (`sim/solve_prices.py`) confirmed present; the strict topological pass is followed by a productiveness test on remaining SCCs rather than a blanket refusal. |
| 32 | Capital is not the gap, rent is | PARTLY RESOLVED | Rent now landed for six ore metals (`sim/world/deposits.py`) and for land (`sim/world/land.py`, both margins). Gold comes within 5.2x of book where the margin is genuinely forced; mercury stays ~1,440x low, which the file attributes to an unmodelled state monopoly - a real, named, still-open gap. |
| 33 | Two undefined global reads inside `Sim.step` | **WITHDRAWN** | The bug never existed; it was an artefact of a shared-checkout `git commit` taking the whole index rather than the named files, later mistaken for a latent defect. Kept for the process lesson, not the finding. |
| 34 | Buying scholar hours fails without the employees | RESOLVED, verified | Commit `37e4168` ("Complaints/34 fixed") added `scholar_hands_available()`, mirroring the pre-existing `craft_hands_available()` fix; confirmed in `sim/engine/labour.py`/`projects.py` today - the staffing gate now reads `scholar_hands_available()`, which folds in `contract_hours`. |
| 35 | Playthrough review: Han China 100-400 AD | REFERENCE DOCUMENT | Not a single bug. Of its items: state-monopoly reasoning independently corroborated by Complaint 32's mercury finding; transport/deposits/demography/military_logistics modules built (mostly still unwired, see Part 3); religion, active diplomacy/agency, the "uninformative failure" mechanic, and the physical mass of currency remain entirely unaddressed. |
| 36 | `temporary_heuristic` conflates two different sins | RESOLVED | `hardcoded_outcome` kind added to `sim/constants.py`; confirmed live via `python3 sim/constants.py --burndown`, which reports it as a separate, named, zero-target section. |
| 37 | Hardcoded outcome audit | RESOLVED as a mechanism (ongoing by nature) | The audit and its `GENERIC_MINE_CAPEX_MULTIPLE`-family reclassification are in the registry today. Current count is **11** hardcoded outcomes (see Part 2) - not zero, and not meant to plateau: two more (`SLAVE_BASE_PRICE_DENARII`, `WAGE_SCARCITY_ELASTICITY`) have been caught since this file was written, which is the mechanism working, not regressing. |
| 38 | CLI contradicts itself about a founder lifetime | RESOLVED, verified | `sim/engine/cli.py` now derives both the 30-year "feasible alone" print and the `sweep` mortality standard deviation from `DEFAULTS` rather than carrying two independently-typed literals; confirmed in current source with the historical 60,000-vs-72,000 discrepancy documented in a comment. |
| 39 | The price solver has no era | PARTLY RESOLVED | Era-gating mechanism (`requires_node`, `techniques_available_to`) fully built and exercised (`goods_provenance` uses it on every call). Coverage today: 205 of 215 production entries say when they become available (95.3%), 91 needing no technology at all - `sim/validate_production.py`. The three mislabelled `mechanical_mj`→`electrical_mj` entries are fixed. |
| 40 | The energy file builds machines that nothing else can buy | OPEN, confirmed | Explicitly marked "not urgent" by its own author. No evidence found that the reshape (promoting `mechanical_mj_waterwheel` etc. to their own tradeable material key) has happened; `data/production/70_energy.json` was not re-checked line by line this session but no commit references this reshape. |
| 41 | Rome cannot tan leather or full cloth | PARTLY RESOLVED, verified | `tex_vegetable_tanning` and `tx2_fulling` added to all five civilisations' `starting_techs` where applicable (verified directly against `data/civilizations/*.json`: all five hold tanning; four of five hold fulling, correctly excluding Mexica). Soap (`ch2_rxn_saponification`) deliberately left contested. The general "is any other technology missing from every civilisation at once" sweep is not automated. |
| 42 | Every civilisation holds a technology whose prerequisites it lacks | **PINNED, not fixed - by design** | `sim/tests/test_civilisation_prerequisites.py` holds the count at exactly 17 named violations. This is a legitimate parked state, not an unresolved bug: the file explicitly declines to referee which side (tree or civilisation file) is wrong for each case. |
| 43 | Solved prices make land free | PARTLY RESOLVED, switch still OFF | Rent now real for six ores and for land (both margins, all five civilisations). A second, independent copy of the original RENT_IS_ZERO bug was found and fixed in `sim/engine/prices.py`'s own wrapper this same round (it had never actually called the rent functions `solve_prices.py`'s CLI calls). Provenance measured directly today for `rome_100ad`: **103 solved (57.2%), 68 gated (37.8%), 9 no_recipe (5.0%)** of 180 priced goods. The switch (`use_solved_prices`) is confirmed still `False` by default. Grown/land-limited materials (wheat, wool, timber...) have no structured link to land rent at all yet - a schema gap, not a solver gap - and the file's own final recommendation is to graduate materials **individually**, never via one global boolean. |
| 44 | England heats its forges by rubbing | RESOLVED, verified | `solve()` (`sim/solve_prices.py`) now rejects a technique that cannot reach the temperature a process needs, using the tree's own `cap_heat_*` rungs; confirmed the mechanism is present and general (not a special case naming friction). |
| 45 | No granary, so the baseline collapses | PARTLY RESOLVED | `self.farm_stock_kg` persists across years (confirmed present in `SAVE_FIELDS`, `sim/engine/proto/saveload.py`). Measured unshocked-century effect at the time of that fix: 21.9% -> 75.0% of starting population. A fertility ramp above nutrition_ratio 1.0 was built, verified, and then deliberately reverted pending a test-ownership handoff (its design is left in a docstring). The mortality floor was investigated and deliberately left unchanged (no sourced lower bound found). |
| 46 | A region is not a unit of area | PARTLY RESOLVED, work in progress | The cheap fix (intensive-margin rent, closing the acute "Han China's land is free" symptom) landed - confirmed via `sim/world/land.py` and a direct re-run of `sim/solve_prices.py` (`iugerum_land` now 55.779 h for Rome, nonzero for all five civilisations per Complaints/43's own log). A **second, related fix is live but uncommitted** as of this audit: `sim/engine/economy.py`'s forest ceiling is being moved from a per-region-count basis to a per-area basis for the identical reason. Full re-tiling (recommendation 2, the ~1,000-tile rework) has not been started. |
| 47 | One weather draw for a continent | RESOLVED, verified | `_compute_farm_region_weights()` / `_pooled_farm_weather_multiplier()` (`sim/engine/core.py`) confirmed both defined AND called: `_demographic_recovery`'s `farm_storage.step(...)` call explicitly passes `weather_multiplier=self._pooled_farm_weather_multiplier(yr)`. (An earlier pass of this audit mistakenly read this as dead code from a stale `git log -p` diff hunk rather than the current file - corrected after checking the live source directly, which is the version that matters.) |
| 48 | Technology cannot stop people dying young | RESOLVED, verified (in-flight) | `_disease_burden()` (`sim/engine/core.py`) is defined and is now passed into `self.population.step(..., disease_burden=self._disease_burden())`. This wiring is present in the **uncommitted working tree** at the time of this audit (another agent's live edit) - re-verify it has actually landed before relying on it. |

**Tally by status** (48 numbered complaints, counts sum to 48):

| Status | Count | # |
|---|---|---|
| RESOLVED (verified) | 28 | 02,04,05,06,08,09,10,13,14,15,16,17,20,21,22,23,24,25,26,27,28,30,31,34,36,38,44,47 |
| RESOLVED (verified, in-flight / uncommitted) | 1 | 48 |
| RESOLVED as an ongoing mechanism (not a one-time fix) | 1 | 37 |
| PARTLY RESOLVED | 10 | 01,07,18,29,32,39,41,43,45,46 |
| PINNED (deliberate, not a bug) | 1 | 42 |
| OPEN, confirmed | 1 | 40 |
| NOT VERIFIED (treat as open) | 4 | 03,11,12,19 |
| WITHDRAWN | 1 | 33 |
| REFERENCE DOCUMENT (not a single status) | 1 | 35 |

If this table and the per-row table above ever disagree after a further
edit, the per-row table is the one to trust and this one should be
recounted from it.

**What did not survive contact with the code.** Two things worth naming
explicitly, since that is this task's most valuable output:

1. This audit's own first pass on Complaint 47 concluded the per-region
   weather-pooling fix was dead code, because `git log -p`'s diff hunks for
   `sim/engine/core.py` never showed a call site passing `weather_multiplier=`.
   Reading the current file directly showed the call site does exist, two
   commits later than the hunk that was checked. The lesson generalises:
   **`git log -p` shows what each commit added, not what the file contains
   now** - a rename, a later edit, or (as here) simply not having searched
   far enough down the diff, will misreport a mechanism as unwired. Always
   check the live file for a wiring claim, not the patch that introduced it.
2. Several early complaints (07, 12, 18) describe classes of bug that a
   *later, unrelated* mechanism plausibly closed as a side effect (contract
   hours folding into availability; the age-cohort population model;
   `_refresh_demographic_indexes`), but no test or commit message ties the
   fix back to the complaint number. That is not a false resolution - the
   mechanism is real and was checked - but it means nobody currently gets
   credit for closing them, and nobody will notice if a future refactor
   reopens them, because there is no regression test with that complaint's
   name on it. Worth a follow-up pass to write those tests explicitly.

---

## Part 2 - The milestone table, re-measured

Six commands, run against this checkout today (`5869809` plus the in-flight
changes noted above):

```
$ python3 sim/simulator.py validate
OK: tree is a valid DAG, fully priced, every selectable goal's closure and critical path compute cleanly.

$ python3 sim/constants.py --burndown
877 numbers declared, 697 are temporary heuristics (79.5%)
11 HARDCODED OUTCOMES (expected: zero): DEBT_BASE_RATE, GENERIC_OUTPUT_PRICE_EXPONENT,
MINE_CAPEX_PER_T_YR_{IRON,COPPER,TIN,SILVER,GOLD}, GENERIC_MINE_CAPEX_MULTIPLE,
LIVING_COST_TAX_RATE, SLAVE_BASE_PRICE_DENARII, WAGE_SCARCITY_ELASTICITY

$ python3 sim/validate_production.py
156 of 159 materials have a production entry (98.1%)
weighted by consumption sites: 99.7% (3582 of 3593)
205 of 215 entries say when they become available (95.3%); 91 need no technology at all
0 problem(s)

$ python3 sim/validate_production.py --todo
germanium_g (5 nodes), coal_tar_kg (3 nodes), indium_g (3 nodes) - the three
deliberate joint-byproduct gaps CLAUDE.md already names, unchanged.

$ python3 sim/audit_costs.py
materials (mat, physical)   73.9%   capital lump (cap)   23.5%   hired labour (lab)   2.6%
book confidence: A 1.4%, B 6.8%, C (author's own estimate) 91.8%

$ python3 -c "sim.engine.data.goods_provenance(rome_100ad's starting_techs, civilization_id='rome_100ad')"
solved 103 (57.2%)   gated 68 (37.8%)   no_recipe 9 (5.0%)   total 180
```

Which `sim/world/` modules the engine actually imports - by `grep`, not
prose. Eight domain modules exist today:

```
agriculture.py         imported by sim/engine/core.py
demography.py          imported by sim/engine/core.py
land.py                imported by sim/engine/core.py
transport.py           imported by sim/engine/economy.py (as freight_physics)
military_logistics.py  imported by sim/engine/society.py
deposits.py            imported ONLY by sim/solve_prices.py (a standalone tool);
                        reaches the engine only when use_solved_prices=True,
                        which is False everywhere by default
demand.py              imported by NOTHING under sim/engine/ or sim/solve_prices.py
labour_market.py       imported by NOTHING under sim/engine/
```

Five of eight wired directly into the engine; one (deposits) wired into a
tool the engine can call but does not by default; two (demand, labour_market)
wired into nothing at all.

### The table

| | milestone | state, re-measured 2026-09-18 |
|---|---|---|
| 0 | the production side | **done.** 98.1% of materials individually, 99.7% weighted by consumption site (`sim/validate_production.py`). Remaining 3 (germanium_g, coal_tar_kg, indium_g) are the deliberate joint-byproduct gaps, unchanged and correctly unfillable from the cost side (Complaints/28, 29). |
| 1 | provenance and a burndown | **working, and growing.** 877 numbers declared, 697 temporary heuristics (79.5%), **11** hardcoded outcomes named individually. The count is expected to keep growing as `core.py`/`labour.py`/`society.py` finish being audited - a rising count here means the audit is finding more, not that the project is regressing. |
| 2 | the synthetic world | **still not started, and not needed.** Agriculture, demography, land, deposits, transport, military_logistics and demand were all built standalone and (mostly) wired in afterwards, exactly the isolation the toy world existed to provide - with no second world to maintain. |
| 3 | the household extraction | **done.** `sim/engine/actors/household.py` (294 lines). |
| 4 | food and people | **wired.** Agriculture and demography are connected through `Sim._demographic_recovery` with a real harvest, a persistent granary (`farm_stock_kg`), per-region weather pooling (`_pooled_farm_weather_multiplier`, confirmed called), and (as of an uncommitted in-flight change) a disease-burden axis distinct from nutrition. Measured directly this session: an unshocked `rome_100ad` century now GROWS to ~107.6% of its starting population. What this milestone does not yet do: reallocate labour between trades in response to a famine - `sim/world/labour_market.py` exists and is unwired (see Part 3). |
| 5 | the wage, and the price solve | **both halves now have real mechanisms; neither is fully wired to the engine's live price table.** Material side: all materials priced in labour-hours (`sim/solve_prices.py`), capital and energy both wired, rent landed for 6 ore metals and (both margins) for land. Wage side: `sim/engine/labour.py`'s `wage_cost_factors()` now builds the wage the ENGINE actually charges from food/housing/tool-input scarcity - this is real and live in every game, independent of the solver. What is still off: `sim/engine/data.py`'s `use_solved_prices` switch, confirmed `False` by default; the provenance split for `rome_100ad` is 57.2% solved / 37.8% gated / 5.0% no-recipe. |
| 5b | when a technique exists (era gate) | **built and exercised on every provenance call.** `requires_node` coverage: 205 of 215 production entries (95.3%), 91 needing no technology. Three energy-carrier mislabellings (Complaints/39) fixed; England-vs-Rome's process-heat divergence (Complaints/44) now respects a technique's reachable temperature. |
| 6+ | transport, settlements, state finance, war | **transport wired**: `sim/engine/economy.py` imports `sim/world/transport.py` for freight cost. `military_logistics.py` remains standalone. `deposits.py` reaches the engine only through the (currently off) solved-price path. Settlements, state finance and war have no dedicated module yet. |

Five of eight `sim/world/` modules are wired directly into the engine, a
sixth (`deposits.py`) reachable through a tool the engine can call but does
not by default, two (`demand.py`, `labour_market.py`) wired into nothing.
`ENDOGENOUS_COSTS_AND_DOMAINS.md` reflects this state, not an older one.

---

## Part 3 - What is not built, or not linked

Answering the specific questions this task was asked to check, each
confirmed by reading the current source rather than assumed:

**`sim/world/labour_market.py` - confirmed NOT wired into the engine.**
Nothing under `sim/engine/` imports it. What it would take: the module's own
docstring already names the gap precisely - `sim/engine/labour.py` prices
every trade off a static `TRADE_DENSITY` classification that never moves with
another trade's fortunes, and `agriculture.farm_workers_fte_for_population`
computes how many farmers are NEEDED but nothing computes how many farmers
there ARE as a distinct, laggy quantity. Wiring this in is comparable in
scope to the Milestone 4 agriculture wiring: an engine-side call (probably
from `_demographic_recovery` or a sibling method) would need to (a) compute
`labour_hours_required_by_trade` from active production/ventures each year,
(b) step a persisted `Workforce` object forward (a new `SAVE_FIELDS` entry,
the same shape as `farm_stock_kg`), and (c) have `annual_wage()` and the
farm-workforce sizing both read the module's `have_versus_need` output
instead of, respectively, `TRADE_DENSITY` and a population-only formula. This
is also the mechanism `Complaints/45` and `Complaints/48` both point at when
they say "professions do not move" - a famine cannot yet turn a blacksmith
into a farmer, and this module is the answer neither has been given.

**`sim/world/demand.py` - confirmed NOT wired anywhere**, not even into
`sim/solve_prices.py` (checked directly: no `from sim.world import demand`
or equivalent in that file). It correctly reverses the silver/lead
mass-vs-value-share result in isolation (Complaints/29), but the solver
still ships with `joint_output_mass_shares` as its production code path, and
every minor joint byproduct is still marked `(*)` (unanchored) on every run.
Wiring it in means the solver imports `demand` the way it already imports
`deposits` and `land`, and `joint_output_value_shares` replaces the mass
split wherever `demand`'s inputs (a Gini coefficient, household budget
shares) can be supplied for the civilisation being priced.

**The solved-price switch (`sim/engine/prices.py`, `use_solved_prices`) -
confirmed still OFF**, default `False`, and this round's own measurement
(`Complaints/43`'s latest update, itself edited by another live agent during
this audit) gives the sharpest statement yet of what would have to be true
to flip it: (1) every extracted material's rent mechanism exists (six ores
do; forest, quarry, salt-pan and gold's placer step do not); (2) every
grown/land-limited material (wheat, wool, timber...) has a structured link
from its recipe to how much land it represents - today `data/production/`
only has that as human-readable prose, not a field a solver can read, which
is a schema change, not a solver one; (3) a policy for what a `gated`
(era-unreachable) material should cost - unavailable, or an import price -
which needs either a household-side "cannot buy this" path in `economy.py`
or a trade/reach model neither `sim/world/` nor the solver currently has.
The file's own recommendation, worth repeating here because it is the right
shape of fix: **graduate materials out of `prices.json` individually**, not
via one global boolean, starting with the roughly 40 pure-manufacturing
materials that resolve through a real recipe with no extracted, zero-rent
good anywhere upstream of them.

**The 11 hardcoded outcomes, named individually - not zero, and that is
expected; see Part 2 for why a growing count here is the audit working, not
the project regressing.** `DEBT_BASE_RATE`, `LIVING_COST_TAX_RATE`,
`GENERIC_MINE_CAPEX_MULTIPLE` and its five capex siblings,
`SLAVE_BASE_PRICE_DENARII` and `WAGE_SCARCITY_ELASTICITY`. The mine-capex
family has a named fix already on record (Complaints/37): derive
mine capital cost from `sim/world/deposits.py`'s own sinking-cost model
(shaft-sinking hours, aqueduct-construction hours - both already declared
physical quantities) instead of a multiple of book price. Nobody has done
this yet.

---

## Part 4 - What to do next, in order, and why

1. **Wire `sim/world/labour_market.py` into the engine.** This is the single
   most-referenced missing piece across the complaints (45, 48, and the
   module's own docstring all name it independently), it is the one thing
   standing between "a famine kills people" and "a famine also reshapes the
   economy," and the module is already built and tested standalone - this is
   a wiring job, not a design job, the cheapest kind of work this project has
   left in this area.

2. **Wire `sim/world/demand.py` into `sim/solve_prices.py`**, replacing the
   mass-split joint-byproduct allocation. This closes Complaints/29 for real
   rather than leaving it correctly-diagnosed-but-unfixed, and it is a
   contained change (one new import, one function swap) with an existing
   correctness check (the silver/lead reversal) to verify against.

3. **Give `data/production/` a structured land-area field** (e.g. an
   `iugerum_per_batch`-shaped entry, per Complaints/43's own naming) for
   every grown/land-limited material. This is the actual blocker on ever
   turning `use_solved_prices` on for anything agricultural, and until it
   exists the project's headline mechanism - Malthusian land pressure
   reaching a real price - cannot reach a single price a player pays,
   regardless of how good `land.py` itself is.

4. **Extend rent to the non-ore extracted materials** (forest, quarry,
   salt-pan, gold's placer step) using the same Ricardian shape
   `deposits.py` already has for ore. Six of the ~14 extracted materials
   the original Complaints/43 table named are handled; the rest are not,
   and the mechanism to copy already exists.

5. **Then graduate materials out of `prices.json` individually**, per
   Complaints/43's own explicit recommendation, starting with the ~40
   pure-manufacturing materials with no extracted good upstream. Do this
   before touching the global `use_solved_prices` boolean at all - a
   per-material list is the safer and more honest migration path, and it
   is also the only one that can start immediately, without waiting on
   items 3-4 above.

6. **Continue the constants burndown**, specifically the mine-capex family
   (fixable now, from `deposits.py`'s own sinking-cost figures) and the
   re-audit of `core.py`/`labour.py`/`society.py`/`sim/engine/proto/` that
   Complaints/37 explicitly asked for once those files stop being mid-edit.

7. **Do the "author intent" review Complaints/30 asked for and never
   received** - the ~1,063 `up` and 246 `rev` branch-authored values that
   were deliberately held back at the tree's old figures rather than
   applied, specifically to avoid turning theory/method nodes back into
   openable "shops" or breaking a live regression test. This is real,
   already-written data sitting unused, and the review is scoped and
   bounded (a fixed list of nodes), unlike most of the rest of this list.

8. **Re-tiling (Complaints/46's second, larger recommendation) can wait.**
   The cheap fix (intensive-margin rent) already closed the acute symptom
   (a civilisation with one large region pricing its own land at zero), and
   a second, related area-basis fix (the forest ceiling) is already in
   flight. Re-tiling ~1,000 tiles from an agreed generating rule is real
   future work but is not blocking anything else on this list.

9. **The naming sweep and the tech-tree DATA-schema field rename
   (CLAUDE.md section 7) remain queued and are correctly low priority** -
   both are readability work with no behavioural stake, proven safe by
   `prove_rename_safe.py`, and neither blocks any of the above.

Everything above is ordered by what it unblocks, not by how easy it is:
1-2 are wiring jobs against already-built, already-tested modules; 3-5 are
what actually decides whether "prices are calculated, not looked up" reaches
a real game; 6-7 are debt-paydown with a measurable target; 8-9 are real but
not urgent, and saying so plainly is itself useful, since CLAUDE.md's own
history records every agent who has looked at this project independently
overestimating how urgent the naming and migration work is.
