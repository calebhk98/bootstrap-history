"""Step 1 of the year: per (trade, area), set the market wage and share the hours among employers (DESIGN.md)."""
import math
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from sim.constants import declare

from . import asks
from .import_cost import ImportCosts
from .premium import training_premium
from .trades import fallback_trade
from .records import Bid, Clearing, MarketState, YearInputs
from .scarcity import short_run_ceiling

WAGE_SHARE_CLOSED_PER_YEAR = declare(
    "WAGE_SHARE_CLOSED_PER_YEAR", 0.3, kind="temporary_heuristic", unit="share of the gap per year",
    source=None, confidence="D",
    why="How much of the gap between last year's market wage and the clearing point closes in a year. Wages "
        "were sticky (custom, contracts); the speed is not fitted.")

WAGE_UPDATE_PER_ROUND = declare(
    "WAGE_UPDATE_PER_ROUND", 0.02, kind="temporary_heuristic", unit="share of the wage added per round of unfilled vacancies",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace's WAGE_UPDATE (default 0.02 in Labour/model.xml): an employer with vacancies left raises its offer by "
        "this share each round (Firm_update_wage_offer, Labour/Firm_Employer_Functions.c). Not fitted.")

VACANCY_SHARE_THRESHOLD = declare(
    "VACANCY_SHARE_THRESHOLD", 0.05, kind="temporary_heuristic", unit="share of the hours wanted left unfilled",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace raises the offer only when vacancies exceed MIN_VACANCY (default 2 posts; a count, not a share). "
        "A market has no post count, so the threshold is the share of wanted hours the supply cannot fill. Not fitted.")

MATCHING_EFFICIENCY_PER_YEAR = declare(
    "MATCHING_EFFICIENCY_PER_YEAR", 2.0, kind="temporary_heuristic", unit="per year",
    source=None, confidence="D",
    why="Rate at which vacancies and searchers meet. Set so a slack market fills nearly all of a vacancy in a "
        "year while a tight one fills part; not fitted.")

FIRM_LABOUR_SUPPLY_ELASTICITY = declare(
    "FIRM_LABOUR_SUPPLY_ELASTICITY", 2.0, kind="temporary_heuristic", unit="elasticity of recruits to pay",
    source=None, confidence="C",
    why="How strongly an employer's pay over its rivals' raises how fast it recruits; the monopsony "
        "literature puts the firm-level elasticity of labour supply at a few.")

MATCHING_SEARCHER_ELASTICITY = declare(
    "MATCHING_SEARCHER_ELASTICITY", 0.5, kind="temporary_heuristic", unit="elasticity of fill to searchers per vacancy",
    source=None, confidence="C",
    why="How much more of a vacancy fills when more searchers chase it; matching-function estimates put the "
        "elasticity of hires to searchers near one half.")

ON_THE_JOB_SEARCH_SHARE = declare(
    "ON_THE_JOB_SEARCH_SHARE", 0.1, kind="temporary_heuristic", unit="share of a lower payer's hours per year",
    source=None, confidence="D",
    why="The most of a lower-paying employer's hours a better payer can draw off in a year, by workers who "
        "look while employed; not fitted.")


SUPPLY_SOLVE_STEPS = 60      # a numerical bound: the bisection for the wage a rising supply meets a step of demand at


def reservation_wage(inputs: YearInputs, area: str, risk: float) -> float:
    """What an hour must pay: the outside option per hour plus the priced risk of the trade."""
    floor = inputs.subsistence_per_worker_year.get(area, 0.0) / max(inputs.hours_per_worker_year, 1e-12)
    return floor * (1.0 + risk * inputs.value_of_life_years_of_income)


def unskilled_option(state: MarketState, inputs: YearInputs, area: str, trade: str) -> float:
    """What a skilled worker can always earn instead: the unskilled wage the area paid last year, taken
    straight up with no retraining, so no trade quotes below it."""
    fallback = fallback_trade(inputs.trades)
    if trade == fallback:
        return 0.0
    return state.wages.get(area, {}).get(fallback) or 0.0


