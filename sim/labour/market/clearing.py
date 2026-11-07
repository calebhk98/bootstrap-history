"""Step 1 of the year: per (trade, area), set the market wage and share the hours among employers (DESIGN.md)."""
import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from sim.constants import declare

from . import asks, layoffs
from .applications import HireJob, hire_markets
from .import_cost import ImportCosts
from .premium import training_premium
from .reservation import reservation_wage
from .trades import fallback_trade
from .records import EmployerHoursBid, LabourClearing, MarketState, YearInputs
from .scarcity import short_run_ceiling

WAGE_SHARE_CLOSED_PER_YEAR = declare(
    "WAGE_SHARE_CLOSED_PER_YEAR", 0.3, kind="temporary_heuristic", unit="share of the gap per year",
    source=None, confidence="D",
    why="How much of the gap between last year's new-hire wage and a higher clearing point closes in a year (an offer "
        "only rises, as Eurace's WAGE_OFFER does, Firm_update_wage_offer in Labour/Firm_Employer_Functions.c). A lower "
        "clearing point is reached at once, and the ask falls by asks.py, so the downward stickiness lives there. "
        "Every hour of the trade in the area is paid the one wage. The speed is not fitted.")

FIRM_LABOUR_SUPPLY_ELASTICITY = declare(
    "FIRM_LABOUR_SUPPLY_ELASTICITY", 2.0, kind="temporary_heuristic", unit="elasticity of recruits to pay",
    source=None, confidence="C",
    why="How strongly an employer's pay over its rivals' raises how fast it recruits; the monopsony "
        "literature puts the firm-level elasticity of labour supply at a few.")

ON_THE_JOB_SEARCH_SHARE = declare(
    "ON_THE_JOB_SEARCH_SHARE", 0.1, kind="temporary_heuristic", unit="share of a lower payer's hours per year",
    source=None, confidence="D",
    why="The most of a lower-paying employer's hours a better payer can draw off in a year, by workers who "
        "look while employed; not fitted.")


SUPPLY_SOLVE_STEPS = 60      # a numerical bound: the bisection for the wage a rising supply meets a step of demand at


def ask_floor(inputs: YearInputs, area: str, base_reservation: float) -> float:
    """The lowest wage an ask falls to: the area's stated floor (what the household needs less its own plot), or,
    where none is stated, the reservation wage itself (an area with no stated floor gives no reason to sell under what
    an hour must pay)."""
    stated = inputs.ask_floor_per_worker_year.get(area)
    return base_reservation if stated is None else stated / max(inputs.hours_per_worker_year, 1e-12)


def unskilled_option(start_wages: Dict[str, Dict[str, float]], inputs: YearInputs, area: str, trade: str) -> Optional[float]:
    """What a skilled worker can always earn instead: the unskilled wage the area paid at the start of the year (not
    the live one, which the year's clearings rewrite in the order they run), taken straight up with no retraining,
    so no trade quotes below it. None for the unskilled trade itself and where the area paid none."""
    fallback = fallback_trade(inputs.trades)
    if trade == fallback:
        return None
    return start_wages.get(area, {}).get(fallback)


def trained_substitute_wage(start_wages: Dict[str, Dict[str, float]], inputs: YearInputs, area: str, trade: str) -> Optional[float]:
    """The most an hour of a trade can command where hands are few: what it takes to train a substitute. A
    person who trains goes the trade's training years unpaid, so the trade pays the unskilled wage times the
    training premium (premium.training_premium: the multiple that leaves a trainee indifferent) and the risk
    of the work priced as in the reservation wage. A trade needing no training is capped at the unskilled
    wage itself (hands move in at once). Unlimited only for the unskilled trade itself. The unskilled wage is the start
    of the year's; None where the area has neither it nor an outside option to stand in."""
    spec = inputs.trades[trade]
    fallback = fallback_trade(inputs.trades)
    if trade == fallback:
        return math.inf
    known = [wage for wage in (start_wages.get(area, {}).get(fallback), reservation_wage(inputs, area, 0.0)) if wage is not None]
    if not known:
        return None
    unskilled = max(known)
    premium = training_premium(spec.training_years, inputs.discount_rate, inputs.career_years)
    return unskilled * premium * (1.0 + spec.fatality_risk_per_year * inputs.value_of_life_years_of_income)


def clearing_target(reservation: float, offered: float, bids: Sequence[EmployerHoursBid]) -> float:
    """Price where the offered hours (all at `reservation`) meet bids taken highest maximum first."""
    return target_for_demand(reservation, offered, [(bid.maximum_wage, bid.hours) for bid in bids])


