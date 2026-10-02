"""The year's labour market: producers and other employers bid for hours, cohorts offer them, each
(trade, labour area) clears at a sticky wage and the wages are paid at once.

Workers move between trades on their tile toward unfilled hours, a share of the idle a year, and
between each trade and unskilled work toward pay above what the trade's training costs, so the
workforce follows the wages with a lag (training is not yet a delay here).
"""
import dataclasses
import math
from typing import Dict, List, Sequence, Tuple

from sim.constants import declare

from sim.world.wages import CAREER_YEARS

from . import households, labour, settlement
from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .market_memory import KEY_SEPARATOR, market_key
from .setup import LABOUR_AREA_PREFIX
from .types import LabourBid, LabourOffer
from .year_ledger import YearLedger

TRADE_MOBILITY_SHARE_PER_YEAR = declare(
    "TRADE_MOBILITY_SHARE_PER_YEAR", 0.2, kind="temporary_heuristic",
    unit="share of a trade's idle workers who move to trades with unfilled hours in a year, and of a "
         "trade's workforce that enters or leaves it in a year when its pay is twice or under what its "
         "training costs",
    source=None, confidence="D",
    why="People without work drift to where employers want hands, slowed by skill, custom and "
        "guilds. The share stands in for the training and mobility model in sim/world/labour_market.py, "
        "which the economy does not yet drive.")


def subsistence_cost_by_tile(setup, record, view) -> Dict[str, float]:
    """Money a person needs a year for the floors of every need, at last year's prices on each tile."""
    costs = {}
    for tile in sorted({cohort.tile for cohort in record.cohorts.values()}):
        costs[tile] = households.subsistence_cost_per_person(households.need_prices(setup.basket_for(tile), view, tile))
    return costs


def outside_option_by_tile(setup, record, view) -> Dict[str, float]:
    """What a worker must earn in a year to keep the people he supports at their floors, per tile: the
    classical floor under wages. Hours nobody hires go to the household's own plot (households_own.py)."""
    floors = subsistence_cost_by_tile(setup, record, view)
    people: Dict[str, float] = {}
    working: Dict[str, float] = {}
    for cohort in record.cohorts.values():
        people[cohort.tile] = people.get(cohort.tile, 0.0) + cohort.people
        working[cohort.tile] = working.get(cohort.tile, 0.0) + cohort.working_people
    return {tile: floor * (people[tile] / working[tile] if working.get(tile) else 1.0)
            for tile, floor in floors.items()}


def labour_offers(setup, record, view, subsistence_by_tile) -> List[LabourOffer]:
    danger = {trade: spec.fatality_risk_per_year for trade, spec in setup.trades.items()}
    offers: List[LabourOffer] = []
    working_by_tile: Dict[str, float] = {}
    for cohort in record.cohorts.values():
        working_by_tile[cohort.tile] = working_by_tile.get(cohort.tile, 0.0) + cohort.working_people
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        tile_working = working_by_tile.get(cohort.tile, 0.0)
        share = cohort.working_people / tile_working if tile_working > 0.0 else 0.0
        workers = {trade: count * share for trade, count in record.workforce.get(cohort.tile, {}).items()}
        offers.extend(households.labour_offers(cohort, workers, view, subsistence_by_tile.get(cohort.tile, 0.0),
                                               setup.working_hours_per_year, danger))
    premiums = {trade: trade_premium(setup, trade) for trade in {offer.trade for offer in offers}}
    return [dataclasses.replace(offer, reservation_wage=offer.reservation_wage * (1.0 + premiums[offer.trade]))
            if premiums[offer.trade] > 0.0 else offer for offer in offers]


def trade_premium(setup, trade) -> float:
    """What a trade's training years add to the pay a worker asks, as a share: the years of income
    given up to learn it, repaid over a working life (labour.training_premium) at the family's own
    time preference, since the family pays for training by going without, not by borrowing."""
    spec = setup.trades.get(trade)
    if spec is None or spec.training_years <= 0.0:
        return 0.0
    return labour.training_premium(spec.training_years, HOUSEHOLD_TIME_PREFERENCE, CAREER_YEARS)


