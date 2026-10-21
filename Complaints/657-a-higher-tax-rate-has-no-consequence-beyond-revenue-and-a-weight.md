# A higher tax rate has no consequence beyond revenue and a typed burden weight

**Status:** partly - a harvest tax and a land tax reach the farmer's and the owner's own rules; concealment, flight and unrest (486) and the AI state's foresight of the loss are open, so `FISCAL_BURDEN_WEIGHT` stays

Follows from 626 (tax rates as a state choice).

**What is wrong.** A state can raise the rate of a form (a player's lever, or an AI state's `raise_rate` response), and the
form yields more of the same base. Nothing else follows from the higher rate: the taxed base does not shrink, hide, move
or stop being worked, and compliance does not wear down. The AI state weighs a raise only by `FISCAL_BURDEN_WEIGHT`
(`sim/agents/tuning_fiscal.py`), a typed heuristic, so it will keep raising a rate as far as the shortfall asks, up to the
yearly step. A rate that costs nothing but a weight is still an input, not an outcome.

**Evidence.** `sim/agents/fiscal_response.py` (`menu`, the `raise_rate` option); `sim/agents/revenue.py` (the base does not
read the rate); `concealed` and `defiance` on `ActorRecord` are set by demand answers, not by the rate.

**Why it matters.** Without a response of the base, there is no ceiling to taxation but the rate cap, and no way a state
loses by overtaxing (CLAUDE.md 4.1: the outcome should come from lower-level state, not from a typed elasticity).

**What it would take.** A mechanism for how taxpayers respond to the share taken: concealment of income and land,
migration out of a taxed tile, withdrawal of labour, from the payers' own choices (households and firms compare what they
keep with what they could keep elsewhere), not a typed elasticity. Then the AI state values the loss of base as a consequence
of a raise, and `FISCAL_BURDEN_WEIGHT` retires.

**Test.** A test: raising a rate on a base whose payers can conceal or leave lowers the base next year; an AI state with the
loss in its menu raises a rate less than one without.

## Progress

- **Harvest tax reaches farm effort.** `sim/agents/tax_burden.py` `harvest_share_taken` reads the state's present rates (levers
  included), the tiles each form covers and the share its officials reach. `LabourWorld.harvest_share_taken`
  (`sim/engine/labour_port.py`) hands it to `_farm_hour_value_over_wage` (`sim/labour/labour_allocation.py`), which now
  decides on `farm_intake.value_over_wage_after_tax`: a farm hour's food at the staple's price less the share taken, over the
  wage. Hands leave the land by the existing `kept_farm_workers` rule when the ratio falls under one.
- **Land tax reaches the owner's holding.** `tax_burden.land_tax_share_of_rent` turns a form on `land_rent` (its rate) or
  `land_value` (its rate over the market rate of interest) into a share of the rent. `YearInputs.land_tax_share_of_rent`
  carries it to `land_market.settle_year` and `titles.settle_tenancies`: a lessor whose managing cost plus the tax exceed the
  rent holds a loss and lets the title go (abandonment through `titles.release`, the path 538 built). `tax_burden.after_tax_rent`
  is the owner's net figure.
- **Poll tax** already acts through household cash: `taxes._collect_money` pays no more than the purse holds, and an unpaid
  remainder is an arrear.
- Tests: `sim/tests/test_tax_pressure_reaches_decisions.py` (share taken, harvest tax lowers farm effort, land tax lowers the
  net rent and makes a marginal tenancy a loss). They call the rules with built inputs; the engine wiring (`labour_port`,
  `economy_port_land`) is covered only by whole-game topics.
- Still open: no taxed base is concealed or moved (needs households' and firms' choice between declaring, hiding and leaving a
  taxed tile); no unrest or flight (486); the producers' land demand and run decisions in the economy do not net a harvest
  tax off expected revenue (`land_market.demands_of`); the AI state's `raise_rate` option does not yet count the base lost
  through these. `FISCAL_BURDEN_WEIGHT` therefore stays as the labelled stand-in; it retires when the menu values the
  measured fall in base.
- Sources: no source on pre-modern tax pressure and abandonment (agri deserti) was opened in this session, so none is cited.