def target_for_demand(reservation: float, offered: float, demand: Sequence[Tuple[float, float]]) -> float:
    """`clearing_target` over (maximum wage, hours) pairs, the form a LabourClearing keeps its demand in."""
    live = sorted(((cap, hours) for cap, hours in demand if cap >= reservation), reverse=True)
    taken = 0.0
    for index, (cap, hours) in enumerate(live):
        taken += hours
        if taken >= offered:
            beyond = live[index + 1][0] if taken <= offered and index + 1 < len(live) else (
                cap if taken > offered else -math.inf)
            return (max(reservation, beyond) + cap) / 2.0
    return reservation


def supply_target(reservation: float, supply: Callable[[float], float], bids: Sequence[EmployerHoursBid]) -> float:
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


def pressure(last: float, reservation: float, offered: float, bids: Sequence[EmployerHoursBid]) -> float:
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
    (asks.py) already falls gradually."""
    return WAGE_SHARE_CLOSED_PER_YEAR if goal > last else 1.0


def market_wage(last: Optional[float], reservation: float, offered: float, bids: Sequence[EmployerHoursBid]) -> float:
    """The wage the market clears at, before the year's rounds of offers."""
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


def eligible_bids(bids: Sequence[EmployerHoursBid], wage: float) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """Per employer: hours wanted at the market wage, the wage it starts offering at, and its rank (its highest maximum
    wage). An employer whose maximum is under the wage wants none, held hours included."""
    wanted: Dict[str, float] = {}
    paid: Dict[str, float] = {}
    ranks: Dict[str, float] = {}
    for bid in sorted(bids, key=lambda each: (each.employer, each.maximum_wage, each.hours)):
        if bid.maximum_wage < wage:
            continue
        wanted[bid.employer] = wanted.get(bid.employer, 0.0) + bid.hours
        paid[bid.employer] = wage
        ranks[bid.employer] = max(ranks.get(bid.employer, 0.0), bid.maximum_wage)
    return wanted, paid, ranks


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
    """Short employers (`paid` here is the rank, the highest maximum wage) draw hours off strictly lower ones, in proportion to what each can give."""
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


def offer_ceilings(bids: Sequence[EmployerHoursBid], wage: float, paid: Dict[str, float], market_ceiling: float) -> Dict[str, float]:
    """The most each employer offers in the year's rounds: what its least valuable wanted hour (the lowest tranche
    whose maximum covers the wage) is worth to it, no more than the market's ceiling (`short_run_ceiling`) and the clearing point (past it the hours wanted fall away), and never
    under the offer it starts at."""
    lowest: Dict[str, float] = {}
    for bid in bids:
        if bid.maximum_wage >= wage:
            lowest[bid.employer] = min(lowest.get(bid.employer, math.inf), bid.maximum_wage)
    return {employer: max(min(cap, market_ceiling), paid.get(employer, 0.0)) for employer, cap in lowest.items()}


@dataclass
class _Pending:
    """A market cleared as far as its hiring rounds: everything `_finish` needs once `job` (None where the market offers no
    hours) has been run."""
    state: MarketState
    trade: str
    area: str
    bids: Sequence[EmployerHoursBid]
    wage: float
    paid: Dict[str, float]
    ranks: Dict[str, float]
    hired: Dict[str, float]
    wanted: Dict[str, float]
    offered: float
    sold_at: Optional[Callable[[float], float]]
    target: Optional[float]
    full: float
    base_reservation: float
    lowest: float
    job: Optional[HireJob]


