"""The year's labour market: producers and other employers bid for hours, cohorts offer them, each
(trade, labour area) clears at a sticky wage and the wages are paid at once.

Workers move between trades on their tile toward unfilled hours, a share of the idle a year, so the
workforce follows the wages with a lag (training is not yet a delay here).
"""
import dataclasses
import math
from typing import Dict, List, Sequence, Tuple

from sim.constants import declare

from sim.world.wages import CAREER_YEARS

from . import households, labour, settlement
from .market_memory import market_key
from .setup import LABOUR_AREA_PREFIX
from .types import LabourBid, LabourOffer
from .year_ledger import YearLedger

TRADE_MOBILITY_SHARE_PER_YEAR = declare(
    "TRADE_MOBILITY_SHARE_PER_YEAR", 0.2, kind="temporary_heuristic",
    unit="share of a trade's idle workers who move to trades with unfilled hours in a year",
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
    rate = view.interest_rate(setup.currency_id)
    premiums = {trade: trade_premium(setup, trade, rate) for trade in {offer.trade for offer in offers}}
    return [dataclasses.replace(offer, reservation_wage=offer.reservation_wage * (1.0 + premiums[offer.trade]))
            if premiums[offer.trade] > 0.0 else offer for offer in offers]


def trade_premium(setup, trade, rate) -> float:
    """What a trade's training years add to the pay a worker asks, as a share: the years of income
    given up to learn it, repaid over a working life at the going rate (labour.training_premium)."""
    spec = setup.trades.get(trade)
    if spec is None or spec.training_years <= 0.0:
        return 0.0
    return labour.training_premium(spec.training_years, rate, CAREER_YEARS)


def clear_labour(setup, record, bids: Sequence[LabourBid], offers: Sequence[LabourOffer],
                 ledger: YearLedger) -> None:
    grouped: Dict[Tuple[str, str], Tuple[List[LabourBid], List[LabourOffer]]] = {}
    for bid in bids:
        grouped.setdefault((bid.trade, bid.area), ([], []))[0].append(bid)
    for offer in offers:
        grouped.setdefault((offer.trade, offer.area), ([], []))[1].append(offer)
    memory = record.memory
    for (trade, area), (trade_bids, trade_offers) in sorted(grouped.items()):
        key = market_key(trade, area)
        result = labour.clear(trade_bids, trade_offers, trade, area, setup.currency_id, memory.wages.get(key))
        done = settlement.settle_labour(record.book, result)
        ledger.note_postings(done.postings, "wages")
        ledger.note_labour(result)
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
