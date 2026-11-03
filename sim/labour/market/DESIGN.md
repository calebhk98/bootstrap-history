# The labour-market core

One simulated year of a labour market over plain records (`records.py`). Any actor (the founder, a firm,
a state, a later player) takes part only through what it bids, what schools it runs and where it is.
Nothing here names a trade, a material or a civilisation; trades arrive as a registry (`trades.py`).

## State

People are counted per labour area × trade × ability band (`aptitude.py`). Trainees are cohorts per
area × trade: `[years_left, people per band, completion_bonus]`. Market wages are remembered per area × trade.

## The year (`year.py`), in order

1. **Clearing** (`clearing.py`), per (trade, area).
   - The hours offered in a market are what its households sell (`YearInputs.hours_sold_at`, the hours their offers hold,
     rising with the wage); a caller giving no schedule has every worker sell `hours_per_worker_year`. The ask is the reservation wage:
     `reservation_wage = subsistence_per_worker_year / hours_per_worker_year * (1 + fatality_risk_per_year * value_of_life_years_of_income)`.
   - Employers bid hours up to a `maximum_wage`. The wage the search rounds start from rises a share of the way toward the
     clearing point each year and falls to it at once (Eurace's `WAGE_OFFER` only rises, Firm_update_wage_offer; the
     workers' ask falls by `asks.py`). There is one wage per trade and area: retained hours are paid it like new hires, so no
     employer holds a contract of its own. (Eurace instead raises existing employees' wages each month by productivity
     progress times union strength, Statistical_Office/Firm_Statistics_Functions.c; this model has no such step.)
   - Before the search rounds an employer lays off the hours it holds beyond those it wants (`layoffs.py`,
     `hours_to_lay_off`, after Eurace's `Firm_set_labour_market_actions`: it counts hours, not employees, and does not pick whom to dismiss);
     one holding fewer than it wants lays off none. The random dismissals inside the rounds are in `applications.py`.
   - An employer starts at the market wage, capped at its maximum, and raises its offer each search round
     while its vacancies stay open (below). Hours go to the employers with the highest maximum first.
   - Workers who stay with an employer keep their hours (`MarketState.hired_hours`) unless the employer wants fewer, but not their
     wage. The trade's wage (`Clearing.wage`, `MarketState.wages`) is one figure: the
     hours-weighted mean of the offers actually paid to the hours taken on (`clear_one`, from the hours `hire_through_rounds`
     returns), or the wage the rounds start from when none were taken on. Every hour hired is paid it, and the hours households sell are
     counted at it. New hires come from the year's search rounds
     (`applications.py`, Eurace's protocol): each round every employer dismisses a random share of its workers and reposts
     the vacancies; searchers (the unretained, and the dismissed asking the wage they were paid) apply to a bounded number
     of employers whose offer is at or above their ask; an employer takes on as many hours as it has vacancies; a searcher
     takes the highest offer; searchers who found nothing cut their ask; an employer whose vacancies stay open raises its offer. Recruitment friction is the bounded
     applications and the dismissals, not a fitted rate.
     An employer with a higher maximum is filled first and draws hours from lower ones.
2. **Training** (`training.py`). Trainee cohorts age a year. At zero years left they graduate.
   - Each band's chance of finishing is `aptitude.completion_chance(band ability + cohort bonus, difficulty)`.
   - Those who do not finish join the fallback trade.
   - Places to learn at once in a trade in an area are its teachers' (`training.enrol`): `incumbent workers *
     APPRENTICES_PER_MASTER + school seats` (the constant `APPRENTICES_PER_MASTER`, `training.py`), less the trainees already enrolled; there is no division by the training years.
     Those who apply beyond the places are refused.
   - A trade with no incumbents and no school cannot reproduce.
3. **Expected income after training** (`expectations.income_at_graduation`), which switching weighs. People enter the core only
   through demography: the economy rescales the core's people on each tile to the working people the cohorts hold, so the core has
   no entrants or leavers of its own.
   - `income_at_graduation` is the floor plus what the wage the market is heading to
     (`Clearing.target_wage`: where hours offered meet hours wanted, not the sticky wage) pays over the
     trade's own reservation wage, so danger pay is not a reward. It keeps today's premium only for the
     part of today's shortage that those already training will not fill. Where there is no shortage today, only the share of
     hours employers want finds work (`finds_work`, as in `expected_income`): a glut shows the floor, however high the lagging wage
     still is.
   - Hands that have joined a trade needing no training since its clearing (switchers and migrants take it up at
     once, so no trainee count shows them) are hours offered too: `income_at_graduation` slides the heading wage down the
     clearing's demand schedule (`Clearing.demand`) and counts them in the supply then (`expectations.hours_arrived_since`).
     Without it a thin unskilled market that cleared at its dearest bid drew a twentieth of the whole area's workers in one year.
   - A trade's expected income today (`expected_income`) is Harris-Todaro: the hours that find work earn
     the average wage, the rest earn the outside option. The chance of finding work is hours wanted over
     hours offered, so a few unfilled hours beside idle hands (matching friction) are not a sure job.
   - The training premium of a trade is not written anywhere. It is the wage at which enough able people choose the trade.
4. **Switching** (`switching.py`). Workers re-weigh their trade against the others, with a stay option.
   - Only moves worth more than staying are considered. Otherwise float noise and the logit's taste spread leak a large idle trade into a glutted one.
   - The gain is the present value of the expected-wage difference, less the retraining time, in units of a year's subsistence.
   - Retraining within a skill family takes a share of the full training.
   - A destination is weighed by `income_at_graduation` whether or not it has workers already, and
     switchers also choose in rounds. Weighing a trade that has workers by its pay today made a shortage
     the apprentices would fill still draw switchers and flooded it.
   - Switchers become trainees of the new trade and use the same intake.
   - Of those considering a change in a year, `1 / career_years` of a trade's people are the young who have just come of
     working age (demography adds them to the tile; the core only re-weighs them). They give up the unskilled income, not
     their trade's, weigh a whole career, and consider a trade paying more than that after training even when the training
     cost makes it worth less than staying: the training premium is exactly the wage that leaves such a person indifferent,
     so a rule needing a strict gain over staying could never start or grow a trained trade. The rest are established
     workers (half a career ahead, only moves worth more than staying). Both enrol as trainees through the same places
     (teachers or school seats); `Economy._follow_population` scales trainees and workers of a tile by one factor.
   - A trade's workers who sold no hours this year reconsider at the share that found no work, if that is over the
     yearly consideration share: only those without work look about.
5. **Migration** (`migration.py`). Workers re-weigh their area against the routes out of it, with a stay option.
   - The comparison is the log of real expected wage (expected wage over subsistence) in the same trade, less the moving cost in years of subsistence.
   - Only listed routes are considered, so the cost is areas × routes × trades.

6. **Formation** (`formation.py`, `formation_bonded.py`), run last. A (trade, area) where employers want hours and no one
   works or trains in the trade gets its first hands from the routes that need no teacher.
   - Migrants come first, from the areas that hold the trade, most spare hands first and no more than they can release
     (`spare_people`, `migration_takes`).
   - Bonded people are then bought where the area's civilisation allows it, at the owners' ask and the buyers' bid
     (`bonded_worth.py`); the same purchase also fills vacancies a trade with people still has left.
   - Conversion needs a teacher and a payer, so the caller's own verbs (training schools) carry it out.

Every logit uses a log-sum-exp guard. Every move takes people out of one count and puts the same float
into another, and a test checks that people are conserved.

## A scarce trade's wage today and after training

Training takes years, so a trade whose employers bid far above the cost of training a substitute pays a scarcity
wage this year. `scarcity.py` bounds it: no training needed means the long-run cost (`clearing.trained_substitute_wage`,
the unskilled wage times the training premium); otherwise the hours-weighted worth of the bids (one stray bid with few
hours does not set it), and where trained hands can be fetched, `ImportCosts.supply` gives the bound and the share of the hours wanted that can come at it.
The ceiling is the mean of the bid worth and the bound-capped worth weighted by that share (`short_run_ceiling`), so it follows the hours
that can be fetched instead of switching on once they cover the whole shortage. Fetching counts
only the hours workers sell at the wage (`hours_sold_at`), here and where the hands come from: hours kept for plots
and leisure are not hands in hand, so an area whose workers sell nothing at the going wage has its shortage priced by
what fetching costs, not by the dearest bid (an unskilled wage that jumped to a plot's worth and pulled every skilled
trade with it, Complaint 678). What
switchers weigh is the clearing's `target_wage`, capped at the long-run cost: a person who trains arrives after the
training years, when the shortage the apprentices fill is gone. A worker already in the trade reads today's wage
(`expected_income`) and offers more hours at it through `hours_sold_at`. A switcher into a trade also trains, so it
reads `income_at_graduation`; a faster move within a skill family is only the shorter retraining in `switching.py`.

## Hours bid for and not hired

Two rules in the search loop of `applications.py` keep hours from sitting idle beside open vacancies:
- An employer whose vacancies stay open (over `VACANCY_SHARE_THRESHOLD` of the hours it wants) raises its offer each round by
  `WAGE_UPDATE_PER_ROUND` (Eurace's `Firm_update_wage_offer`, `raised_offer`), not past `offer_ceilings`: what its least valuable
  wanted tranche is worth to it, the short-run ceiling and the clearing point. An offer is never lowered, and there is no separate
  yearly raise. The offers end as the mean paid to the hours each employer took on.
- A searcher's ask is capped at the best offer an employer with a vacancy posts (`capped_asks`): a seller does not ask
  more than any buyer is seen to pay, as `asks.record` already holds for the market's ask.

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

The core is complete and tested (`python3 -m sim.tests --only labour_core_training,labour_core_clearing,labour_core_switching,labour_core_migration,labour_core_opening,labour_core_year,labour_core_bid_ranking,labour_core_import_cost,labour_core_seed_and_reservations,labour_core_skilled_ceiling,labour_core_substitute_wage,labour_core_supply_schedule`).
The agent economy (on by default) calls it every year (`sim/economy/year_labour.py`) and keeps its state
in its record, so the core sets the wage every employer is quoted. The core's people by trade are the economy's
(`sim/economy/api.py`, `people_by_trade`); `sim/labour/labour_allocation.py` holds only the society's labour need by
trade (household demand through the recipe graph, which the spin-up follows until the agent economy has opened) and
the farming technique, and moves no one between trades.

What stays outside the core is what it is given and does not decide: the trade registry (`trades.py`, filled from
data), the households' saved fields and yearly call, the subsistence staple, the hire command's premium and the
recipe need shares. Each was a complaint, now closed (`Complaints/closed/`), and none is left open here; a new gap
is filed in `Complaints/`.