def trained_substitute_wage(state: MarketState, inputs: YearInputs, area: str, trade: str) -> float:
    """The most an hour of a trade can command where hands are few: what it takes to train a substitute. A
    person who trains goes the trade's training years unpaid, so the trade pays the unskilled wage times the
    training premium (premium.training_premium: the multiple that leaves a trainee indifferent) and the risk
    of the work priced as in the reservation wage. A trade needing no training is capped at the unskilled
    wage itself (hands move in at once). Unlimited only for the unskilled trade itself."""
    spec = inputs.trades[trade]
    fallback = fallback_trade(inputs.trades)
    if trade == fallback:
        return math.inf
    unskilled = max(state.wages.get(area, {}).get(fallback) or 0.0, reservation_wage(inputs, area, 0.0))
    premium = training_premium(spec.training_years, inputs.discount_rate, inputs.career_years)
    return unskilled * premium * (1.0 + spec.fatality_risk_per_year * inputs.value_of_life_years_of_income)


def clearing_target(reservation: float, offered: float, bids: Sequence[Bid]) -> float:
    """Price where the offered hours (all at `reservation`) meet bids taken highest maximum first."""
    live = sorted(((bid.maximum_wage, bid.hours) for bid in bids if bid.maximum_wage >= reservation), reverse=True)
    taken = 0.0
    for index, (cap, hours) in enumerate(live):
        taken += hours
        if taken >= offered:
            beyond = live[index + 1][0] if taken <= offered and index + 1 < len(live) else (
                cap if taken > offered else -math.inf)
            return (max(reservation, beyond) + cap) / 2.0
    return reservation


def supply_target(reservation: float, supply: Callable[[float], float], bids: Sequence[Bid]) -> float:
    """The lowest wage at which the hours sold (`supply`, rising in the wage) cover the hours employers want at it
    (bids taken highest maximum first): the reservation wage where they do already. Within a step of demand it is
    the wage the supply reaches that step's hours at, so a small excess of hours moves the wage a little, where hours
    all offered at the reservation wage move it all the way."""
    caps = sorted({bid.maximum_wage for bid in bids if bid.maximum_wage >= reservation})       # lowest first
    edges = [reservation] + caps
    for index in range(len(edges)):      # the demand on (edges[index], edges[index + 1]] is that of the bids at or above edges[index + 1]
        low = edges[index]
        high = edges[index + 1] if index + 1 < len(edges) else None
        wanted = math.fsum(bid.hours for bid in bids if bid.maximum_wage >= (high if high is not None else math.inf))
        if high is None:
            return low           # above every cap nobody wants an hour, so the wage cannot be above the highest cap
        if supply(high) < wanted:
            continue
        if supply(low) >= wanted:
            return low
        for _step in range(SUPPLY_SOLVE_STEPS):
            middle = (low + high) / 2.0
            if supply(middle) >= wanted:
                high = middle
            else:
                low = middle
        return high
    return reservation


def pressure(last: float, reservation: float, offered: float, bids: Sequence[Bid]) -> float:
    """How far the market is from balance at last year's wage: the share of the offered hours that employers
    leave unwanted or want beyond them, capped at one. The target jumps from the ask to the bids' maxima as
    wanted hours cross the offered ones, so a step that closed a fixed share of the gap would swing the wage
    by that jump for a sliver of imbalance (a cobweb, Complaint 651); scaled by the imbalance it is continuous."""
    at = max(last, reservation)
    wanted = sum(bid.hours for bid in bids if bid.maximum_wage >= at)
    return min(1.0, abs(wanted - offered) / offered)


