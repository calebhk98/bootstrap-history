# Catalogue of modules, views and commands

**Status:** draft, task 1.5 of `MODULE_MIGRATION_TASKS.md`. A design input for `MODULE_REGISTRY_PLAN.md` section 4: modules read each other only through named views and write only through commands to the owner of a fact. Changes no code. Analysis done at `e8b004c`, the head of `sim-module-registry-plan` (the plan's own numbers were taken at `0be2f72`; Appendix B reproduces there as 906 read-only, 640 writer and 13 pure references, and at this head as well).

This directory has one file per proposed module (`<module>.md`), `core.md` (what `Sim` keeps and what dissolves) and `caches_and_ports.md` (every cache, port object and invalidation point found, feeding task 1.2). The numbers below were produced by the static analysis in "How the numbers were made"; nothing was run in a game. Tables were generated from one description of the catalogue and then edited by hand; the whole of `ledger`, `living_stock`, `projects` and this file were read after generation, the others were spot-checked. CLAUDE.md asks that every number carry the command that produced it: the ones here come from one-off analysis scripts kept outside the repository (the task forbade committing them), so no committed command reproduces them. Where a plain `grep` gives a figure, the command is beside it. Re-measure before acting on any count.

## Summary

- **28 modules** proposed from the 124 mixin classes plus the `Sim` body, the `ForwardingPropertiesMixin` aliases and the walled packages' handles. **141 views and 105 commands.**
- Under this grouping there are **1048 references across modules** (the plan's 1559 counted every class pair, including classes that now sit in one module), to **292 distinct methods and properties**: 149 that Appendix B classes read-only or pure and 143 it classes as writers. A further 79 references go to or from the composition root (`Sim`'s own state, year, caches). The walled packages add **237 handle members** used from outside (`labour` 106, `geography` 27, `economy` 51, `goods_market` 25, `actors` 24, `world_map` 2, `stores` 2), all mapped to views or commands here, and the engine reads and writes owned state fields directly (111 distinct fields read and 84 written across module boundaries; 574 read sites and 176 write sites in mixin code, 585 and 75 more in `sim/ui`, `sim/agents`, function modules and the like).
- **Appendix B overstates the writers.** `ActorsMixin.actors` and `edge` create `state.actors` on first read, so every caller of either counts as a writer. Treating those two as lazy initialisation, the plan's 1559 class-pair references split 1174 read-only, 372 writers, 13 pure instead of 906, 640, 13. Of the 143 distinct cross-module methods the plan counts as writers, 98 are published here as views (reads in disguise) and 45 as commands; but 61 of those views still write somewhere below them after the correction, from a short list of root causes ("Reads that write" below).
- **Views per old thing.** 141 views against 149 distinct read-only methods referenced across modules is 0.95, which on its own would trip the plan's stop criterion. It is the wrong denominator: those views also replace 237 package handle members and 111 owned fields that the method count leaves out. Against every name another module or outside caller uses (840), the ratio is 0.17, about 6.0 old names behind each view. The stricter test (a view replacing exactly one referenced method and no field) finds **20 of 141 views, 14%**; 10 modules are at or above 20% (list under "Flags"); most have only three to eight views, so one view moves the percentage a lot.

- **Flagged problems.** (1) 14 of 28 modules exceed the 15-reads limit, including two of the three prototype domains (`projects` 42, `living_stock` 29; `ledger` reads 1). (2) Module-level reads form one cycle of 26 modules; the view-level graph is acyclic. Real data cycles to prove: `prices`<->`production`, `materials`<->`resources`, `projects`<->`ventures`<->`production`. (3) 26 views are under the three-caller floor. (4) 10 modules have a one-to-one share of at least 20% and 3 have at least 0.4 views per used name (`demography`, `ledger`, `prices`). (5) 61 methods published as views still write below them, from 22 root causes, mostly first-read creation (see "Reads that write"). (6) by direct writes into other modules' fields (mixin code), `hazards` touches 8 modules (14 fields); `projects` touches 7 modules (13 fields); `polity` touches 5 modules (10 fields); `finance` touches 5 modules (9 fields): every one of those writes becomes a command. `hazards` is the widest writer into other modules; by kinds of command sent, `projects` sends 18, `finance` 18 and `hazards` 12. (7) The stop criterion as worded cannot be applied with the plan's denominator (the method count omits handle members and fields).
## Conventions in these files

- **Names are proposals, sites are measured.** View names, command names, channel names and refusal causes are this draft's proposals. File and line citations, counts of callers and the lists of old methods are measured from the code at `e8b004c`.
- **Kinds.** `table` is one whole value, `keyed` one value per key computed on first read of the key, `quote` a question with arguments that is never cached (`sim/assembly/spec.py`). `Seat` yes means the value is the acting seat's (`seat_scoped`); a seat-scoped view must also answer for a country seat, which has no household or founder.
- **Replaces.** The old methods and properties (`self.<name>` on `Sim`), package handle members (`labour.hire`, `geography.api`, `goods_market.quote`), and owned state fields that other code reads directly. A name appears under exactly one view or command.
- **Callers today** is the number of distinct caller modules (mixin code) plus caller areas (`<ui>`, `<agents>`, `<engine-functions>`, `<mods>`, ...) of what the view replaces, from the same scans. A view under three, unless a quote, is listed in the flags.
- **Direct field access is the larger coupling.** The method scan alone finds 1048 cross-module references; the field and handle scans find 1884 more read sites and 251 write sites. A catalogue built from methods alone would have missed most of what the migration changes.
- **Modules own state in slots.** `Proposed slot` names the world dataclass and per-seat dataclass the module would register (task 1.3); the field tables give today's path.

## The modules

| # | Module | What it owns | Views | Commands | Old methods owned | Referenced from other modules |
|---|---|---|---|---|---|---|
| 1 | [`actors`](actors.md) | The cast of other actors: governments and firms, their records and registry, and the agents package's world adapters. | 3 | 2 | 11 | 5 |
| 2 | [`agriculture`](agriculture.md) | Farming: farmland, farm weather, soil nitrogen, wild stock and food potential. **Moved in part** (`sim/agriculture/`; the farm holding waits for demography and workforce). | 10 | 2 | 22 | 4 |
| 3 | [`campaigns`](campaigns.md) | Armies, campaigns, conquest, captives and revolts. Moved: 1 view, 4 commands, sends 14 (see the file). | 1 | 4 | 46 | 0 |
| 4 | [`coin`](coin.md) | Coin as a metal: stock and price level, revaluation, keeping, carriage and theft. **Moved** (`sim/coin/`). | 13 | 4 | 29 | 11 |
| 5 | [`demography`](demography.md) | Population: counts by age, by tile, urban share, food eaten, recovery after shocks. | 4 | 4 | 19 | 5 |
| 6 | [`diffusion`](diffusion.md) | How knowledge spreads: literacy, schooling, diffusion indices, disclosure and licensing, tech effects on society. | 5 | 4 | 48 | 12 |
| 7 | [`disease`](disease.md) | Epidemics and endemic disease: the disease package, burden, forecasts and medical coverage. | 3 | 2 | 17 | 9 |
| 8 | [`finance`](finance.md) | Debt: credit limits, interest, arrears, insolvency, bondage and the capital market. | 7 | 7 | 50 | 7 |
| 9 | [`foreign_trade`](foreign_trade.md) | Trade with partner countries: their economies, supply, payments in coin, lift capacity, actors' trade books. | 4 | 5 | 40 | 13 |
| 10 | [`freight`](freight.md) | Carriage of goods at home and abroad: carriers and their costs, routes, what merchants add, route dues. **Moved** (`sim/freight/`). | 15 | 1 | 50 | 10 |
| 11 | [`hazards`](hazards.md) | Disasters and shocks: random events, dated shocks, world hazards, famine watch, relief and the output factor. | 4 | 2 | 52 | 7 |
| 12 | [`knowledge`](knowledge.md) | What each seat knows and can see: techniques held, forgotten, revealed (fog), and the tree itself. | 3 | 3 | 19 | 8 |
| 13 | [`land`](land.md) | Land and the map: tile ownership, claims, roads and ports, works, colonies, and the geography package. | 7 | 4 | 37 | 12 |
| 14 | [`ledger`](ledger.md) | Money and goods balances: the one writer of what an actor holds. | 5 | 10 | 10 | 9 |
| 15 | [`living_stock`](living_stock.md) | Herds and defence stores: holding, growing, buying, smuggling and drawing animals and arms. | 4 | 5 | 45 | 7 |
| 16 | [`markets`](markets.md) | Orders and market outcomes: goods market quotes, clearing, household demand, goods-category factors, the agent economy record. | 8 | 5 | 33 | 5 |
| 17 | [`materials`](materials.md) | Material supply and demand, the resource throttle, electricity and the materials a project consumes. | 6 | 1 | 63 | 22 |
| 18 | [`mechanics`](mechanics.md) | What the tree's effects add up to: an index over tech-tree mechanics and effect lookups. **Moved** (`sim/mechanics/`). | 22 | 0 | 32 | 24 |
| 19 | [`polity`](polity.md) | The state and the household's standing with it: reputation, scandal, eminence, protection, levies, reach, interest groups. | 7 | 4 | 58 | 13 |
| 20 | [`prices`](prices.md) | Calculated prices: the material price table, cost books, entry cost ratios. | 4 | 0 | 15 | 5 |
| 21 | [`production`](production.md) | What runs: operating techniques and capability, revenue and upkeep of concerns, industry experience, techniques in use. | 7 | 4 | 74 | 31 |
| 22 | [`projects`](projects.md) | The lifecycle of a project: can it start, what it costs, progress, completion and failure. | 8 | 7 | 96 | 15 |
| 23 | [`reporting`](reporting.md) | Moved: the seat's log, the automation audit trail and the real-output and price-ratio indicators. The warn-once notes are not here (reporting.md says where they go). | 8 | 6 | 21 | 5 |
| 24 | [`resources`](resources.md) | Extractive resources: mines, deposits, prospecting, forest and nitre beds. | 5 | 4 | 63 | 14 |
| 25 | [`seats`](seats.md) | Seats and the acting context: who plays, goals and win conditions, the founder's life, dealings between seats. | 6 | 6 | 42 | 8 |
| 26 | [`stores`](stores.md) | Mod-declared key/value stores (`state.stores`). | 1 | 1 | 1 | 1 |
| 27 | [`ventures`](ventures.md) | Concerns the seat opens and closes: crews, foremen, staffing closures, quotes and auto-opening. | 4 | 3 | 59 | 19 |
| 28 | [`workforce`](workforce.md) | People who work: staff by trade, hours, wages, training, slaves and the labour market. | 11 | 8 | 58 | 11 |

The remaining 31 methods and properties belong to the composition root and are described in [`core.md`](core.md). Existing walled packages and where they land: `sim/labour` becomes `workforce` (its `Labour` is a thirteen-class composite behind `LabourPortMixin`, 106 members used from outside); `sim/geography` becomes `land`, with its food and deposit queries split to `agriculture`, `resources` and `living_stock`; `sim/economy` becomes `markets` (51 members used from outside), with credit to `finance`, coin to `coin`, labour to `workforce`; `sim/agents` becomes `actors` plus the actor-side halves of `polity`, `finance`, `ledger` and `campaigns`; `sim/disease` becomes `disease`; `sim/ui` is a reader of views and a sender of commands, not a module. `sim/book.py` and `sim/contracts.py` (the shared money book and debt registry) become the inside of `ledger` and `finance`.

## Where each of the 124 mixin classes goes

A class split across modules is listed with the number of its methods each module takes. `ForwardingPropertiesMixin` is split by the field each alias names; it disappears (see `core.md`).

| Class | File | Module (methods) |
|---|---|---|
| `ModStoresMixin` | `sim/engine/mod_stores.py` | `stores` (1) |
| `RealPriceRatiosMixin` | `sim/engine/real_price_ratios.py` | `reporting` (5) |
| `CoinRevaluationMixin` | `sim/engine/coin_revaluation.py` | `coin` (4) |
| `MechanicsMixin` | `sim/engine/mechanics.py` | `mechanics` (32), `production` (1) |
| `EconomyMixin` | `sim/engine/economy.py` | `core` (8), `projects` (6), `knowledge` (1) |
| `GoodsMixin` | `sim/engine/economy_goods.py` | `markets` (9), `workforce` (3), `agriculture` (2) |
| `MaterialSupplyMixin` | `sim/engine/economy_materials.py` | `materials` (20), `ledger` (4), `prices` (3), `markets` (3), `core` (2), `production` (1) |
| `MaterialReachMixin` | `sim/engine/material_reach.py` | `materials` (4) |
| `ElectricityMixin` | `sim/engine/economy_electricity.py` | `materials` (13) |
| `FreightMixin` | `sim/engine/economy_freight.py` | `materials` (7), `freight` (6), `resources` (4) |
| `MiningMixin` | `sim/engine/economy_mining.py` | `resources` (40), `land` (1) |
| `MineDepositsMixin` | `sim/engine/mine_deposits.py` | `resources` (15) |
| `CreditMixin` | `sim/engine/economy_credit.py` | `finance` (17), `workforce` (3), `projects` (1) |
| `HouseholdBillMixin` | `sim/engine/economy_household_bill.py` | `workforce` (3) |
| `DebtServiceMixin` | `sim/engine/economy_debt_service.py` | `finance` (7) |
| `CapitalMarketMixin` | `sim/engine/economy_capital_market.py` | `finance` (9) |
| `InterestMixin` | `sim/engine/economy_interest.py` | `finance` (4) |
| `MarketAbsorptionMixin` | `sim/engine/economy_absorption.py` | `markets` (1) |
| `ProjectCostTailMixin` | `sim/engine/projects_cost_tail.py` | `projects` (1) |
| `ProductionMixin` | `sim/engine/economy_production.py` | `production` (23), `polity` (3), `workforce` (1) |
| `ProjectMaterialsMixin` | `sim/engine/project_materials.py` | `materials` (15) |
| `ViewShareMixin` | `sim/engine/view_share.py` | `core` (7) |
| `MarketClearingMixin` | `sim/engine/market_clearing.py` | `markets` (10) |
| `ForeignEconomiesMixin` | `sim/engine/foreign_economies.py` | `foreign_trade` (9) |
| `ForeignRoutesMixin` | `sim/engine/foreign_routes.py` | `freight` (17) |
| `DomesticHaulMixin` | `sim/engine/domestic_haul.py` | `freight` (9) |
| `ForeignCapacityMixin` | `sim/engine/foreign_capacity.py` | `foreign_trade` (6) |
| `ForeignPaymentsMixin` | `sim/engine/foreign_payments.py` | `foreign_trade` (8), `coin` (6) |
| `ForeignTradersMixin` | `sim/engine/foreign_traders.py` | `freight` (14) |
| `ForeignActorTradeMixin` | `sim/engine/foreign_actor_trade.py` | `foreign_trade` (10) |
| `TraderCargoMixin` | `sim/engine/trader_cargo.py` | `foreign_trade` (7) |
| `MarketDemandMixin` | `sim/engine/market_demand.py` | `markets` (8) |
| `StaticBookBasketMixin` | `sim/engine/static_book_basket.py` | `markets` (1) |
| `RealOutputMixin` | `sim/engine/real_output.py` | `reporting` (7) |
| `ConcernVolumeMixin` | `sim/engine/concern_volume.py` | `production` (5) |
| `ConcernBookSalesMixin` | `sim/engine/concern_book_sales.py` | `production` (4) |
| `TechniquesInUseMixin` | `sim/engine/techniques_in_use.py` | `production` (4) |
| `IndustryDepthMixin` | `sim/engine/industry_depth.py` | `production` (18) |
| `IndustryConcernMixin` | `sim/engine/industry_concern.py` | `production` (4) |
| `IncumbentPricesMixin` | `sim/engine/incumbent_prices.py` | `prices` (4) |
| `ProducerCostsMixin` | `sim/engine/producer_costs.py` | `prices` (8) |
| `FogMixin` | `sim/engine/fog.py` | `knowledge` (10), `hazards` (2) |
| `GeographyPortMixin` | `sim/engine/geography_port.py` | `land` (2) |
| `DiseasePortMixin` | `sim/engine/disease_port.py` | `disease` (8) |
| `LabourPortMixin` | `sim/engine/labour_port.py` | `workforce` (1) |
| `ProjectsMixin` | `sim/engine/projects.py` | `projects` (0) |
| `BlockersMixin` | `sim/engine/blockers.py` | `projects` (6) |
| `CapabilityMixin` | `sim/engine/projects_capability.py` | `production` (7) |
| `VenturesMixin` | `sim/engine/projects_ventures.py` | `ventures` (16) |
| `RunningGatesMixin` | `sim/engine/projects_running_gates.py` | `projects` (8) |
| `StaffingMixin` | `sim/engine/projects_staffing.py` | `ventures` (21) |
| `StaffingShortfallMixin` | `sim/engine/projects_staffing_shortfall.py` | `ventures` (7) |
| `StaffingReportMixin` | `sim/engine/projects_staffing_report.py` | `ventures` (6) |
| `OpenGateMixin` | `sim/engine/projects_open_gate.py` | `projects` (2) |
| `AllocationNotesMixin` | `sim/engine/allocation_notes.py` | `workforce` (3) |
| `VentureQuotesMixin` | `sim/engine/projects_venture_quotes.py` | `ventures` (7) |
| `HourQueueMixin` | `sim/engine/projects_hour_queue.py` | `workforce` (3) |
| `StartingMixin` | `sim/engine/projects_starting.py` | `projects` (33) |
| `ExclusionsMixin` | `sim/engine/projects_exclusions.py` | `projects` (2) |
| `ProgressMixin` | `sim/engine/projects_progress.py` | `workforce` (10), `projects` (8) |
| `CompletionMixin` | `sim/engine/projects_completion.py` | `projects` (9) |
| `RebuildMixin` | `sim/engine/projects_rebuild.py` | `projects` (6) |
| `SeatMixin` | `sim/engine/core_seats.py` | `core` (5), `seats` (2) |
| `SeatRunMixin` | `sim/engine/seat_run.py` | `seats` (11) |
| `SeatHandoverMixin` | `sim/engine/seat_handover.py` | `seats` (1) |
| `SeatBuildsMixin` | `sim/engine/seat_builds.py` | `seats` (2) |
| `SeatSightMixin` | `sim/engine/seat_sight.py` | `seats` (2) |
| `ShockYearMixin` | `sim/engine/shock_year.py` | `hazards` (11) |
| `WaysMixin` | `sim/engine/ways.py` | `land` (8) |
| `WorksMixin` | `sim/engine/works.py` | `land` (7) |
| `HeldWorksMixin` | `sim/engine/held_works.py` | `land` (3) |
| `SocietyMixin` | `sim/engine/society.py` | `polity` (0) |
| `HazardReliefMixin` | `sim/engine/hazard_relief.py` | `hazards` (12) |
| `HazardsMixin` | `sim/engine/society_hazards.py` | `hazards` (21) |
| `StatePressureMixin` | `sim/engine/society_state_pressure.py` | `polity` (22) |
| `AdoptionMixin` | `sim/engine/society_adoption.py` | `diffusion` (15) |
| `DiffusionMixin` | `sim/engine/society_diffusion.py` | `diffusion` (22) |
| `ActorsMixin` | `sim/engine/society_actors.py` | `actors` (11), `diffusion` (4), `ledger` (4), `polity` (4) |
| `DisclosureMixin` | `sim/engine/society_disclosure.py` | `diffusion` (7) |
| `FounderSalesMixin` | `sim/engine/founder_sales.py` | `production` (3), `agriculture` (1) |
| `SeatDealingsMixin` | `sim/engine/seat_dealings.py` | `seats` (7) |
| `SeatBankMixin` | `sim/engine/seat_bank.py` | `finance` (1) |
| `InterestGroupsMixin` | `sim/engine/interest_groups.py` | `polity` (7) |
| `BenefactionsMixin` | `sim/engine/benefactions.py` | `polity` (0) |
| `TransfersMixin` | `sim/engine/transfers.py` | `polity` (6) |
| `ConcernLevyMixin` | `sim/engine/concern_levy.py` | `polity` (2) |
| `CoverageMixin` | `sim/engine/coverage.py` | `disease` (8) |
| `FoodReliefMixin` | `sim/engine/food_relief.py` | `living_stock` (2) |
| `LegitimacyMixin` | `sim/engine/legitimacy.py` | `polity` (7) |
| `WorkingDayMixin` | `sim/engine/working_day.py` | `workforce` (2) |
| `ColoniesMixin` | `sim/engine/colonies.py` | `land` (7) |
| `TileOwnershipMixin` | `sim/engine/tile_ownership.py` | `land` (9) |
| `WorldHazardsMixin` | `sim/engine/world_hazards.py` | `hazards` (3) |
| `RouteDuesMixin` | `sim/engine/route_dues.py` | `freight` (4) |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | `workforce` (46), `reporting` (16), `seats` (16), `knowledge` (14), `finance` (12), `polity` (12), `projects` (10), `materials` (8), `resources` (8), `demography` (6), `ledger` (4), `agriculture` (4), `ventures` (3), `production` (2), `hazards` (2), `core` (2) |
| `GoalsMixin` | `sim/engine/goals.py` | `seats` (4) |
| `StepPhasesMixin` | `sim/engine/core_step_phases.py` | `workforce` (4), `core` (3), `finance` (3), `seats` (2), `reporting` (1), `hazards` (1), `polity` (1) |
| `StaffPhaseMixin` | `sim/engine/step_phase_staff.py` | `workforce` (1) |
| `MoneyPhaseMixin` | `sim/engine/step_phase_money.py` | `finance` (3), `seats` (1) |
| `ProjectStartPhaseMixin` | `sim/engine/step_phase_project_start.py` | `projects` (2) |
| `ProjectProgressPhaseMixin` | `sim/engine/step_phase_projects.py` | `projects` (7) |
| `LivingStockMixin` | `sim/engine/living_stock.py` | `living_stock` (8) |
| `LivingStockOpeningMixin` | `sim/engine/living_stock_opening.py` | `living_stock` (4) |
| `CoinHoardMixin` | `sim/engine/coin_hoard.py` | `coin` (8) |
| `CoinCarriageMixin` | `sim/engine/coin_carriage.py` | `coin` (4) |
| `TheftChargeMixin` | `sim/engine/theft_charge.py` | `coin` (5) |
| `HoldingsExposureMixin` | `sim/engine/holdings_exposure.py` | `coin` (2) |
| `LivingStockTradeMixin` | `sim/engine/living_stock_trade.py` | `living_stock` (4) |
| `LivingStockSmugglingMixin` | `sim/engine/living_stock_smuggling.py` | `living_stock` (9) |
| `LivingStockYearlyMixin` | `sim/engine/living_stock_yearly.py` | `living_stock` (4) |
| `LivingStockGrowthMixin` | `sim/engine/living_stock_growth.py` | `living_stock` (6) |
| `FoodSupplyMixin` | `sim/engine/food_supply.py` | `agriculture` (4) |
| `SoilNitrogenMixin` | `sim/engine/soil_nitrogen_year.py` | `agriculture` (5) |
| `FoodEatenMixin` | `sim/engine/food_eaten.py` | `demography` (2) |
| `DemographicRecoveryMixin` | `sim/engine/demographic_recovery.py` | `demography` (1) |
| `RegionalPeopleMixin` | `sim/engine/regional_people.py` | `demography` (4) |
| `UrbanShareMixin` | `sim/engine/urban_share.py` | `demography` (5) |
| `DefenceStoresMixin` | `sim/engine/defence_stores.py` | `living_stock` (8) |
| `CampaignActorsMixin` | `sim/engine/campaign_actors.py` | `campaigns` (17) |
| `CampaignYearMixin` | `sim/engine/campaign_year.py` | `campaigns` (18) |
| `RevoltYearMixin` | `sim/engine/revolt_year.py` | `campaigns` (8) |
| `CaptivesMixin` | `sim/engine/captives.py` | `campaigns` (3) |
| `EconomyPortMixin` | `sim/engine/economy_port.py` | `markets` (1) |
| `NodeRederiveMixin` | `sim/engine/node_rederive.py` | `production` (3) |

## Dependency matrix

Each cell is the number of distinct views of the column module that the row module reads, from method references, field accesses, package handle members and the inputs of its own derived views. Read the row as "module reads these". Column numbers are the module numbers in the table above. Commands are in the second matrix.

```
                1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28  total  providers
actors          .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  2  1  .  .  .  .  .  .  .  .  .  .  .      4      3
agriculture     .  .  .  .  .  .  .  .  .  .  .  .  2  1  1  .  .  .  .  1  .  .  .  .  .  .  .  2      7      5
campaigns       1  .  .  .  2  .  .  .  .  .  .  .  4  .  .  .  .  .  1  .  .  .  .  .  .  1  .  .      9      5
coin            1  2  .  .  .  .  .  2  2  1  .  .  2  3  .  3  .  .  3  1  .  .  1  1  .  .  .  3     25     13
demography      .  2  .  .  .  .  1  .  .  .  .  .  3  .  1  .  .  .  .  .  .  .  1  .  .  .  .  2     10      6
diffusion       1  .  .  .  1  .  2  .  .  .  .  1  .  .  1  .  .  5  3  .  1  1  1  .  2  .  .  4     23     12
disease         .  .  .  .  2  .  .  .  .  .  .  1  1  .  .  .  .  2  .  .  2  .  1  .  1  .  .  1     11      8
finance         1  .  .  .  .  .  .  .  .  .  1  .  .  2  .  1  .  3  2  .  3  2  1  3  2  .  1  7     29     13
foreign_trade   1  .  .  2  .  .  .  1  .  3  .  1  2  1  .  4  2  .  .  1  .  .  .  1  1  .  .  .     20     12
freight         1  .  .  .  .  .  .  1  2  .  .  .  3  .  .  1  .  .  .  2  .  .  .  .  1  .  .  4     15      8
hazards         .  .  .  .  .  2  1  .  .  .  .  2  .  1  1  .  .  4  2  .  1  3  1  1  3  .  1  2     25     14
knowledge       .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  3  .  .  1  .  .  .      4      2
land            .  .  .  .  .  .  2  1  1  .  .  1  .  .  .  1  1  1  .  .  1  1  1  .  .  1  .  2     14     12
ledger          .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      1      1
living_stock    1  2  .  1  .  .  .  .  2  2  .  1  2  3  .  3  1  2  2  .  2  .  .  .  1  .  1  3     29     16
markets         1  .  .  .  1  .  .  .  .  .  1  1  1  2  .  .  2  1  .  3  3  .  1  .  1  .  .  2     20     13
materials       .  .  .  .  1  1  .  .  1  .  .  2  1  2  .  2  .  2  .  1  1  3  .  4  .  .  .  .     21     12
mechanics       .  .  .  .  .  .  .  .  .  .  .  2  .  .  .  .  .  .  .  .  2  .  .  .  1  .  .  2      7      4
polity          1  .  .  1  1  .  .  .  .  .  1  1  .  2  .  1  1  3  .  .  2  1  2  .  3  .  .  5     25     14
prices          .  .  .  .  .  .  .  1  .  .  .  1  .  .  .  3  2  .  .  .  4  .  .  .  .  .  .  3     14      6
production      2  .  .  1  1  1  1  1  .  .  1  1  1  1  .  4  1  3  1  3  .  1  1  .  2  .  2  7     36     20
projects        .  .  .  .  .  1  .  3  .  .  2  2  2  1  2  .  4  4  1  .  4  .  1  3  2  .  3  7     42     16
reporting       .  .  .  1  1  .  .  .  .  .  .  .  .  .  .  4  .  .  .  1  .  .  .  .  .  .  .  3     10      5
resources       .  1  .  .  .  .  .  .  .  .  .  1  1  2  .  .  4  2  1  2  2  .  1  .  .  .  .  3     20     11
seats           1  .  .  .  .  2  .  .  .  .  1  2  .  .  .  .  1  2  1  .  2  1  1  .  .  .  .  1     15     11
stores          .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      0      0
ventures        .  .  .  .  .  1  .  2  .  .  .  2  .  1  1  .  .  1  .  1  6  3  1  .  1  .  .  4     24     12
workforce       .  .  .  .  1  1  1  1  .  .  .  1  .  1  .  2  1  2  .  .  3  2  1  1  1  .  1  .     20     15
```

Commands sent (distinct command classes of the column module that the row module sends):

```
                1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28  total
actors          .  .  .  2  .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .      4
agriculture     .  .  .  .  .  .  .  .  .  .  .  .  .  2  .  .  .  .  .  .  .  .  .  .  .  .  .  .      2
campaigns       .  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      1
coin            .  1  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  .  .  .      2
demography      .  1  .  .  .  .  1  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  1  .  .  .  .  1      5
diffusion       .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  1  .  .  .  .  2      4
disease         .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  1  2      5
finance         1  .  .  2  1  1  .  .  .  .  1  .  .  3  .  .  .  .  1  .  .  1  1  1  .  .  2  3     18
foreign_trade   .  .  .  .  .  .  .  .  .  .  .  .  .  1  .  1  .  .  .  .  .  .  .  .  .  .  .  .      2
freight         .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      0
hazards         .  .  .  1  1  .  .  .  .  .  .  1  .  1  .  .  .  .  1  .  1  1  1  .  1  .  1  2     12
knowledge       .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      0
land            .  .  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  1  .  .  .  .  .      2
ledger          .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      1
living_stock    .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .      2
markets         .  .  .  1  1  .  .  .  1  .  .  .  1  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .      5
materials       .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  .  .  .      1
mechanics       .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      0
polity          .  .  .  .  .  .  .  .  .  .  1  1  .  2  .  1  .  .  .  .  .  .  2  .  .  .  .  2      9
prices          .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      0
production      .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  1      1
projects        .  .  .  .  .  1  .  .  .  .  .  2  .  2  2  .  1  .  2  .  .  .  1  3  1  .  1  2     18
reporting       .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      0
resources       .  .  .  .  .  .  .  .  .  .  .  .  .  2  .  .  .  .  .  .  .  .  1  .  .  .  .  .      3
seats           .  .  .  .  .  .  .  .  .  .  1  2  .  .  .  .  .  .  .  .  1  1  1  .  .  .  .  .      6
stores          .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .      0
ventures        .  .  .  .  .  .  .  .  .  .  .  1  .  1  .  .  .  .  .  .  .  1  1  .  .  .  .  .      4
workforce       .  .  .  .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  1  .  .  .  .  .      2
```

## Counts per module

`Used names` is every method, property, handle member or field alias of the module that another module's mixin code or code outside the mixins (`sim/ui`, `sim/agents`, ports, function modules, `sim/labour`, `sim/economy`, mods) uses. `Read-only referenced` is the number of distinct methods of the module that other modules' mixins reference and Appendix B classes as read-only or pure.

| Module | Views | Commands | Used names | Views per used name | Read-only methods referenced | One-to-one views | Views read | Providers read | Modules reading it | Modules sending to it |
|---|---|---|---|---|---|---|---|---|---|---|
| `actors` | 3 | 2 | 29 | 0.10 | 0 | 1 | 4 | 3 | 11 | 1 |
| `agriculture` | 5 | 2 | 24 | 0.21 | 3 | 1 | 7 | 5 | 4 | 2 |
| `campaigns` | 3 | 5 | 8 | 0.38 | 0 | 0 | 9 | 5 | 0 | 0 |
| `coin` (moved; views, commands and reads re-counted from the spec, the rest not re-measured) | 13 | 4 | 19 | 0.68 | 2 | - | 30 | - | 6 | 4 |
| `demography` | 4 | 4 | 8 | 0.50 | 3 | 0 | 10 | 6 | 9 | 3 |
| `diffusion` | 5 | 4 | 28 | 0.18 | 5 | 1 | 23 | 12 | 7 | 2 |
| `disease` | 3 | 2 | 12 | 0.25 | 8 | 0 | 11 | 8 | 6 | 1 |
| `finance` | 7 | 7 | 34 | 0.21 | 1 | 2 | 29 | 13 | 9 | 1 |
| `foreign_trade` | 4 | 5 | 28 | 0.14 | 4 | 0 | 20 | 12 | 6 | 3 |
| `freight` | 4 | 1 | 14 | 0.29 | 1 | 1 | 15 | 8 | 3 | 0 |
| `hazards` | 4 | 2 | 16 | 0.25 | 3 | 0 | 25 | 14 | 6 | 4 |
| `knowledge` | 3 | 3 | 16 | 0.19 | 7 | 0 | 4 | 2 | 17 | 5 |
| `land` | 7 | 4 | 33 | 0.21 | 11 | 1 | 14 | 12 | 13 | 3 |
| `ledger` | 5 | 10 | 11 | 0.45 | 2 | 0 | 1 | 1 | 14 | 11 |
| `living_stock` | 4 | 5 | 22 | 0.18 | 2 | 1 | 29 | 16 | 6 | 1 |
| `markets` | 8 | 5 | 83 | 0.10 | 4 | 1 | 20 | 13 | 13 | 3 |
| `materials` | 6 | 1 | 35 | 0.17 | 9 | 0 | 21 | 12 | 12 | 1 |
| `mechanics` | 5 | 0 | 26 | 0.19 | 24 | 0 | 7 | 4 | 15 | 0 |
| `polity` | 7 | 4 | 32 | 0.22 | 10 | 1 | 25 | 14 | 10 | 5 |
| `prices` | 4 | 0 | 7 | 0.57 | 1 | 3 | 14 | 6 | 10 | 0 |
| `production` | 7 | 4 | 47 | 0.15 | 14 | 0 | 36 | 20 | 16 | 3 |
| `projects` | 8 | 7 | 42 | 0.19 | 11 | 2 | 42 | 16 | 11 | 4 |
| `reporting` | 3 | 3 | 13 | 0.23 | 3 | 0 | 10 | 5 | 15 | 13 |
| `resources` | 5 | 4 | 35 | 0.14 | 6 | 0 | 20 | 11 | 7 | 2 |
| `seats` | 6 | 6 | 33 | 0.18 | 5 | 1 | 15 | 11 | 15 | 2 |
| `stores` | 1 | 1 | 3 | 0.33 | 1 | 1 | 0 | 0 | 2 | 0 |
| `ventures` | 4 | 3 | 33 | 0.12 | 7 | 1 | 24 | 12 | 6 | 4 |
| `workforce` | 11 | 8 | 149 | 0.07 | 8 | 2 | 20 | 15 | 20 | 8 |
| **All** | **141** | **105** | **840** | **0.17** | **149** | **20** | | | | |

## Ratio of views to old methods, and the plan's stop criterion

| Denominator | Count | Views per item |
|---|---|---|
| Distinct read-only (or pure) methods referenced across modules | 149 | 0.95 |
| All distinct methods referenced across modules (reads and writers) | 292 | 0.48 |
| Names used by other modules or by outside callers, package handle members included | 840 | 0.17 |
| Cross-module references (mixin code only) | 1048 | 0.13 |

Task 2.4 stops the plan if "a domain's catalogue comes out near one view per old method (more than 20% one-to-one)". By the strict test (a view that replaces exactly one cross-referenced method and no owned field) the whole catalogue is 20 of 141 (14%). Per module, with the modules at or above 20% marked:

| Module | Views | One-to-one | Share | Under the 3-caller floor |
|---|---|---|---|---|
| `actors` | 3 | 1 | 33% **flag** | - |
| `agriculture` | 5 | 1 | 20% **flag** | `wild_stock` |
| `campaigns` | 3 | 0 | 0% | `armies`, `campaign_sites`, `stability` |
| `coin` | 13 | - | - | - (not re-measured) |
| `demography` | 4 | 0 | 0% | `food_eaten`, `yearly_record` |
| `diffusion` | 5 | 1 | 20% **flag** | - |
| `disease` | 3 | 0 | 0% | - |
| `finance` | 7 | 2 | 29% **flag** | `debt_interest_rate` |
| `foreign_trade` | 4 | 0 | 0% | `actor_trade` |
| `freight` | 4 | 1 | 25% **flag** | `carrier_models`, `route_dues` |
| `hazards` | 4 | 0 | 0% | `hazard_relief` |
| `knowledge` | 3 | 0 | 0% | `tree` |
| `land` | 7 | 1 | 14% | `works`, `colonies` |
| `ledger` | 5 | 0 | 0% | `cash_book` |
| `living_stock` | 4 | 1 | 25% **flag** | `relief` |
| `markets` | 8 | 1 | 12% | `market_absorption` |
| `materials` | 6 | 0 | 0% | - |
| `mechanics` | 5 | 0 | 0% | - |
| `polity` | 7 | 1 | 14% | `state_account`, `interest_groups` |
| `prices` | 4 | 3 | 75% **flag** | `cost_ratios` |
| `production` | 7 | 0 | 0% | - |
| `projects` | 8 | 2 | 25% **flag** | `committed_cost` |
| `reporting` | 3 | 0 | 0% | `price_ratios` |
| `resources` | 5 | 0 | 0% | `mine_catalogue` |
| `seats` | 6 | 1 | 17% | `dealings` |
| `stores` | 1 | 1 | 100% **flag** | - |
| `ventures` | 4 | 1 | 25% **flag** | - |
| `workforce` | 11 | 2 | 18% | `trade_spread` |

## Flags

### Modules over the 15-declared-reads limit of task 2.4

14 of 28 modules read more than 15 views of other modules (views read / providers read): `projects` 42 / 16; `production` 36 / 20; `living_stock` 29 / 16; `finance` 29 / 13; `polity` 25 / 14; `hazards` 25 / 14; `coin` 25 / 13; `ventures` 24 / 12; `diffusion` 23 / 12; `materials` 21 / 12; `workforce` 20 / 15; `resources` 20 / 11; `markets` 20 / 13; `foreign_trade` 20 / 12.

The three prototype domains: `living_stock` reads 29 views from 16 providers, `projects` (the start-of-project check, the heavy reader of 2.3) reads 42 from 16, `ledger` reads 1. Counted by providers (modules read) instead of views, `living_stock` (16), `production` (20), `projects` (16) are above 15 and `workforce` at 15. The limit as worded trips 14 of 28 domains, so it and the view grain need to be settled together before the gate: either count modules read, or accept wider views for the heavy readers (a consumer that needs eleven facts about people should read one `staff` table, not eleven views), or give a derived view a declared bundle of inputs that counts once. This catalogue leaves the grain where the consumers' questions put it so the effect is visible.

### Views per old method close to one

Modules with at least 0.4 views per used name: `demography` (4 views for 8 names); `ledger` (5 views for 11 names); `prices` (4 views for 7 names). Each has few names behind it, so the count is small rather than the grouping wrong, but each is where a view could be a renamed method: `prices` publishes four views for seven names and three of them are one-to-one (`material_prices`, `material_price`, `cost_ratios` should probably be two); `demography` has `yearly_record` and `food_eaten` under the three-caller floor and should fold into `population`; `ledger`'s `balance` and `acting_balance` can be one keyed view whose default key is the acting seat; `campaigns` (0.38) and `stores` (0.33) are just under the line and have almost no callers outside themselves yet.

Modules with one-to-one share at or above 20%: `actors` 1 of 3; `agriculture` 1 of 5; `diffusion` 1 of 5; `finance` 2 of 7; `freight` 1 of 4; `living_stock` 1 of 4; `prices` 3 of 4; `projects` 2 of 8; `stores` 1 of 1; `ventures` 1 of 4.

### Views under the three-caller floor

26 views have fewer than three distinct callers today and are not quotes: `agriculture`: `wild_stock`; `campaigns`: `armies`, `campaign_sites`, `stability`; `coin`: `coin_metal`; `demography`: `food_eaten`, `yearly_record`; `finance`: `debt_interest_rate`; `foreign_trade`: `actor_trade`; `freight`: `carrier_models`, `route_dues`; `hazards`: `hazard_relief`; `knowledge`: `tree`; `land`: `works`, `colonies`; `ledger`: `cash_book`; `living_stock`: `relief`; `markets`: `market_absorption`; `polity`: `state_account`, `interest_groups`; `prices`: `cost_ratios`; `projects`: `committed_cost`; `reporting`: `price_ratios`; `resources`: `mine_catalogue`; `seats`: `dealings`; `workforce`: `trade_spread`. Several are consumed only by the UI today (`sim/ui` counts as one caller area) or only by their own module's function modules; they are listed so the second consumer, a merge or a conversion to a quote can be decided in review.

### Reads that write

171 methods that are published as views still write somewhere below them after the lazy `state.actors` creation is set aside (61 of them are referenced from another module; the rest are internal to their module's views). They trace to the 22 root causes below. Only the first column is a write in the strict sense; most are first-read creation that can move to assembly or a phase, which is what makes the view pure.

| Root | Owner | What it writes | Views it makes impure (count) | Fix in the catalogue |
|---|---|---|---|---|
| `_material_stock` | `ledger` | creates the tonnes ledger on first call, promotes a loaded dict, sweeps non-physical keys into `economy.capacity_pool` | 48: `_material_stock`, `_peek_throttle`, `_win_condition_value`, `bounty_price`, `counter_supply_gap`, `failure_loss` and 42 more | create at assembly or load; the sweep becomes `ChangeCapacityPool` in a phase |
| `techniques_spread` | `production` | records `economy.technique_record_started` the first time a technique is seen in use | 46: `_market_conditions`, `_market_flow_figures`, `_market_outcome`, `_money_refusal`, `bearable_part_of`, `concern_baskets_now` and 40 more | record the first run in a phase hook so `techniques_in_use` is a pure view |
| `seed_opening_industry_experience` | `production` | seeds `projects.industry_seeded` and the opening tenure on first read | 20: `_staffing_draws`, `concern_runs_without_founder`, `concern_staff_by_trade`, `concerns_to_close_for_staffing`, `effective_risk`, `industry_depth` and 14 more | seed once in the opening phase |
| `_foreign_ledger` | `foreign_trade` | creates `ledgers[civilization_id]` on first read | 12: `_cargo_lost_share`, `_foreign_ledger`, `_trader_cost_share`, `_trader_cycle_years`, `_trader_margin_share`, `foreign_lift_capacity_tonnes` and 6 more | create when the partner is loaded |
| `_switch_seat` | `seats` | `act_as` rebinds `self.household` while a method iterates seats | 11: `dealing_party`, `dealings_listing`, `distance_between_seats`, `find_dealer`, `patron_clients`, `quote_concern_sale` and 5 more | seat-keyed views take a seat id instead of switching the acting seat |
| `campaign_store` | `campaigns` | `store.setdefault` on first read of the campaign store | 9: `_garrison_on`, `_stability_of`, `armies_of`, `army_of`, `army_records`, `campaign_column` and 3 more | create at module start |
| `_agent_basket` | `reporting` | `baseline.update` (a memo of the agent basket) | 3: `_agent_basket`, `coin_value_ratio`, `real_price_ratio` | memo only: fold into the view cache |
| `_farm_year_weather_seed` | `agriculture` | assigns `scenario.weather_salt` lazily | 3: `_farm_year_weather_seed`, `_pooled_farm_weather_multiplier`, `farm_weather_by_tile` | fill the year's salt in the phase that draws the weather |
| `_market_entry` | `markets` | creates `book[commodity]` on first read | 3: `_market_entry`, `_open_market_book`, `market_state` | create when a commodity is first priced, in the opening or clearing phase |
| `_foreign_entry` | `foreign_trade` | `foreign_market_book.setdefault`: creates a partner's entry on first read | 2: `_foreign_entry`, `partner_price_response` | create the entry when the partner is loaded |
| `resource_throttle` | `materials` | banks own output and prior stock, notes draws, counts the shortage, stores the signature of the stock it saw | 2: `project_resource_throttle`, `resource_throttle` | split into the pure quote `resource_throttle` and the command `ApplyThrottle`; the shared function computes both |
| `urban_people_by_tile` | `demography` | stores the urban share it computes in `population.urban_share_of_people` | 2: `urban_fraction`, `urban_people_by_tile` | compute in `step_regions_of_people` (the phase) and publish the stored value |
| `_market_flows` | `markets` | accrues `economy.market_flows` while reporting them | 1: `_market_flows` | accrue in the clearing phase only |
| `_material_opening_stock` | `ledger` | writes the year's opening snapshot the first time it is read in a year | 1: `_material_opening_stock` | write it in `begin_seat_year` (`ChangeStock`-free snapshot command) |
| `expected_calendar_years` | `projects` | sets `projects.failed_attempts[node]` to a trial value and restores it | 1: `expected_calendar_years` | compute from a copy |
| `founder_exposure` | `coin` | built `take` closures that mutate purse, stock and granary (done: `household_exposure` returns amounts, the theft sends `TakeGoods`) | 1: `founder_exposure` | done |
| `refresh_farm_territory` | `agriculture` | calls `labour.set_farm_area` | 1: `refresh_farm_territory` | a command to workforce (`AllocateFarmLabour`), made in the phase |
| `clear_unused_hours_report` | `workforce` | pops `household.unused_hours_reported` as it reports | 1: `report_unused_directed_hours` | report and clear are two steps; clear is a command in the phase |
| `revenue_capacity` | `production` | assigns `household.wage_hours_this_year` while computing capacity | 1: `revenue_capacity` | a real write inside a read; send `CommitHours` from the phase and make capacity pure |
| `_staffing_tally` | `ventures` | assigns `projects.staffing_tally` while summarising | 1: `staffing_closure_summary` | record in the staff phase |
| `substitution_quality` | `projects` | assigns `household._last_subst_gap` (a note for the next message) | 1: `substitution_quality` | return the gap with the answer |
| `capability_factor` | `production` | assigns `household._cap_factor` (a memo) | 1: `workshop_output` | fold into the view cache |

Also found by reading, not by the scan: `expected_calendar_years` briefly sets `projects.failed_attempts[node]` to a trial value and restores it (`projects_progress.py` around line 450); `_peek_throttle` snapshots and restores the stock and the market flows (`economy_electricity.py:523-541`); `founder_exposure` returns lots whose `take` closures mutate the purse and stock (`holdings_exposure.py:60-85`). A view cannot do any of the three; each is a quote computed from copies, with the commit as a command.

### Cycles in reads

The module-level read graph is **one strongly connected component of 26 of the 28 modules** (outside it: `campaigns`, `stores`). Mutual reads are the rule, not the exception, so assembly must not require modules to form a DAG; what freshness needs is that the **view-level** graph, from the declared `inputs`, is acyclic. It is: 0 view cycles among the 141 declared views (the check covers only declared inputs; reads inside a view's computation that are not declared are not in it).

Strongest mutual pairs (views read each way): `production` <-> `workforce` (7, 3); `projects` <-> `workforce` (7, 2); `finance` <-> `workforce` (7, 1); `materials` <-> `resources` (4, 4); `production` <-> `ventures` (2, 6); `materials` <-> `projects` (3, 4); `prices` <-> `production` (4, 3); `markets` <-> `production` (3, 4); `markets` <-> `prices` (3, 3); `projects` <-> `ventures` (3, 3); `finance` <-> `projects` (2, 3); `markets` <-> `reporting` (1, 4); `production` <-> `projects` (1, 4); `foreign_trade` <-> `freight` (3, 2).

Real data cycles to prove or break before those modules migrate (each is a pair or triple whose values feed each other within a year, not just two modules that happen to talk):

1. `prices` <-> `production`: material prices depend on techniques in use (`price_epoch`), and revenue depends on prices. Today broken because techniques change at project completion, not inside the year; the equivalence tool must show it.
2. `materials` <-> `resources`: mine capacity feeds material supply; mine operating cost reads prices which read supply.
3. `projects` <-> `ventures` <-> `production`: starting a project opens ventures; venture crews and quotes read revenue and upkeep. If the prototype shows these three cannot be separated, the fallback is to merge `ventures` into `production` (their mutual reads are 2 and 6) and leave `projects` the lifecycle only.
4. `mechanics` <-> `production`: removed in this catalogue by moving `running_with_mechanic` to `production`; `mechanics` then reads only `knowledge`.
5. `markets` <-> `production` / `prices` / `workforce`: the clearing reads wages, techniques and revenue and writes them back through the year's close.
6. `finance` <-> `projects`, `knowledge` <-> `projects`, `hazards` <-> `projects`: a read one way and a command the other; not a data cycle.

## Proposed migration order

Leaves first means the modules fewest others read, so their move changes the fewest consumers, subject to two rules from the data: a module that sends many commands (`projects` 18, `finance` 18, `hazards` 12, `polity` 9) migrates after the owners of those commands exist; and the plan's phases fix the conserved quantities first. The read counts are in the matrix above.

| Wave | Modules | Why | Proof |
|---|---|---|---|
| 2 (prototypes) | `living_stock`, then the command side of `ledger`, then the start slice of `projects` | The three domains of different shape: a leaf that nothing but project starting and the UI reads (6 modules read it; it reads 29 views, the widest outbound fan of a leaf), the busiest command owner (11 modules send to it; 35 `pay_edge`, 8 `receive_from_edge`, 7 `pay_wages`, 28 `book.transfer`/`post` and 7 `move_goods` call sites, `grep -rnE "<name>\(" sim mods --include=*.py | grep -v /tests/ | grep -v "def " | wc -l`), and the heaviest reader (42 views). | Equivalence micro tier after each; gate report 2.4 |
| 3a | `reporting` (`RecordEvent` only), then the rest of `ledger` (reporting shipped whole on `mr/reporting`: 100 sites converted) | 104 `.log.append` sites across about twelve modules change no value and remove the largest write fan-out; the ledger's remaining commands are `Transfer`, `PostBatch`, `MoveGoods`, `ChangeStock`, `NoteSpend`, `ResetBalance`, `MarkCash` | full equivalence tier, conservation tests |
| 3b | `workforce` (hours: `CommitHours`, `Hire`, `Fire`, `LoseStaff`), `land` (`TransferTile`), `demography` (`KillPeople`, `MovePeople`) | Owners of conserved quantities; `hazards`, `campaigns`, `disease` and `finance` write into them today | full tier, conservation tests, save round trip |
| 4 | `workforce` (the package), `land` (the package), `markets` (the package), `disease` | The walled packages become modules; their adapters become declared view lists and the lazy port properties go | save round trip; long tier after |
| 5a (leaves) | `campaigns`, `stores`, `freight`, `agriculture`, `resources`, `foreign_trade`, `coin`, `diffusion`, `mechanics`, `knowledge` | Few modules read them (readers: campaigns 0, stores 2, freight 3, agriculture 4, resources 7, foreign_trade 6, coin 6, diffusion 7, mechanics 15, knowledge 17); `mechanics` and `knowledge` are read by many but read almost nothing (7 and 4 views), so they are leaves of the dependency graph | per-module equivalence |
| 5b | `hazards`, `seats`, `polity`, `actors`, `prices`, `materials` | `hazards` is the widest writer (needs 8 command owners done); `seats` carries `act_as`; `prices` holds the solver; `materials` holds the throttle quote/commit split | per-module equivalence, random state check for hazards |
| 5c (hub) | `finance`, `production`, `ventures`, `projects` (the rest) | Most-read and most-sending; `production` is read by 16 modules and reads 20 providers; `ventures` and `projects` are in a cycle with it | full and long tiers every merge |

The greedy order from the read graph alone (fewest reads into the modules still to place first) is: `stores`, `ledger`, `actors`, `knowledge`, `mechanics`, `agriculture`, `campaigns`, `demography`, `disease`, `land`, `reporting`, `seats`, `diffusion`, `freight`, `foreign_trade`, `hazards`, `markets`, `materials`, `prices`, `resources`, `workforce`, `polity`, `coin`, `living_stock`, `production`, `finance`, `projects`, `ventures`. Its back edges (a module reading one placed later, which must go through an old-method forwarder until the later module moves) are the heaviest cut: `campaigns` -> `land` (4); `reporting` -> `markets` (4); `diffusion` -> `workforce` (4); `freight` -> `workforce` (4); `foreign_trade` -> `markets` (4); `materials` -> `resources` (4); `prices` -> `production` (4); `knowledge` -> `projects` (3); `demography` -> `land` (3); `reporting` -> `workforce` (3).

## The year's shared phases

`SHIPPED` in `sim/engine/year_phases.py` hides that six of its phases are sequences of steps belonging to several modules, in an order that is part of the behaviour. Read from `step_phase_money.py`, `core_step_phases.py` and `market_clearing.py`. When a phase is split by owner, the order below must survive: either the root runs an ordered list of (module, step) hooks inside the phase, or each hook is a `PhaseHook` with an explicit `after`. Reordering changes results.

| Phase | Step, in order | Owner after the move |
|---|---|---|
| `begin_seat_year` (`core_step_phases.py:110-116`) | 1. scandal mark `scandal_last_year`<br>2. automation audit<br>3. `hear_of_other_seats` | 1. polity<br>2. reporting<br>3. seats (split into the phases `begin_seat_year`, `trim_audit`, `hear_of_other_seats`) |
| `begin_world_year` (`core_step_phases.py:118-123`) | 1. `refresh_derived_nodes`<br>2. `refresh_farm_territory`<br>3. `_open_market_book` | 1. production<br>2. agriculture<br>3. markets |
| `money_seat` (`step_phase_money.py:32-157`) | 1. living cost, dependants, mine cost, coin keeping due (reads)<br>2. receive venture revenue; pay upkeep, living costs, mine costs, coin guards<br>3. `charge_founder_for_theft`<br>4. `mothball_mines`<br>5. `reopen_restaffed_ventures`, `close_lapsed_dependents`, `close_unstaffed_ventures`, `auto_open_ventures`<br>6. `charge_interest`, `note_venture_year`, `shed_loss_makers`, `warn_near_the_limit`, `enforce_credit_limit`<br>7. insolvency floor and bleed<br>8. auto-buy people, auto-manumit | 1. workforce, resources, coin<br>2. ledger (commands from production, workforce, resources, coin)<br>3. coin<br>4. resources<br>5. ventures, projects<br>6. finance, ventures<br>7. finance, workforce (staff cuts)<br>8. workforce |
| `money_world` (`:159-188`) | 1. output-factor recovery<br>2. `_demographic_recovery` (with `step_regions_of_people`, `advance_colonies`)<br>3. `advance_society`<br>4. `advance_actors` | 1. hazards<br>2. demography, land<br>3. diffusion<br>4. actors |
| `seat_work` (`core_step_phases.py:125-139`) | 1. `_step_teach_trades`, `_step_standing_work_directive`<br>2. `_step_start_projects`<br>3. `_step_materials`<br>4. `_step_progress`<br>5. `_step_wage_fallback`<br>6. `_step_reputation`: reputation, familiarity, protection, scandal, levies; hours capture and reset; `spend_last_year`<br>7. `_step_bondage`<br>8. `_step_founder_mortality` | 1. workforce<br>2. projects<br>3. materials<br>4. projects<br>5. workforce<br>6. polity; workforce; ledger<br>7. finance<br>8. seats |
| `market` (`market_clearing.py:193-202`) | 1. `finish_ways` (then `finish_works`)<br>2. `_open_market_book`, `economy.run_agent_year`<br>3. `record_food_eaten`<br>4. `close_partner_books`<br>5. `_close_real_output`<br>6. `revalue_coin_metals`<br>7. `record_wage_market_ratios` | 1. land<br>2. markets<br>3. demography<br>4. foreign_trade<br>5. reporting (the command `CloseRealOutput`, sent from the end of `_step_market`)<br>6. coin (the phase `coin_revaluation`)<br>7. reporting (the phase `wage_market_ratios`) |

`enforce_credit_limit` runs twice a year: inside `money_seat` (`step_phase_money.py:97`) and as the shipped phase `credit_limit`. Whether the second run is meant is not decided here.

## How the numbers were made

All static, no game built and no test run. Scripts were kept in the scratch area, not in the repository; the steps are reproducible from the plan's Appendix B.

1. Appendix B of `MODULE_REGISTRY_PLAN.md`, unchanged, for the kind of each referenced method (reads only, writes, pure). Reproduced: 906 / 640 / 13.
2. An extension of the same script: for every method or property referenced across mixin classes, its defining class, its kind, and its callers as `Class.method`; and, per mixin method, the instance fields it reads and writes (AST over `self.<section>.<field>` and `self.state.<section>.<field>` chains and local aliases such as `household = self.state.household`).
3. A second run with `actors` and `edge` treated as lazy initialisation instead of writers, giving the adjusted split in the summary.
4. A regrouping table (mixin class to module, with per-method overrides for the classes that mix topics: `ActorsMixin`, `CreditMixin`, `EconomyMixin`, `FogMixin`, `StepPhasesMixin`, `MaterialSupplyMixin`, `ProductionMixin`, `FreightMixin`, `GoodsMixin`, `MiningMixin`, `ForwardingPropertiesMixin` by field, and the body of `Sim`), and an ownership table for every field of `HouseholdState`, `ProjectsState`, `HoldingsState`, `EconomyState`, `PopulationState`, `DiseaseState`, `FounderState`, `GovernanceState` and `SeatProgressState`.
5. Field access across modules: an AST pass over all mixin methods and over every other function in `sim/` outside `tests`, resolving `state.household.x`, `household.x`, `projects.x`, `holdings.x`, `economy.x`, `population.x` and the forwarding aliases; reads and writes separately.
6. Package handle use: `self.labour.<member>`, `self.geography.<member>`, `self.world_map.<member>`, `self.economy.<member>`, `self.goods_market.<member>`, `self.actors.<member>`, `self.stores.<member>`, by AST inside mixin methods and by pattern in other files. Reproduces the plan's 106 / 27 / 51.
7. Direct writes to owned fields: an AST scan of assignments, augmented assignments, deletes and container mutators (`append`, `update`, `pop`, `add`, `discard`, `setdefault` and the like) on the paths above, with file and line.
8. Caches: attribute stores whose name contains cache, memo, seq, stamp, version, sig, epoch, scope or facade, and `__dict__[...]` stores, in `sim/` outside tests.
9. The catalogue itself (views, commands, inputs) was written by hand from those tables. A validator checked that every replaced method exists and belongs to the module claiming it, every owned field and every handle member is claimed at most once, every view input exists, every cross-module method reference and field access resolves to a view or a command (zero unresolved), and that the view graph has no cycle.

Limits of the method: it is static. Calls through a local variable, `getattr`, a callback passed in, or a method reached on another object are missed; a write through an object passed as an argument is missed; the field scan misses a field reached through a variable that is not a plain alias of `self`. The counts are lower bounds on the coupling, as the plan says of its own.

## What this draft does not settle

- **View grain for heavy readers.** See the 15-read flag. A decision on counting (views, providers or bundles) is needed before the gate.
- **Whether `ventures` is its own module.** It reads `production` six times and `production` reads it twice; if the prototype for project starting finds them inseparable, merge them.
- **`stores`** is a framework service more than a module; the assembly may carry it.
- **`actors` and the agents package.** `sim/agents` is 159 files that already act as a module with its own registry; `actors` here is only the engine's side (registry accessors and `agents_port*`). Whether `Government` and `Firm` become modules of their own, or `polity` and `production` split further, is not decided here.
- **Names not opened.** Where a module file describes a function module (for example `solve_prices_round.py`, `labour/market/year.py`) from its name and its size rather than from reading it, the file says so in its hard spots only for what was read; treat the rest as unchecked.
- The per-module `Replaces` lists are the cross-module surface only. Methods used inside a module stay internal and are listed by name in (a) of its file.

