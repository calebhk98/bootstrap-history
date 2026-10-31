"""The workforce after the hidden spin-up years, trimmed to the hours employers will actually want.

The opening staffs a trade by the hours producers need at full capacity (labour_state.opening_workforce).
Producers then work well under capacity, so a trade holds more people than it has jobs and, glutted, pays
the floor. The spin-up's few years cannot thin it (a trade's people leave slowly). Here each skilled trade
is cut to the hours producers plan for the coming year plus what other buyers hired in the last;
the people cut take up the unskilled trade, as the opening gives them to it.
"""
from typing import Dict, Mapping, Tuple

from sim.labour.api import bound_by_hirers, fallback_trade

from . import carriage_hours, opening_placement, producers, state_budget, workforce_version
from .labour_state import core_trades, plot_trade, producers_hours_needed, seeded_hours
from .market_memory import market_key


def expected_hours(setup, record, view) -> Dict[Tuple[str, str], float]:
    """Hours wanted next year by (labour area, trade): what each producer plans to bid, plus what the
    employers other than producers hired last year (the state and other buyers show up there)."""
    wanted: Dict[Tuple[str, str], float] = {}
    for producer_id, producer in sorted(record.producers.items()):
        recipe = setup.recipes[producer.recipe_id]
        plan = producers.plan(producer, recipe, view, record.book.balance(producer_id, setup.currency_id))
        for bid in plan.labour_bids:
            wanted[(bid.area, bid.trade)] = wanted.get((bid.area, bid.trade), 0.0) + bid.hours
    return add_others_hired(wanted, record.workforce.workers, record.hours_hired_by_others)


def add_others_hired(wanted: Mapping[Tuple[str, str], float], workers: Mapping[str, Mapping[str, object]],
                     hired_by_others: Mapping[str, float]) -> Dict[Tuple[str, str], float]:
    """`wanted` plus, for each trade the workers hold in an area, the hours the other employers hired there."""
    total = dict(wanted)
    for area, by_trade in workers.items():
        for trade in by_trade:
            total[(area, trade)] = total.get((area, trade), 0.0) + hired_by_others.get(market_key(trade, area), 0.0)
    return total


def trim_to_expected_hours(setup, record, view) -> None:
    """Cut every non-fallback trade holding more people than the hours wanted need; the rest join the
    fallback trade in the same ability bands."""
    fallback = fallback_trade(core_trades(setup))
    wanted = hours_kept(seeded_hours(setup, producers_hours_needed(setup, record)),
                        expected_hours(setup, record, view), state_hours(setup, record, view),
                        carriage_plan_hours(setup, record))
    hours_per_worker = record.opening_sold_hours_by_area or record.opening_sold_hours_per_worker or setup.working_hours_per_year     # as the opening staffed them
    trim_people(record.workforce, wanted, fallback, hours_per_worker, setup.working_hours_per_year)
    send_idle_to_plots(record.workforce, wanted, fallback, plot_trade(setup), hours_per_worker, setup.working_hours_per_year)


def state_hours(setup, record, view) -> Dict[Tuple[str, str], float]:
    """Hours the state's wage budget bids by (labour area, trade)."""
    return hours_by_area_and_trade(state_budget.wage_labour_bids(setup, record, view, record.state_budget.wage_budget))


def carriage_plan_hours(setup, record) -> Dict[Tuple[str, str], float]:
    """Hours the merchants' carriage crews are planned to bid by (labour area, trade): the carriers' own demand."""
    return hours_by_area_and_trade(carriage_hours.bids(setup, record))


def hours_by_area_and_trade(bids) -> Dict[Tuple[str, str], float]:
    """The bids' hours summed by (labour area, trade)."""
    hours: Dict[Tuple[str, str], float] = {}
    for bid in bids:
        hours[(bid.area, bid.trade)] = hours.get((bid.area, bid.trade), 0.0) + bid.hours
    return hours


def hours_kept(seeds_by_area: Mapping[str, Mapping[str, float]], wanted: Mapping[Tuple[str, str], float],
               state_wanted: Mapping[Tuple[str, str], float],
               carriage_wanted: Mapping[Tuple[str, str], float]) -> Dict[Tuple[str, str], float]:
    """`wanted` with each seeded trade (the society's need, for trades no producer's runs staff) kept at its seed
    only as far as its hirers' hours go: what producers plan and others hired, the state's bids and the hours the
    merchants' carriage crews are planned to bid. The people
    beyond that are not kept (Complaint 556)."""
    kept = dict(wanted)
    for area, seeds in seeds_by_area.items():
        hirers = {trade: wanted.get((area, trade), 0.0) + state_wanted.get((area, trade), 0.0)
                  + carriage_wanted.get((area, trade), 0.0) for trade in seeds}
        for trade, hours in bound_by_hirers(seeds, hirers).items():
            kept[(area, trade)] = max(kept.get((area, trade), 0.0), hours)
    return kept


def trim_people(state, wanted: Dict[Tuple[str, str], float], fallback: str, working_hours_per_year,
                default_hours: float = 0.0) -> None:
    """Cut workers, then trainees (who would graduate into the trade and refill it), until each trade holds
    no more people than its wanted hours need. `working_hours_per_year` is the hours a person sells, one figure or one per
    area (`default_hours` for an area it does not name)."""
    workforce_version.bump(state)
    for area, by_trade in state.workers.items():
        for trade, bands in by_trade.items():
            people = sum(bands)
            keep = wanted.get((area, trade), 0.0) / opening_placement.hours_per_worker_in(area, working_hours_per_year, default_hours)
            if trade == fallback or people <= keep:
                continue
            factor = keep / people
            freed = [count * (1.0 - factor) for count in bands]
            bands[:] = [count * factor for count in bands]
            _give_to_fallback(by_trade, fallback, freed)
    for area, by_trade in state.trainees.items():
        workers = state.workers.setdefault(area, {})
        for trade, cohorts in by_trade.items():
            enrolled = sum(sum(cohort[1]) for cohort in cohorts)
            room = max(0.0, wanted.get((area, trade), 0.0) / opening_placement.hours_per_worker_in(area, working_hours_per_year, default_hours)
                       - sum(workers.get(trade, [])))
            if trade == fallback or enrolled <= room:
                continue
            factor = room / enrolled
            for cohort in cohorts:
                _give_to_fallback(workers, fallback, [count * (1.0 - factor) for count in cohort[1]])
                cohort[1] = [count * factor for count in cohort[1]]


def send_idle_to_plots(state, wanted: Dict[Tuple[str, str], float], fallback: str, idle_trade: str,
                       working_hours_per_year, default_hours: float = 0.0) -> None:
    """The fallback trade keeps the people its wanted hours need; the rest, whom no employer wants, work their own
    plots as `idle_trade`."""
    workforce_version.bump(state)
    if not idle_trade or idle_trade == fallback:
        return
    for area, by_trade in state.workers.items():
        bands = by_trade.get(fallback)
        people = sum(bands) if bands else 0.0
        keep = wanted.get((area, fallback), 0.0) / opening_placement.hours_per_worker_in(area, working_hours_per_year, default_hours)
        if people <= keep or people <= 0.0:
            continue
        factor = keep / people
        freed = [count * (1.0 - factor) for count in bands]
        bands[:] = [count * factor for count in bands]
        _give_to_fallback(by_trade, idle_trade, freed)


def _give_to_fallback(by_trade, fallback: str, freed) -> None:
    home = by_trade.setdefault(fallback, [0.0] * len(freed))
    home[:] = [count + back for count, back in zip(home, freed)]
