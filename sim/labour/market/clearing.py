"""Step 1 of the year: per (trade, area), set the market wage and share the hours among employers (DESIGN.md)."""
import math
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from sim.constants import declare

from . import asks, layoffs
from .asks import VACANCY_SHARE_THRESHOLD, WAGE_UPDATE_PER_ROUND  # noqa: F401  (declared beside the rounds that use them)
from .applications import hire_through_rounds
from .import_cost import ImportCosts
from .premium import training_premium
from .trades import fallback_trade
from .records import Bid, Clearing, MarketState, YearInputs
from .scarcity import short_run_ceiling

WAGE_SHARE_CLOSED_PER_YEAR = declare(
    "WAGE_SHARE_CLOSED_PER_YEAR", 0.3, kind="temporary_heuristic", unit="share of the gap per year",
    source=None, confidence="D",
    why="How much of the gap between last year's new-hire wage and a higher clearing point closes in a year (an offer "
        "only rises, as Eurace's WAGE_OFFER does, Firm_update_wage_offer in Labour/Firm_Employer_Functions.c). A lower "
        "clearing point is reached at once for new hires: held hours keep their contract (contracted_wage) and the ask "
        "falls by asks.py, so the downward stickiness lives there. The speed is not fitted.")

MATCHING_EFFICIENCY_PER_YEAR = declare(
    "MATCHING_EFFICIENCY_PER_YEAR", 2.0, kind="temporary_heuristic", unit="per year",
    source=None, confidence="D",
    why="Rate at which vacancies and searchers meet. Used only by the founder's recruitable estimate in "
        "labour_market_api.py; the clearing itself hires by applications.py. Set so a slack market fills nearly all of "
        "a vacancy in a year while a tight one fills part; not fitted.")

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
    return target_for_demand(reservation, offered, [(bid.maximum_wage, bid.hours) for bid in bids])


def target_for_demand(reservation: float, offered: float, demand: Sequence[Tuple[float, float]]) -> float:
    """`clearing_target` over (maximum wage, hours) pairs, the form a Clearing keeps its demand in."""
    live = sorted(((cap, hours) for cap, hours in demand if cap >= reservation), reverse=True)
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


def share_closed(last: float, goal: float) -> float:
    """The share of the gap to `goal` that closes in a year for the wage new hires clear at: a rise is gradual
    (`WAGE_SHARE_CLOSED_PER_YEAR`, an offer only rises step by step); a fall is the whole gap, since the workers' own ask
    (asks.py) already falls gradually and held hours do not follow it down (contracted_wage)."""
    return WAGE_SHARE_CLOSED_PER_YEAR if goal > last else 1.0


def market_wage(last: Optional[float], reservation: float, offered: float, bids: Sequence[Bid]) -> float:
    """The wage new hires clear at (not the wage of hours already held)."""
    if offered <= 0.0:
        return last if last is not None else max((bid.maximum_wage for bid in bids), default=reservation)
    if not bids:    # hours on offer and nobody wanting them: new hires would clear at the ask
        return reservation
    target = clearing_target(reservation, offered, bids)
    wage = target if last is None else last + share_closed(last, target) * pressure(last, reservation, offered, bids) * (target - last)
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


def eligible_bids(bids: Sequence[Bid], wage: float, contracts: Optional[Dict[str, float]] = None
                  ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float]]:
    """Per employer: hours wanted at the market wage (for new hires), the wage paid them, the standing, and the hours
    wanted for hours already held. A held hour keeps its contract (`contracts`, the wage last year's hours were hired at),
    so a bid is still wanted for them while its maximum covers the lower of the contract and the market wage: a raised
    market wage lays off no one whose contract the employer can still pay (Eurace lays off by need alone,
    Firm_set_labour_market_actions in Labour/Firm_Employer_Functions.c, never by the offer rising)."""
    contracts = contracts or {}
    wanted: Dict[str, float] = {}
    paid: Dict[str, float] = {}
    ranks: Dict[str, float] = {}
    wanted_to_keep: Dict[str, float] = {}
    for bid in sorted(bids, key=lambda each: (each.employer, each.maximum_wage, each.hours)):
        if bid.maximum_wage >= min(wage, contracts.get(bid.employer, wage)):
            wanted_to_keep[bid.employer] = wanted_to_keep.get(bid.employer, 0.0) + bid.hours
            ranks[bid.employer] = max(ranks.get(bid.employer, 0.0), standing(bid.maximum_wage, bid.pay_premium))
        if bid.maximum_wage < wage:
            continue
        wanted[bid.employer] = wanted.get(bid.employer, 0.0) + bid.hours
        paid[bid.employer] = max(paid.get(bid.employer, 0.0),
                                 min(bid.maximum_wage, wage * (1.0 + bid.pay_premium)))
    return wanted, paid, ranks, wanted_to_keep


