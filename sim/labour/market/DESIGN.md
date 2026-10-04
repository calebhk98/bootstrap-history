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
   `completion_chance * present_value(expected_wage after training) + (1 - completion_chance) * present_value(fallback expected_wage after training)`.
   - `expected_wage = average_wage * employment_share * hours_per_worker_year`. This is Harris-Todaro: idle markets look worse.
   - Applicants beyond a trade's intake go to their next choice, and finally to the fallback trade.
   - The training premium of a trade is not written anywhere. It is the wage at which enough able people choose the trade.
5. **Switching** (`switching.py`). Workers re-weigh their trade against the others, with a stay option.
   - The gain is the present value of the expected-wage difference, less the retraining time, in units of a year's subsistence.
   - Retraining within a skill family takes a share of the full training.
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

## Status and what is outside this folder

See `Complaints/` for the switches the economy and engine owners need to make. The file numbers are listed in
`sim/labour/README.md` once written.
