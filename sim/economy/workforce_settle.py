"""The workforce after the hidden spin-up years, trimmed to the hours employers will actually want.

The opening staffs a trade by the hours producers need at full capacity (labour_state.opening_workforce).
Producers then work well under capacity, so a trade holds more people than it has jobs and, glutted, pays
the floor. The spin-up's few years cannot thin it (a trade's people leave slowly). Here each skilled trade
is cut to the hours producers plan for the coming year, or the hours hired in the last, whichever is more;
the people cut take up the unskilled trade, as the opening gives them to it.
"""
from typing import Dict, Tuple

from sim.labour.api import fallback_trade

from . import producers
from .labour_state import core_trades
from .market_memory import market_key


def expected_hours(setup, record, view) -> Dict[Tuple[str, str], float]:
    """Hours wanted next year by (labour area, trade): what each producer plans to bid, or what the
    market hired last year where that is more (state and other buyers show up there)."""
    wanted: Dict[Tuple[str, str], float] = {}
    for producer_id, producer in sorted(record.producers.items()):
        plan = producers.plan(producer, setup.recipes[producer.recipe_id], view,
                              record.book.balance(producer_id, setup.currency_id))
        for bid in plan.labour_bids:
            wanted[(bid.area, bid.trade)] = wanted.get((bid.area, bid.trade), 0.0) + bid.hours
    for area, by_trade in record.workforce.workers.items():
        for trade in by_trade:
            hired = record.hours_hired.get(market_key(trade, area), 0.0)
            wanted[(area, trade)] = max(wanted.get((area, trade), 0.0), hired)
    return wanted


def trim_to_expected_hours(setup, record, view) -> None:
    """Cut every non-fallback trade holding more people than the hours wanted need; the rest join the
    fallback trade in the same ability bands."""
    fallback = fallback_trade(core_trades(setup))
    trim_people(record.workforce, expected_hours(setup, record, view), fallback, setup.working_hours_per_year)


def trim_people(state, wanted: Dict[Tuple[str, str], float], fallback: str, working_hours_per_year: float) -> None:
    """Cut workers, then trainees (who would graduate into the trade and refill it), until each trade holds
    no more people than its wanted hours need."""
    for area, by_trade in state.workers.items():
        for trade, bands in by_trade.items():
            people = sum(bands)
            keep = wanted.get((area, trade), 0.0) / working_hours_per_year
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
            room = max(0.0, wanted.get((area, trade), 0.0) / working_hours_per_year - sum(workers.get(trade, [])))
            if trade == fallback or enrolled <= room:
                continue
            factor = room / enrolled
            for cohort in cohorts:
                _give_to_fallback(workers, fallback, [count * (1.0 - factor) for count in cohort[1]])
                cohort[1] = [count * factor for count in cohort[1]]


def _give_to_fallback(by_trade, fallback: str, freed) -> None:
    home = by_trade.setdefault(fallback, [0.0] * len(freed))
    home[:] = [count + back for count, back in zip(home, freed)]