def national_wages(setup, record) -> Dict[str, float]:
    """Each trade's wage over its labour markets, weighted by the hours each usually hires; a trade
    nobody hires is paid the unskilled wage plus what its training costs (trade_premium)."""
    totals: Dict[str, Tuple[float, float]] = {}
    for key, wage in record.memory.wages.items():
        hours = record.memory.hours_hired.get(key, 0.0)
        if hours > 0.0:
            trade = key.split(KEY_SEPARATOR, 1)[0]
            value, total_hours = totals.get(trade, (0.0, 0.0))
            totals[trade] = (value + wage * hours, total_hours + hours)
    wages = {trade: value / total_hours for trade, (value, total_hours) in sorted(totals.items())}
    unskilled = wages.get(setup.unskilled_trade)
    if unskilled is not None:
        for trade in sorted(setup.trades):
            if trade not in wages:
                wages[trade] = unskilled * (1.0 + trade_premium(setup, trade))
    return wages


def clear_labour(setup, record, bids: Sequence[LabourBid], offers: Sequence[LabourOffer],
                 ledger: YearLedger) -> None:
    grouped: Dict[Tuple[str, str], Tuple[List[LabourBid], List[LabourOffer]]] = {}
    for bid in bids:
        grouped.setdefault((bid.trade, bid.area), ([], []))[0].append(bid)
    for offer in offers:
        grouped.setdefault((offer.trade, offer.area), ([], []))[1].append(offer)
    memory = record.memory
    for key in set(memory.hours_hired) - {market_key(trade, area) for trade, area in grouped}:
        memory.note_hours(key, 0.0)
    for (trade, area), (trade_bids, trade_offers) in sorted(grouped.items()):
        key = market_key(trade, area)
        result = labour.clear(trade_bids, trade_offers, trade, area, setup.currency_id, memory.wages.get(key))
        done = settlement.settle_labour(record.book, result)
        ledger.note_postings(done.postings, "wages")
        ledger.note_labour(result)
        memory.note_hours(key, result.hours_hired)
        if result.wage > 0.0:
            memory.wages[key] = result.wage


def move_workers(setup, record, ledger: YearLedger) -> None:
    """Idle workers in a trade move toward the trades on their tile that had unfilled hours."""
    hours = setup.working_hours_per_year
    idle: Dict[Tuple[str, str], float] = {}
    vacant: Dict[Tuple[str, str], float] = {}
    for result in ledger.labour_results:
        tile = result.area[len(LABOUR_AREA_PREFIX):]
        idle[(tile, result.trade)] = result.idle_hours / hours
        vacant[(tile, result.trade)] = result.vacant_hours / hours
    for tile, workforce in sorted(record.workforce.items()):
        wanted = {trade: count for (place, trade), count in vacant.items() if place == tile and count > 0.0}
        total_wanted = math.fsum(wanted.values())
        if total_wanted <= 0.0:
            continue
        movers = math.fsum(min(idle.get((tile, trade), 0.0), workforce.get(trade, 0.0))
                           for trade in workforce) * TRADE_MOBILITY_SHARE_PER_YEAR
        movers = min(movers, total_wanted)
        if movers <= 0.0:
            continue
        idle_total = math.fsum(min(idle.get((tile, trade), 0.0), workforce.get(trade, 0.0)) for trade in workforce)
        for trade in sorted(workforce):
            leaving = min(idle.get((tile, trade), 0.0), workforce[trade])
            if idle_total > 0.0:
                workforce[trade] -= movers * leaving / idle_total
        for trade, count in sorted(wanted.items()):
            workforce[trade] = workforce.get(trade, 0.0) + movers * count / total_wanted


def follow_pay(setup, record, ledger: YearLedger) -> None:
    """Workers move between each trade and the tile's unskilled trade until the trade pays the unskilled
    wage plus what its training costs (trade_premium): a trade paying more draws people in, one paying
    less loses them, in proportion to the gap and the trade's size."""
    unskilled = setup.unskilled_trade
    wages = {}
    for result in ledger.labour_results:
        if result.wage > 0.0:
            wages[(result.area[len(LABOUR_AREA_PREFIX):], result.trade)] = result.wage
    for tile, workforce in sorted(record.workforce.items()):
        unskilled_wage = wages.get((tile, unskilled))
        if unskilled_wage is None:
            continue
        for trade in sorted(workforce):
            wage = wages.get((tile, trade))
            if trade == unskilled or wage is None:
                continue
            gap = wage / (unskilled_wage * (1.0 + trade_premium(setup, trade))) - 1.0
            change = TRADE_MOBILITY_SHARE_PER_YEAR * workforce[trade] * max(-1.0, min(1.0, gap))
            change = max(-workforce[trade], min(change, workforce.get(unskilled, 0.0)))
            workforce[trade] += change
            workforce[unskilled] = workforce.get(unskilled, 0.0) - change