def _prepare(state: MarketState, inputs: YearInputs, trade: str, area: str, bids: Sequence[EmployerHoursBid],
             import_costs: ImportCosts) -> Optional[_Pending]:
    """The market of a trade in an area up to its hiring rounds (the wage before them, the hours kept, the pool and the
    offers' ceilings); None where the area has no stated outside option to hold one on. Reads this market's own entries of
    the state and the year's start wages only, so markets can be prepared in any order."""
    spec = inputs.trades[trade]
    workers = sum(state.workers.get(area, {}).get(trade, []))
    full = workers * inputs.hours_per_worker_year
    sold_at = inputs.sold_schedule(trade, area)
    base_reservation = reservation_wage(inputs, area, spec.fatality_risk_per_year)
    if base_reservation is None:
        return None
    lowest = ask_floor(inputs, area, base_reservation)
    option = unskilled_option(import_costs.wages, inputs, area, trade)
    reservation = max(base_reservation * asks.scale_of(state, area, trade), lowest, 0.0 if option is None else option)
    last = state.wages.get(area, {}).get(trade)
    substitute = trained_substitute_wage(import_costs.wages, inputs, area, trade)
    long_run = reservation if substitute is None else max(substitute, reservation)
    supply = import_costs.supply(area, trade) if bids else None
    imported, fetched_share = supply if supply is not None else (None, 0.0)
    # this year's wage may pass the long-run cost (trainees take years to arrive); what entrants expect stays at it
    ceiling = short_run_ceiling(long_run, reservation, spec.training_years, bids, imported, fetched_share)
    if sold_at is None:
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
        wage, target = _wage_with_supply(last, reservation, ceiling, sold_at, bids)
        goal = supply_target(reservation, sold_at, bids) if bids else wage
        offered = sold_at(wage)
    target = min(target, long_run) if target is not None else None
    wanted, paid, ranks = eligible_bids(bids, wage)
    previous = state.hired_hours.get(area, {}).get(trade, {})
    kept = retain(wanted, previous, offered) if offered > 0.0 else {}
    hired = {employer: kept.get(employer, 0.0) for employer in ranks} if offered > 0.0 else {employer: 0.0 for employer in wanted}
    wanted = {employer: wanted.get(employer, 0.0) for employer in hired}
    job = None
    if offered > 0.0:
        # searchers apply to employers' offers round by round (applications.py); the unretained hours start as the pool
        job = HireJob(hired, kept, wanted, paid, max(0.0, offered - sum(hired.values())), reservation, lowest,
                      ceilings=offer_ceilings(bids, wage, paid, min(ceiling, goal)))
    return _Pending(state, trade, area, bids, wage, paid, ranks, hired, wanted, offered, sold_at, target, full,
                    base_reservation, lowest, job)


def _finish(pending: _Pending) -> LabourClearing:
    """The market after its hiring rounds: the wage the hours taken on were paid, poaching, and the state written."""
    state, area, trade, bids = pending.state, pending.area, pending.trade, pending.bids
    wage, offered, hired, wanted = pending.wage, pending.offered, pending.hired, pending.wanted
    if pending.job is not None:
        # the wage is what the hours taken on were paid, the offers having risen round by round; every hour of the trade
        # in the area, held or new, is paid it
        taken = pending.job.taken
        new_hours = sum(taken.values())
        if new_hours > 0.0:
            wage = sum(hours * pending.paid[employer] for employer, hours in taken.items()) / new_hours
        if pending.sold_at is not None:
            offered = pending.sold_at(wage)    # the hours sold are those the market settles at
        poach(hired, wanted, pending.ranks)
    hired = {employer: hours for employer, hours in hired.items() if hours > 0.0}
    state.wages.setdefault(area, {})[trade] = wage
    asks.record(state, area, trade, offered, sum(wanted.values()), wage, pending.base_reservation, pending.lowest)
    state.hired_hours.setdefault(area, {})[trade] = dict(hired)
    total = sum(hired.values())
    return LabourClearing(trade=trade, area=area, wage=wage, hours_offered=offered, hours_wanted=sum(wanted.values()),
                    hours_hired=total, hired_by_employer=hired,
                    target_wage=pending.target, hours_held=pending.full,
                    demand=tuple((bid.maximum_wage, bid.hours) for bid in bids))


def clear_one(state: MarketState, inputs: YearInputs, trade: str, area: str, bids: Sequence[EmployerHoursBid],
              import_costs: Optional[ImportCosts] = None) -> Optional[LabourClearing]:
    """The market of a trade in an area for the year; None where the area has no stated outside option to hold one on."""
    pending = _prepare(state, inputs, trade, area, bids, import_costs or ImportCosts(state, inputs))
    if pending is None:
        return None
    if pending.job is not None:
        hire_markets([pending.job])
    return _finish(pending)


def clear_all(state: MarketState, inputs: YearInputs) -> List[LabourClearing]:
    """Every market of the year, in sorted (trade, area) order: all prepared, the hiring rounds of all of them run in one
    kernel call, then each finished."""
    bids_by_market: Dict[Tuple[str, str], List[EmployerHoursBid]] = {}
    for bid in inputs.bids:
        if bid.hours > 0.0 and bid.trade in inputs.trades:
            bids_by_market.setdefault((bid.trade, bid.area), []).append(bid)
    markets: Set[Tuple[str, str]] = set(bids_by_market)
    for area, by_trade in state.workers.items():
        markets.update((trade, area) for trade, bands in by_trade.items()
                       if sum(bands) > 0.0 and trade in inputs.trades)
    import_costs = ImportCosts(state, inputs)
    prepared = [_prepare(state, inputs, trade, area, bids_by_market.get((trade, area), []), import_costs)
                for trade, area in sorted(markets)]
    pending = [each for each in prepared if each is not None]
    hire_markets([each.job for each in pending if each.job is not None])
    return [_finish(each) for each in pending]
