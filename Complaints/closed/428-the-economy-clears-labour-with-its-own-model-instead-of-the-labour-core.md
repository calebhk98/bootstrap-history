# The economy clears labour with its own model instead of the labour core

**Status:** closed - the core sets wages and the engine's hours by trade; see Resolution

`sim/economy/labour.py` and `sim/economy/year_labour.py` (clear, move_workers, follow_asks,
trade_premium) are a second labour market beside `sim/labour/market/`. The agent economy is on by
default, so its per-tile clearing sets the wage every employer is quoted (`LabourMarket._annual` reads
`economy.agent_wage_per_hour`). Its workers move between trades on a tile as a fixed share of the idle,
with no training time, no ability, no migration between tiles and no schools, and its training premium
is a written formula rather than an outcome. The labour core
(`sim/labour/market/DESIGN.md`, reached through `sim.labour.api`) does all of these. Its tests run in
well under a second: `python3 -m sim.tests --only labour_core_year`.

Why it matters: two models of the same market drift apart (Complaint 115). Skill scarcity, schools,
migration and paying over the market only reach the game through the model that sets the wage.

What it would take (all in `sim/economy/`, owner of that package):
- `record.workforce[tile][trade]` becomes a `sim.labour.api.MarketState` (people per ability band, trainee
  cohorts, wages, each employer's hours), kept in the record. Use `market_state_to_plain` and
  `market_state_from_plain` for the save.
- Each year's `LabourBid`s become `sim.labour.api.Bid` records, one per tranche of falling marginal value
  (a single flat bid per producer makes demand vertical and the wage jump floor-to-ceiling; DESIGN.md
  "Demand must slope"): employer, trade, area (the labour area
  key), hours, `maximum_wage`, and `pay_premium` (zero unless the employer chooses one).
- `subsistence_per_worker_year` comes from `outside_option_by_tile`. `entrants` and `attrition_share`
  come from the demography cohorts. `routes` come from the tile neighbours and freight cost already used
  for market areas.
- The opening workforce comes from `sim.labour.api.opening_labour_market` (hard trades staffed from the able).
- `clear_labour` then calls `sim.labour.api.clear_labour_markets` and settles each `Clearing`'s
  `hired_by_employer` × `paid_by_employer`. `move_workers` and `follow_asks` are replaced by the rest of
  `run_labour_year`.
- Delete `sim/economy/labour.py`'s clearing, `labour_asks.py` and `TRADE_MOBILITY_SHARE_PER_YEAR`.
- After this, `sim/labour/labour_market.py`'s `Workforce.step` (society hours by trade,
  `labour_allocation.reallocate`) is a third copy. The engine should read hours by trade from the same
  state, and that module goes. (Done: see Resolution.)

## Resolution

- The engine's hours by trade (`society_labour_hours`) are the labour core's people by trade while the agent
  economy runs and the recipe graph's need while it is off; the farm's hours follow the food balance at the
  occupational mobility rate. `Workforce.step` and `labour_allocation.reallocate` are gone.
- Skill premium: a trade needing long training paid the labourer's wage in the agent economy. The core's
  switchers weighed a destination that already had workers by its pay today (not by what it will pay once
  they are trained, net of those already training), took a few unfilled hours beside idle hands for a sure
  job, and chose all at once; entrants did the same and read the sticky wage of a glutted trade, and the
  danger pay of a risky trade, as reward. Skilled trades filled past their jobs and sat at the floor. Now
  both choose in rounds that see each other's places, weigh `income_at_graduation` (the wage the market is
  heading to, over the trade's own reservation wage), and the opening seeds no written wage. Tests:
  `economy_labour_core`, `labour_core_switching`, `labour_core_entrants`.
- The opening glut of skilled workers is Complaint 465. The dead constants `MAXIMUM_REALLOCATION_PERIODS`
  and `CONVERGENCE_TOLERANCE_HOURS` remain in `sim/algorithm_parameters.py` (outside the labour package);
  nothing reads them.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 430 (`closed/430-the-labour-core-has-no-save-field-and-no-yearly-call.md`): the labour core has no save field and no yearly call; the same decision as this issue.
- 435 (`closed/435-han-opening-wages-spread-over-two-orders-of-magnitude.md`): Han opening wages: carpenter outlier and a scale mismatch between the agent economy and the wage schedule, which go when one model sets wages.
- 433 (`closed/433-ui-cannot-offer-pay-over-the-market.md`): the UI cannot offer pay over the market; blocked until the premium is charged yearly by the labour core.