def vacancy_raise(wage: float, target: float, wanted: float, offered: float) -> float:
    """The wage after the rounds of a year in which employers' vacancies stayed open: raised by WAGE_UPDATE_PER_ROUND each
    round, as Firm_update_wage_offer (Eurace, Labour/Firm_Employer_Functions.c) raises WAGE_OFFER while VACANCIES exceed
    MIN_VACANCY, but not past the clearing `target` (Eurace's firms stop by budget; here the clearing point is the bound,
    so the offer cannot overshoot) and never below `wage`. `wanted` and `offered` are hours at last year's wage."""
    if wanted <= 0.0 or (wanted - offered) / wanted <= VACANCY_SHARE_THRESHOLD:
        return wage
    raised = wage * (1.0 + WAGE_UPDATE_PER_ROUND) ** asks.SEARCH_ROUNDS_PER_YEAR
    return max(wage, min(raised, target))


def market_wage(last: Optional[float], reservation: float, offered: float, bids: Sequence[Bid]) -> float:
    if offered <= 0.0:
        return last if last is not None else max((bid.maximum_wage for bid in bids), default=reservation)
    if not bids:    # hours on offer and nobody wanting them: the quote drifts down to the ask
        return reservation if last is None else last + WAGE_SHARE_CLOSED_PER_YEAR * (reservation - last)
    target = clearing_target(reservation, offered, bids)
    wage = target if last is None else last + WAGE_SHARE_CLOSED_PER_YEAR * pressure(last, reservation, offered, bids) * (target - last)
    if last is not None:     # the sticky move above, then the offer's raise while vacancies stay open
        wanted = sum(bid.hours for bid in bids if bid.maximum_wage >= max(last, reservation))
        wage = vacancy_raise(wage, target, wanted, offered)
    if any(bid.maximum_wage >= reservation for bid in bids):
        wage = max(wage, reservation)
    # no employer can pay above its maximum: a wage that lags above every maximum falls to the best of them
    return min(wage, max(max(bid.maximum_wage for bid in bids), reservation))


def premium_factor(paid: float, rival_paid: float) -> float:
    return (paid / rival_paid) ** FIRM_LABOUR_SUPPLY_ELASTICITY if rival_paid > 0.0 else 1.0


def on_the_job_loss_share(paid: float, rival_paid: float) -> float:
    """Share of an employer's hours a strictly higher rival draws off in a year; none when it pays as much."""
    if rival_paid <= paid:
        return 0.0
    return min(1.0, ON_THE_JOB_SEARCH_SHARE * premium_factor(rival_paid, paid))


def standing(maximum_wage: float, pay_premium: float) -> float:
    """How strongly an employer draws hours: the most an hour is worth to it, raised by the premium it offers.
    Employers are ranked, and hours move between them, by this and not by the wage paid, which the ceiling caps
    (Complaint 667). Stands in for the entrant's own means of drawing hours (advertising, a signing cost) that no
    mechanism yet supplies; the incumbent's edge is the matching friction and `ON_THE_JOB_SEARCH_SHARE` alone."""
    return maximum_wage * (1.0 + pay_premium)


def eligible_bids(bids: Sequence[Bid], wage: float) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """Hours wanted, the wage paid and the standing, per employer, among bids that can afford the market wage."""
    wanted: Dict[str, float] = {}
    paid: Dict[str, float] = {}
    ranks: Dict[str, float] = {}
    for bid in sorted(bids, key=lambda each: (each.employer, each.maximum_wage, each.hours)):
        if bid.maximum_wage < wage:
            continue
        wanted[bid.employer] = wanted.get(bid.employer, 0.0) + bid.hours
        paid[bid.employer] = max(paid.get(bid.employer, 0.0),
                                 min(bid.maximum_wage, wage * (1.0 + bid.pay_premium)))
        ranks[bid.employer] = max(ranks.get(bid.employer, 0.0), standing(bid.maximum_wage, bid.pay_premium))
    return wanted, paid, ranks


