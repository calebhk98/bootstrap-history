"""The clearing rule for the year's labour markets: each (trade, area) pays one wage, last year's moved a share of the way
to the wage where the hours offered meet the hours employers want (`wage_step.symmetric_wage`), and the hours go to the
bids that want them at that wage (`hires_at_wage`). No rounds of search, no ask that drifts: a market at its clearing
wage stays there, and where the least an hour is sold for rises above the wage, the wage climbs to it by the same share. It stands where `clearing.clear_all` stands (YearInputs.clearing) and writes what that writes."""
from typing import Dict, List, Optional, Sequence, Set, Tuple

from . import clearing
from .hires_at_wage import by_employer, hires_at_wage, ranks_of, wanted_at_wage
from .import_cost import ImportCosts
from .records import EmployerHoursBid, LabourClearing, MarketState, YearInputs
from .reservation import reservation_wage
from .scarcity import short_run_ceiling
from .trades import fallback_trade
from .unskilled_reach import reservation_with_unskilled_option
from .wage_step import symmetric_wage


def wage_floor(inputs: YearInputs, area: str, risk: float) -> Optional[float]:
    """The lowest wage an hour of a trade is sold at in an area: the area's stated floor (what the household needs less
    what its own plot gives) with the trade's risk priced as the reservation wage prices it; where the area states no
    floor, the reservation wage. None where the area has no outside option to hold a market on."""
    reservation = reservation_wage(inputs, area, risk)
    stated = inputs.ask_floor_per_worker_year.get(area)
    if reservation is None or stated is None:
        return reservation
    danger = 1.0 + max(0.0, risk) * inputs.value_of_life_years_of_income
    return stated / max(inputs.hours_per_worker_year, 1e-12) * danger


def clear_one_at_one_wage(state: MarketState, inputs: YearInputs, trade: str, area: str, bids: Sequence[EmployerHoursBid],
                          import_costs: ImportCosts) -> Optional[LabourClearing]:
    """The market of a trade in an area for the year, the state written; None where the area has no outside option."""
    spec = inputs.trades[trade]
    own_floor = wage_floor(inputs, area, spec.fatality_risk_per_year)
    if own_floor is None:
        return None
    held = sum(state.workers.get(area, {}).get(trade, [])) * inputs.hours_per_worker_year
    schedule = inputs.sold_schedule(trade, area)
    hours_sold = schedule if schedule is not None else (lambda wage: held)
    option = clearing.unskilled_option(import_costs.wages, inputs, area, trade)
    jobs = 0.0 if option is None else import_costs.jobs_at(area, fallback_trade(inputs.trades), option)
    floor = reservation_with_unskilled_option(own_floor, option, jobs, import_costs.everyone(area, trade))
    substitute = clearing.trained_substitute_wage(import_costs.wages, inputs, area, trade)
    long_run = floor if substitute is None else max(substitute, floor)
    fetched = import_costs.supply(area, trade) if bids else None
    imported, fetched_share = fetched if fetched is not None else (None, 0.0)
    ceiling = short_run_ceiling(long_run, floor, spec.training_years, bids, imported, fetched_share)
    goal = min(clearing.supply_target(floor, hours_sold, bids), ceiling) if bids else floor
    wage = symmetric_wage(state.wages.get(area, {}).get(trade), goal, floor, ceiling)
    offered = hours_sold(wage)
    ordered = sorted(bids, key=lambda bid: (bid.employer, bid.maximum_wage, bid.hours))
    employers = [bid.employer for bid in ordered]
    caps = [bid.maximum_wage for bid in ordered]
    wanted_by_bid = wanted_at_wage(wage, min(floor, wage), caps, [bid.hours for bid in ordered])     # a wage still climbing to its floor is the wage paid
    wanted, standing = ranks_of(employers, caps, wanted_by_bid)
    hired = {employer: 0.0 for employer in wanted}
    hired.update(by_employer(employers, hires_at_wage(offered, wanted_by_bid)))
    hired = {employer: hired[employer] for employer in wanted}
    clearing.poach(hired, wanted, standing)
    hired = {employer: hours for employer, hours in hired.items() if hours > 0.0}
    state.wages.setdefault(area, {})[trade] = wage
    state.hired_hours.setdefault(area, {})[trade] = dict(hired)
    return LabourClearing(trade=trade, area=area, wage=wage, hours_offered=offered, hours_wanted=sum(wanted.values()),
                          hours_hired=sum(hired.values()), hired_by_employer=hired, target_wage=min(goal, long_run),
                          hours_held=held, demand=tuple((bid.maximum_wage, bid.hours) for bid in bids))


def clear_all_at_one_wage(state: MarketState, inputs: YearInputs) -> Sequence[LabourClearing]:
    """Every market of the year in sorted (trade, area) order: the markets with a bid and those with workers."""
    bids_by_market: Dict[Tuple[str, str], List[EmployerHoursBid]] = {}
    for bid in inputs.bids:
        if bid.hours > 0.0 and bid.trade in inputs.trades:
            bids_by_market.setdefault((bid.trade, bid.area), []).append(bid)
    markets: Set[Tuple[str, str]] = set(bids_by_market)
    for area, by_trade in state.workers.items():
        markets.update((trade, area) for trade, bands in by_trade.items() if sum(bands) > 0.0 and trade in inputs.trades)
    import_costs = ImportCosts(state, inputs)
    cleared = [clear_one_at_one_wage(state, inputs, trade, area, bids_by_market.get((trade, area), []), import_costs)
               for trade, area in sorted(markets)]
    return [each for each in cleared if each is not None]
