# The labour-market core

One simulated year of a labour market over plain records (`records.py`). Any actor (the founder, a firm,
a state, a later player) takes part only through what it bids, what schools it runs and where it is.
Nothing here names a trade, a material or a civilisation; trades arrive as a registry (`trades.py`).

## State

People are counted per labour area × trade × ability band (`aptitude.py`). Trainees are cohorts per
area × trade: `[years_left, people per band, completion_bonus]`. Market wages are remembered per area × trade.

## The year (`year.py`), in order

1. **Clearing** (`clearing.py`), per (trade, area).
   - Every worker offers `hours_per_worker_year` at the area's reservation wage:
     `reservation_wage = subsistence_per_worker_year / hours_per_worker_year * (1 + fatality_risk_per_year * value_of_life_years_of_income)`.
   - Employers bid hours up to a `maximum_wage`. The market wage moves a share of the way toward the
     clearing point each year (sticky).
   - An employer pays `market_wage * (1 + pay_premium)`, capped at its maximum. Hours go to the highest
     payers first.
   - Workers who stay with an employer keep their hours. New hires are limited by a matching function
     of searchers per vacancy, which is recruitment friction: a large new hire fills over several years.
     A premium raises the employer's matching rate and lets it draw workers from lower payers.
2. **Attrition.** A share of workers and trainees leave work each year (deaths, retirement; demography's number).
3. **Training** (`training.py`). Trainee cohorts age a year. At zero years left they graduate.
   - Each band's chance of finishing is `aptitude.completion_chance(band ability + cohort bonus, difficulty)`.
   - Those who do not finish join the fallback trade.
   - Yearly intake to a trade in an area is capped by its teachers:
     `incumbent workers * apprentices_per_master / training_years + school seats`.
   - A trade with no incumbents and no school cannot reproduce.
4. **Entrants** (`entrants.py`). The coming-of-age cohort chooses a trade, band by band, by logit over:
   `completion_chance * present_value(income_at_graduation) + (1 - completion_chance) * present_value(fallback income) + taste_scale * log(jobs in the trade)`.
   - The cohort chooses in rounds (`expectations.DECISION_ROUNDS_PER_YEAR`); each round sees the places
     the earlier ones took. Choices made all at once overshoot a shortage, the trade gluts a
     training-length later, and wages cycle between floor and ceiling.
   - The log-jobs term (a size variable) makes a trade with many places draw many and one nobody employs
     draw almost nobody, however many trades a mod adds. Without it, a logit over many alternatives spreads
     entrants evenly.
   - `income_at_graduation` is the floor plus what the wage the market is heading to
     (`Clearing.target_wage`: where hours offered meet hours wanted, not the sticky wage) pays over the
     trade's own reservation wage, so danger pay is not a reward. It keeps today's premium only for the
     part of today's shortage that those already training will not fill. A glut shows the floor, however
     high the lagging wage still is.
   - A trade's expected income today (`expected_income`) is Harris-Todaro: the hours that find work earn
     the average wage, the rest earn the outside option. The chance of finding work is hours wanted over
     hours offered, so a few unfilled hours beside idle hands (matching friction) are not a sure job.
   - Applicants beyond a trade's intake go to their next choice, and finally to the fallback trade.
   - The training premium of a trade is not written anywhere. It is the wage at which enough able people choose the trade.
5. **Switching** (`switching.py`). Workers re-weigh their trade against the others, with a stay option.
   - Only moves worth more than staying are considered. Otherwise float noise and the logit's taste spread leak a large idle trade into a glutted one.
   - The gain is the present value of the expected-wage difference, less the retraining time, in units of a year's subsistence.
   - Retraining within a skill family takes a share of the full training.
   - A destination is weighed by `income_at_graduation` whether or not it has workers already, and
     switchers also choose in rounds. Weighing a trade that has workers by its pay today made a shortage
     the apprentices would fill still draw switchers and flooded it.
   - Switchers become trainees of the new trade and use the same intake.
6. **Migration** (`migration.py`). Workers re-weigh their area against the routes out of it, with a stay option.
   - The comparison is the log of real expected wage (expected wage over subsistence) in the same trade, less the moving cost in years of subsistence.
   - Only listed routes are considered, so the cost is areas × routes × trades.

Every logit uses a log-sum-exp guard. Every move takes people out of one count and puts the same float
into another, and a test checks that people are conserved.

## Paying above the market

`Bid.pay_premium` is the actor's lever.
- It fills first.
- It matches faster, through `(1 + pay_premium) ** FIRM_LABOUR_SUPPLY_ELASTICITY`.
- It draws from lower payers.
- It raises the trade's average wage in the area, which pulls entrants, switchers and migrants in later years.

## Schools

`School(owner, trade, area, seats, completion_bonus)` is an intake on top of apprenticeship. Seats
produce workers only after the trade's training years, and only as many as can finish. A school cannot
create aptitude. Its bonus shifts the completion curve.

## Heuristics

Every tuning number is declared with `kind="temporary_heuristic"` beside the code that uses it.
`python3 sim/constants.py --burndown` lists them.

## Opening

`opening.py` places each area's working people in the trades its work needs. Hard trades are staffed
first from the bands able to finish them; the rest go to the fallback trade.

## Demand must slope

Clearing finds the wage where hours offered meet employers' bids. If every bid for a trade sits far above
the workers' ask, demand is vertical over the range that matters. A one-percent swing in supply then
moves the wage from floor to ceiling. Callers should bid in tranches of falling value: the marginal
worker is worth less than the first.

## Status and what is outside this folder

The core is complete and tested (`python3 -m sim.tests --only labour_core_training,labour_core_clearing,labour_core_entrants,labour_core_switching,labour_core_migration,labour_core_opening,labour_core_year,labour_core_walls`).
The agent economy (on by default) calls it every year (`sim/economy/year_labour.py`) and keeps its state
in its record, so the core sets the wage every employer is quoted. The engine's hours by trade are
the core's people by trade (`sim/labour/labour_allocation.py`); until the agent economy has opened they follow
the need the recipe graph puts on each trade. Still outside the core:

- Complaint 429 (done for `literate`, `taught_from`, `tool_basket`, `staff_resource`, `fatality_risk_per_year`,
  now read from the trade registry): `difficulty` and `fallback` are still derived in code, and
  `legacy_trade_defaults.py` keeps the role constants.
- Complaint 430: a saved field and a yearly call, plus the household fields for a standing pay premium and
  school cohorts.
- Complaint 432: the subsistence staple is wheat for every civilisation.
- Complaint 433: the player's hire command takes a premium and shows how many can be found.
- Complaint 434: recipe need shares behind trade populations overweight mining and omit transport.