def retain(wanted: Dict[str, float], previous: Dict[str, float], offered: float) -> Dict[str, float]:
    kept = {employer: min(hours, previous.get(employer, 0.0)) for employer, hours in wanted.items()}
    total = sum(kept.values())
    scale = offered / total if total > offered else 1.0
    return {employer: hours * scale for employer, hours in kept.items()}


def pay_groups(ranks: Dict[str, float], employers: Sequence[str]) -> List[List[str]]:
    """Employers grouped by standing, highest first, names sorted within a group."""
    groups: Dict[float, List[str]] = {}
    for employer in sorted(employers):
        groups.setdefault(ranks[employer], []).append(employer)
    return [groups[wage] for wage in sorted(groups, reverse=True)]


def hire_new(hired: Dict[str, float], wanted: Dict[str, float], paid: Dict[str, float], offered: float,
             wage: float) -> None:
    """Employers in descending standing (`paid` here is the standing) take new hours from the unretained pool, limited by matching friction."""
    pool = max(0.0, offered - sum(hired.values()))
    unserved = sum(wanted[employer] - hired[employer] for employer in wanted)
    for group in pay_groups(paid, list(wanted)):
        needs = {employer: wanted[employer] - hired[employer] for employer in group}
        vacancies = sum(needs.values()) if unserved <= 0.0 else unserved
        searchers_per_vacancy = max(0.0, pool) / vacancies if vacancies > 0.0 else 0.0
        rate = MATCHING_EFFICIENCY_PER_YEAR * searchers_per_vacancy ** MATCHING_SEARCHER_ELASTICITY
        takes = {employer: needs[employer] * (1.0 - math.exp(-rate * premium_factor(paid[employer], wage)))
                 for employer in group}
        total = sum(takes.values())
        scale = pool / total if total > pool and total > 0.0 else 1.0
        for employer in group:
            hired[employer] += takes[employer] * scale
        pool = max(0.0, offered - sum(hired.values()))
        unserved -= sum(needs.values())


def poach(hired: Dict[str, float], wanted: Dict[str, float], paid: Dict[str, float]) -> None:
    """Short employers (`paid` here is the standing) draw hours off strictly lower ones, in proportion to what each can give."""
    for group in pay_groups(paid, list(wanted)):
        for employer in group:
            short = wanted[employer] - hired[employer]
            capacity = {other: hired[other] * on_the_job_loss_share(paid[other], paid[employer])
                        for other in wanted if paid[other] < paid[employer] and hired[other] > 0.0}
            total = sum(capacity.values())
            if short <= 0.0 or total <= 0.0:
                continue
            moved = min(short, total)
            for other in sorted(capacity):
                hired[other] -= moved * capacity[other] / total
            hired[employer] += moved


def _wage_with_supply(last, reservation, ceiling, supply, bids):
    """(wage, heading wage) of a market whose hours sold rise with the wage: the wage moves toward where the supply
    meets the demand, by the imbalance at last year's wage, as `market_wage` does for hours all offered at the ask."""
    if not bids:
        wage = reservation if last is None else last + WAGE_SHARE_CLOSED_PER_YEAR * (reservation - last)
        return min(wage, ceiling), None
    goal = supply_target(reservation, supply, bids)

    def moved(wage_now):
        offered = supply(max(wage_now, reservation))
        gap = 1.0 if offered <= 0.0 else min(1.0, abs(sum(bid.hours for bid in bids if bid.maximum_wage >= max(wage_now, reservation)) - offered) / offered)
        return wage_now + gap * (min(goal, ceiling) - wage_now)

    wage = goal if last is None else last + WAGE_SHARE_CLOSED_PER_YEAR * (moved(last) - last)
    if last is not None:     # then the offer's raise while vacancies stay open (`vacancy_raise`)
        at = max(last, reservation)
        wage = vacancy_raise(wage, min(goal, ceiling), sum(bid.hours for bid in bids if bid.maximum_wage >= at), supply(at))
    if any(bid.maximum_wage >= reservation for bid in bids):
        wage = max(wage, reservation)
    wage = min(wage, max(max(bid.maximum_wage for bid in bids), reservation), ceiling)
    return wage, moved(wage)