def contracted_wage(contract: Optional[float], market: float, best_maximum: float) -> float:
    """The wage an employer pays an hour it already held: the wage the hour was hired at, however the market wage has
    moved since (Eurace fixes a worker's wage at the offer when hired, Firm_hire_workers / Household_receive_wage in
    Labour/), so long as the employer can still pay it: no more than its best maximum. With no contract, the market wage."""
    return min(market if contract is None else contract, best_maximum)


def pay_by_employer(kept: Dict[str, float], hired: Dict[str, float], contracts: Dict[str, float],
                    new_paid: Dict[str, float], market: float, best_maximum: Dict[str, float]
                    ) -> Tuple[Dict[str, float], float]:
    """(the wage an hour paid, per employer; the hours-weighted mean over everyone hired). An employer's kept hours are
    paid their contract, the rest of its hours the wage the new hires cleared at (`new_paid`). The mean is the trade's
    reported market wage; with no one hired it is the wage new hires would clear at (`market`)."""
    paid: Dict[str, float] = {}
    bill = 0.0
    for employer, hours in sorted(hired.items()):
        held = min(kept.get(employer, 0.0), hours)
        held_pay = contracted_wage(contracts.get(employer), market, best_maximum.get(employer, math.inf))
        wage_paid = (held * held_pay + (hours - held) * new_paid.get(employer, market)) / hours if hours > 0.0 else market
        paid[employer] = wage_paid
        bill += hours * wage_paid
    total = sum(hired.values())
    return paid, (bill / total if total > 0.0 else market)


def retain(wanted: Dict[str, float], previous: Dict[str, float], offered: float) -> Dict[str, float]:
    # an employer lays off the hours it holds beyond those it wants (layoffs.hours_to_lay_off, after Eurace Firm_send_redundancies)
    kept = {employer: hours if layoffs.hours_to_lay_off(previous.get(employer, 0.0), hours) > 0.0
            else previous.get(employer, 0.0) for employer, hours in wanted.items()}
    total = sum(kept.values())
    scale = offered / total if total > offered else 1.0
    return {employer: hours * scale for employer, hours in kept.items()}


def pay_groups(ranks: Dict[str, float], employers: Sequence[str]) -> List[List[str]]:
    """Employers grouped by standing, highest first, names sorted within a group."""
    groups: Dict[float, List[str]] = {}
    for employer in sorted(employers):
        groups.setdefault(ranks[employer], []).append(employer)
    return [groups[wage] for wage in sorted(groups, reverse=True)]


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
        return min(reservation, ceiling), None
    goal = supply_target(reservation, supply, bids)

    def moved(wage_now):
        offered = supply(max(wage_now, reservation))
        gap = 1.0 if offered <= 0.0 else min(1.0, abs(sum(bid.hours for bid in bids if bid.maximum_wage >= max(wage_now, reservation)) - offered) / offered)
        return wage_now + gap * (min(goal, ceiling) - wage_now)

    wage = goal if last is None else last + share_closed(last, moved(last)) * (moved(last) - last)
    if any(bid.maximum_wage >= reservation for bid in bids):
        wage = max(wage, reservation)
    wage = min(wage, max(max(bid.maximum_wage for bid in bids), reservation), ceiling)
    return wage, (wage if last is not None and wage < last else moved(wage))     # a wage that fell has taken the whole move


def offer_ceilings(bids: Sequence[Bid], wage: float, paid: Dict[str, float], market_ceiling: float) -> Dict[str, float]:
    """The most each employer offers in the year's rounds: what its least valuable wanted hour (the lowest tranche
    whose maximum covers the wage) is worth to it, no more than the market's ceiling (`short_run_ceiling`) and the clearing point (past it the hours wanted fall away), and never
    under the offer it starts at."""
    lowest: Dict[str, float] = {}
    for bid in bids:
        if bid.maximum_wage >= wage:
            lowest[bid.employer] = min(lowest.get(bid.employer, math.inf), bid.maximum_wage)
    return {employer: max(min(cap, market_ceiling), paid.get(employer, 0.0)) for employer, cap in lowest.items()}


