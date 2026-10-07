"""Step 1 of the year: per (trade, area), set the market wage and share the hours among employers (DESIGN.md)."""
import math
from typing import Dict, List, Optional, Sequence, Set, Tuple

from sim.constants import declare
from .records import Bid, Clearing, MarketState, YearInputs

WAGE_SHARE_CLOSED_PER_YEAR = declare(
    "WAGE_SHARE_CLOSED_PER_YEAR", 0.3, kind="temporary_heuristic", unit="share of the gap per year",
    source=None, confidence="D",
    why="How much of the gap between last year's market wage and the clearing point closes in a year. Wages "
        "were sticky (custom, contracts); the speed is not fitted.")

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


def reservation_wage(inputs: YearInputs, area: str, risk: float) -> float:
    """What an hour must pay: the outside option per hour plus the priced risk of the trade."""
    floor = inputs.subsistence_per_worker_year.get(area, 0.0) / max(inputs.hours_per_worker_year, 1e-12)
    return floor * (1.0 + risk * inputs.value_of_life_years_of_income)


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


def market_wage(last: Optional[float], reservation: float, offered: float, bids: Sequence[Bid]) -> float:
    if offered <= 0.0 or not bids:
        return last if last is not None else max((bid.maximum_wage for bid in bids), default=reservation)
    target = clearing_target(reservation, offered, bids)
    wage = target if last is None else last + WAGE_SHARE_CLOSED_PER_YEAR * (target - last)
    if any(bid.maximum_wage >= reservation for bid in bids):
        wage = max(wage, reservation)
    return wage


def premium_factor(paid: float, rival_paid: float) -> float:
    return (paid / rival_paid) ** FIRM_LABOUR_SUPPLY_ELASTICITY if rival_paid > 0.0 else 1.0


def eligible_bids(bids: Sequence[Bid], wage: float) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Hours wanted and the wage paid, per employer, among bids that can afford the market wage."""
    wanted: Dict[str, float] = {}
    paid: Dict[str, float] = {}
    for bid in sorted(bids, key=lambda each: (each.employer, each.maximum_wage, each.hours)):
        if bid.maximum_wage < wage:
            continue
        wanted[bid.employer] = wanted.get(bid.employer, 0.0) + bid.hours
        paid[bid.employer] = max(paid.get(bid.employer, 0.0),
                                 min(bid.maximum_wage, wage * (1.0 + bid.pay_premium)))
    return wanted, paid


def retain(wanted: Dict[str, float], previous: Dict[str, float], offered: float) -> Dict[str, float]:
    kept = {employer: min(hours, previous.get(employer, 0.0)) for employer, hours in wanted.items()}
    total = sum(kept.values())
    scale = offered / total if total > offered else 1.0
    return {employer: hours * scale for employer, hours in kept.items()}


def pay_groups(paid: Dict[str, float], employers: Sequence[str]) -> List[List[str]]:
    """Employers grouped by wage paid, highest first, names sorted within a group."""
    groups: Dict[float, List[str]] = {}
    for employer in sorted(employers):
        groups.setdefault(paid[employer], []).append(employer)
    return [groups[wage] for wage in sorted(groups, reverse=True)]


def hire_new(hired: Dict[str, float], wanted: Dict[str, float], paid: Dict[str, float], offered: float,
             wage: float) -> None:
    """Employers in descending pay take new hours from the unretained pool, limited by matching friction."""
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
    """Short employers draw hours off strictly lower payers, in proportion to what each can give."""
    for group in pay_groups(paid, list(wanted)):
        for employer in group:
            short = wanted[employer] - hired[employer]
            capacity = {other: min(hired[other], ON_THE_JOB_SEARCH_SHARE * hired[other]
                                   * premium_factor(paid[employer], paid[other]))
                        for other in wanted if paid[other] < paid[employer] and hired[other] > 0.0}
            total = sum(capacity.values())
            if short <= 0.0 or total <= 0.0:
                continue
            moved = min(short, total)
            for other in sorted(capacity):
                hired[other] -= moved * capacity[other] / total
            hired[employer] += moved


def clear_one(state: MarketState, inputs: YearInputs, trade: str, area: str, bids: Sequence[Bid]) -> Clearing:
    spec = inputs.trades[trade]
    workers = sum(state.workers.get(area, {}).get(trade, []))
    offered = workers * inputs.hours_per_worker_year
    reservation = reservation_wage(inputs, area, spec.fatality_risk_per_year)
    last = state.wages.get(area, {}).get(trade)
    wage = market_wage(last, reservation, offered, bids)
    target = clearing_target(reservation, offered, bids) if offered > 0.0 and bids else wage
    wanted, paid = eligible_bids(bids, wage)
    previous = state.hired_hours.get(area, {}).get(trade, {})
    hired = retain(wanted, previous, offered) if offered > 0.0 else {employer: 0.0 for employer in wanted}
    if offered > 0.0:
        hire_new(hired, wanted, paid, offered, wage)
        poach(hired, wanted, paid)
    hired = {employer: hours for employer, hours in hired.items() if hours > 0.0}
    state.wages.setdefault(area, {})[trade] = wage
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
    return [clear_one(state, inputs, trade, area, bids_by_market.get((trade, area), []))
            for trade, area in sorted(markets)]