def clear_one(state: MarketState, inputs: YearInputs, trade: str, area: str, bids: Sequence[Bid],
              import_costs: Optional[ImportCosts] = None) -> Clearing:
    spec = inputs.trades[trade]
    workers = sum(state.workers.get(area, {}).get(trade, []))
    full = workers * inputs.hours_per_worker_year
    share_at = inputs.hours_share_at.get((trade, area))
    base_reservation = reservation_wage(inputs, area, spec.fatality_risk_per_year)
    lowest = inputs.ask_floor_per_worker_year.get(area, 0.0) / max(inputs.hours_per_worker_year, 1e-12)
    reservation = max(base_reservation * asks.scale_of(state, area, trade), lowest, unskilled_option(state, inputs, area, trade))
    last = state.wages.get(area, {}).get(trade)
    long_run = max(trained_substitute_wage(state, inputs, area, trade), reservation)
    imported = (import_costs or ImportCosts(state, inputs)).wage(area, trade) if bids else None
    # this year's wage may pass the long-run cost (trainees take years to arrive); what entrants expect stays at it
    ceiling = short_run_ceiling(long_run, reservation, spec.training_years, bids, imported)
    if share_at is None or full <= 0.0:
        offered = full
        wage = min(market_wage(last, reservation, offered, bids), ceiling)
        # heading: the wage moves toward the clearing target by the same imbalance scaling `market_wage` applies, so
        # the expectation it feeds is continuous across balance (Complaint 664)
        target = (wage + pressure(wage, reservation, offered, bids) * (min(clearing_target(reservation, offered, bids), ceiling) - wage)
                  if offered > 0.0 and bids else wage)
    else:
        wage, target = _wage_with_supply(last, reservation, ceiling, lambda wage_now: full * share_at(wage_now), bids)
        offered = full * share_at(wage)
    target = min(target, long_run) if target is not None else None
    wanted, paid, ranks = eligible_bids(bids, wage)
    previous = state.hired_hours.get(area, {}).get(trade, {})
    hired = retain(wanted, previous, offered) if offered > 0.0 else {employer: 0.0 for employer in wanted}
    if offered > 0.0:
        hire_new(hired, wanted, ranks, offered, wage)
        poach(hired, wanted, ranks)
    hired = {employer: hours for employer, hours in hired.items() if hours > 0.0}
    state.wages.setdefault(area, {})[trade] = wage
    asks.record(state, area, trade, offered, sum(wanted.values()), wage, base_reservation, lowest)
    state.hired_hours.setdefault(area, {})[trade] = dict(hired)
    total = sum(hired.values())
    average = sum(hours * paid[employer] for employer, hours in hired.items()) / total if total > 0.0 else wage
    return Clearing(trade=trade, area=area, wage=wage, hours_offered=offered, hours_wanted=sum(wanted.values()),
                    hours_hired=total, hired_by_employer=hired,
                    paid_by_employer={employer: paid[employer] for employer in hired}, average_wage=average,
                    target_wage=target)


def clear_all(state: MarketState, inputs: YearInputs) -> List[Clearing]:
    bids_by_market: Dict[Tuple[str, str], List[Bid]] = {}
    for bid in inputs.bids:
        if bid.hours > 0.0 and bid.trade in inputs.trades:
            bids_by_market.setdefault((bid.trade, bid.area), []).append(bid)
    markets: Set[Tuple[str, str]] = set(bids_by_market)
    for area, by_trade in state.workers.items():
        markets.update((trade, area) for trade, bands in by_trade.items()
                       if sum(bands) > 0.0 and trade in inputs.trades)
    import_costs = ImportCosts(state, inputs)
    return [clear_one(state, inputs, trade, area, bids_by_market.get((trade, area), []), import_costs)
            for trade, area in sorted(markets)]