def clear_one(state: MarketState, inputs: YearInputs, trade: str, area: str, bids: Sequence[Bid],
              import_costs: Optional[ImportCosts] = None) -> Clearing:
    spec = inputs.trades[trade]
    workers = sum(state.workers.get(area, {}).get(trade, []))
    full = workers * inputs.hours_per_worker_year
    share_at = inputs.hours_share_at.get((trade, area))
    base_reservation = reservation_wage(inputs, area, spec.fatality_risk_per_year)
    lowest = inputs.ask_floor_per_worker_year.get(area, 0.0) / max(inputs.hours_per_worker_year, 1e-12)
    reservation = max(base_reservation * asks.scale_of(state, area, trade), lowest, unskilled_option(state, inputs, area, trade))
    last = state.entry_wages.get(area, {}).get(trade)
    if last is None:
        last = state.wages.get(area, {}).get(trade)
    long_run = max(trained_substitute_wage(state, inputs, area, trade), reservation)
    supply = (import_costs or ImportCosts(state, inputs)).supply(area, trade) if bids else None
    imported, fetched_share = supply if supply is not None else (None, 0.0)
    # this year's wage may pass the long-run cost (trainees take years to arrive); what entrants expect stays at it
    ceiling = short_run_ceiling(long_run, reservation, spec.training_years, bids, imported, fetched_share)
    if share_at is None or full <= 0.0:
        offered = full
        wage = min(market_wage(last, reservation, offered, bids), ceiling)
        goal = clearing_target(reservation, offered, bids) if offered > 0.0 and bids else wage
        # heading: the wage moves toward the clearing target by the same imbalance scaling `market_wage` applies, so
        # the expectation it feeds is continuous across balance (Complaint 664)
        # (a wage that fell has taken the whole move already, so it is its own heading)
        fell = last is not None and wage < last
        target = (wage + pressure(wage, reservation, offered, bids) * (min(clearing_target(reservation, offered, bids), ceiling) - wage)
                  if offered > 0.0 and bids and not fell else wage)
    else:
        wage, target = _wage_with_supply(last, reservation, ceiling, lambda wage_now: full * share_at(wage_now), bids)
        goal = supply_target(reservation, lambda wage_now: full * share_at(wage_now), bids) if bids else wage
        offered = full * share_at(wage)
    target = min(target, long_run) if target is not None else None
    contracts = state.contract_wages.get(area, {}).get(trade, {})
    wanted, paid, ranks, wanted_to_keep = eligible_bids(bids, wage, contracts)
    previous = state.hired_hours.get(area, {}).get(trade, {})
    kept = retain(wanted_to_keep, previous, offered) if offered > 0.0 else {}
    hired = {employer: kept.get(employer, 0.0) for employer in ranks} if offered > 0.0 else {employer: 0.0 for employer in wanted}
    wanted = {employer: wanted.get(employer, 0.0) for employer in hired}
    best_maximum: Dict[str, float] = {}
    for bid in bids:
        best_maximum[bid.employer] = max(best_maximum.get(bid.employer, 0.0), bid.maximum_wage)
    if offered > 0.0:
        held_pay = {employer: contracted_wage(contracts.get(employer), wage, best_maximum.get(employer, math.inf))
                    for employer in hired}
        # searchers apply to employers' offers round by round (applications.py); the unretained hours start as the pool
        taken = hire_through_rounds(hired, kept, wanted, paid, held_pay, max(0.0, offered - sum(hired.values())),
                                    reservation, lowest, ceilings=offer_ceilings(bids, wage, paid, min(ceiling, goal)))
        # the new-hire wage is what the hours taken on were paid, the offers having risen round by round
        new_hours = sum(taken.values())
        if new_hours > 0.0:
            wage = sum(hours * paid[employer] for employer, hours in taken.items()) / new_hours
        before = dict(hired)
        poach(hired, wanted, ranks)
        # hours an employer lost to a better payer leave the kept and the new alike
        kept = {employer: hours * min(1.0, hired[employer] / before[employer]) if before.get(employer, 0.0) > 0.0 else 0.0
                for employer, hours in kept.items()}
    hired = {employer: hours for employer, hours in hired.items() if hours > 0.0}
    paid_each, reported = pay_by_employer(kept, hired, contracts, paid, wage, best_maximum)
    state.entry_wages.setdefault(area, {})[trade] = wage
    state.wages.setdefault(area, {})[trade] = reported
    state.contract_wages.setdefault(area, {})[trade] = dict(paid_each)
    asks.record(state, area, trade, offered, sum(wanted.values()), wage, base_reservation, lowest)
    state.hired_hours.setdefault(area, {})[trade] = dict(hired)
    total = sum(hired.values())
    average = sum(hours * paid_each[employer] for employer, hours in hired.items()) / total if total > 0.0 else wage
    return Clearing(trade=trade, area=area, wage=reported, hours_offered=offered, hours_wanted=sum(wanted.values()),
                    hours_hired=total, hired_by_employer=hired, paid_by_employer=dict(paid_each), average_wage=average,
                    target_wage=target, new_hire_wage=wage, hours_held=full,
                    demand=tuple((bid.maximum_wage, bid.hours) for bid in bids))


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
