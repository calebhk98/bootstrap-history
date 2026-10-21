# A higher tax rate has no consequence beyond revenue and a typed burden weight

**Status:** partly - a harvest tax and a land tax reach the farmer's and the owner's own rules; concealment of income from a form follows the rate and the officials' reach in both layers (actors and the economy's money, harvest and trade forms), and the AI state's rate-raise yield counts it; the flight comparison, the liability rule and the amnesty, immunity and remission levers are built as rules (below) but the engine does not yet feed them into the labour market's year inputs or the AI state's menu; unrest (486) is open, so `FISCAL_BURDEN_WEIGHT` stays

Follows from 626 (tax rates as a state choice).

**What is wrong now.** A state can raise the rate of a form (a player's lever, or an AI state's `raise_rate` response). The
base now responds in three ways (below), but not in these:

- Flight from a taxed tile: `sim/labour/market/migration.py` (workers weigh the log of expected income over subsistence in
  each area against their own, less moving cost) has no per-area after-tax figure. `tax_burden.harvest_share_taken` already
  gives one for the harvest; it would pass through `YearInputs` into `_real_income`.
- No unrest from a heavy burden (486).
- The producers' land demand and run decisions in the economy do not net a harvest tax off expected revenue
  (`land_market.demands_of`).
- The AI state's `raise_rate` option does not count the base lost through flight or unrest. It weighs a raise by
  `FISCAL_BURDEN_WEIGHT` (`sim/agents/tuning_fiscal.py`), a labelled stand-in; it retires when the menu values those too.

**Why it matters.** Without a full response of the base there is a ceiling to taxation only at the rate cap, and a state
cannot lose by overtaxing in every way a real one does (CLAUDE.md 4.1: the outcome should come from lower-level state, not
from a typed elasticity).

**What it would take.** Finish the payers' own choices (households and firms compare what they keep with what they could keep
elsewhere), then the AI state values the loss of base as a consequence of a raise. Test: raising a rate on a base whose payers
can leave lowers the base next year; an AI state with the loss in its menu raises a rate less than one without.

## Built

- **Harvest tax reaches farm effort.** `sim/agents/tax_burden.py` `harvest_share_taken` reads the state's present rates
  (levers included), the tiles each form covers and the share its officials reach; `LabourWorld.harvest_share_taken`
  hands it to `_farm_hour_value_over_wage` (`sim/labour/labour_allocation.py`), which decides on
  `farm_intake.value_over_wage_after_tax`. Hands leave the land by the existing `kept_farm_workers` rule when the ratio falls
  under one.
- **Land tax reaches the owner's holding.** `tax_burden.land_tax_share_of_rent` turns a form on `land_rent` or `land_value`
  into a share of the rent; `YearInputs.land_tax_share_of_rent` carries it to `land_market.settle_year` and
  `titles.settle_tenancies`: a lessor whose managing cost plus the tax exceed the rent lets the title go (`titles.release`, 538).
- **Poll tax** acts through household cash: `taxes._collect_money` pays no more than the purse holds, and an unpaid remainder
  is an arrear.
- **Income is hidden from a rising rate.** `sim/agents/evasion.py` `hidden_share`: a payer hides the share at which the last
  unit's saving equals the rising cost of hiding it, up to a ceiling, so a higher rate hides more and a state whose
  officials reach more is hidden from less. `revenue.taxed_actors` assesses only declared income; `fiscal_response.rate_raise_yield`
  nets the extra hiding. The economy's forms hide by the same rule through `EconomySetup.hiding`
  (`sim/engine/economy_port_setup.py`), so the economy imports nothing from the actors. Customs duties on border imports
  are not under it. `HIDEABLE_SHARE_OF_INCOME` and `HIDING_MARGINAL_COST_AT_CEILING` (`sim/agents/tuning_evasion.py`) are
  labelled heuristics with `retire` 657.
- Tests: `test_tax_pressure_reaches_decisions.py` (rules called with built inputs; the engine wiring is covered only by
  whole-game topics), `test_tax_evasion.py`, `test_tax_evasion_economy.py`.

- **Flight is the migration rule.** `sim/labour/market/migration.py` scores each route by the income kept after the state's take
  in that area (`YearInputs.taxed_share`) less the move's cost, which now includes the expected penalty of recapture
  (`Route.expected_penalty`, from `sim/agents/flight.py` `expected_penalty_of_leaving`: the chance of recapture at the
  state's reach on the tile he goes to times what he owes with the penalty at that reach). Taxed land a fleeing tenant leaves
  is released to no holder by `sim/economy/titles_flight.py` `tenant_flees` (538's rule).
- **Liability is a state choice.** `sim/agents/liability.py`: individual, or collective per unit, where the stayers split the
  unit's assessment (the merismos). Tested for the sourced spiral: under collective liability a shock raises the stayers'
  take and a larger share leaves each year; under individual liability the take and the share leaving stay flat.
- **Levers** (`sim/agents/government_levers_tax.py`, through `lever`/`levers`): `liability`, `amnesty` (share of arrears
  waived), `immunity` (years a taker of deserted land owes nothing; `flight.share_after_immunity`) and `remission` (every
  form's rate, read through `government_levers.revenue_forms`, so revenue and `tax_burden` see it).
- **Hiding and Yitzhaki.** A penalty in proportion to the tax unpaid leaves the rate out of the choice; the rate effect in
  `evasion.py` comes only from the hiding-cost curve, which stays labelled (`HIDING_MARGINAL_COST_AT_CEILING`).
- Tests: `test_tax_flight_and_liability.py`.

**Still open.** (a) The engine does not yet fill `YearInputs.taxed_share` and `Route.expected_penalty`
(`sim/economy/labour_inputs.py` builds the routes), nor call `tenant_flees` or the return rule each year, nor read
`immunity` where land is taken up; the rules and levers exist and are tested, the wiring is not. (b) The AI state's menu does
not pull `liability`, `amnesty` or `remission`, and `rate_raise_yield` does not net the base lost through flight, so
`FISCAL_BURDEN_WEIGHT` stays. (c) Return of fugitives is the same comparison run backwards (`flight.arrears_owed_by_fugitive`
as the route's cost) but no year step moves them. (d) Unrest (486). (e) The hiding-cost curve has no source.

## Research needed

No source on pre-modern tax pressure, flight and abandonment was opened, so the hiding constants and `FISCAL_BURDEN_WEIGHT`
have none. The question: how did taxpayers respond to a heavier take in the Roman and medieval worlds, by form (flight of
tenants and the abandoned land of the late empire, anachoresis in Roman Egypt, concealment, evasion, revolt), and at what
share of the harvest did each begin? Sources to open: Roman Egypt tax-flight papyri studies, the Codex Theodosianus on agri
deserti, and medieval English peasant flight and tallage studies. A response curve fitted to those is a validation of the
mechanism, not an input to it.
