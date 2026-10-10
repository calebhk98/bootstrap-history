"""The year's labour market: producers and other employers bid for hours, cohorts' workers offer them, and
the labour core (`sim.labour.api`) sets each (trade, labour area) wage, moves people between trades and
tiles, trains and replaces them. The economy settles the wages it reports, at once.

The training premium of a trade is not written here: it is the wage at which enough able people choose
the trade (sim/labour/market/DESIGN.md).
"""
import dataclasses
from typing import Dict, List, Mapping, Sequence, Tuple

from sim.labour.api import CAREER_YEARS, people_in, run_labour_year

from . import households, labour, settlement
from .households_cohort import VALUE_OF_LIFE_YEARS_OF_INCOME
from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .labour_ask_floor import mean_floor_per_hour
from .labour_bids import sloped_bids
from .labour_state import core_trades, give_back, hold_back, mirror_wages, people_by_trade
from .market_memory import market_key
from .setup import labour_area
from .types import Fill, LabourBid, LabourOffer, LabourResult
from .year_ledger import YearLedger


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
    """Each cohort's share of the tile's workers in each trade, as hours at the reservation wage."""
    danger = {trade: spec.fatality_risk_per_year for trade, spec in setup.trades.items()}
    offers: List[LabourOffer] = []
    working_by_tile: Dict[str, float] = {}
    for cohort in record.cohorts.values():
        working_by_tile[cohort.tile] = working_by_tile.get(cohort.tile, 0.0) + cohort.working_people
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        tile_working = working_by_tile.get(cohort.tile, 0.0)
        share = cohort.working_people / tile_working if tile_working > 0.0 else 0.0
        area = labour_area(cohort.tile)
        workers = {trade: count * share for trade, count in people_by_trade(record.workforce, area).items()}
        offers.extend(households.labour_offers(cohort, workers, view, subsistence_by_tile.get(cohort.tile, 0.0),
                                               setup.working_hours_per_year, danger))
    return offers


def trade_premium(setup, trade) -> float:
    """What a trade's training years add to the pay a worker asks, as a share: the years of income
    given up to learn it, repaid over a working life (labour.training_premium) at the family's own
    time preference, since the family pays for training by going without, not by borrowing. Quotes
    of a wage for a trade nobody has bid for yet use it; the clearing does not."""
    spec = setup.trades.get(trade)
    if spec is None or spec.training_years <= 0.0:
        return 0.0
    return labour.training_premium(spec.training_years, HOUSEHOLD_TIME_PREFERENCE, CAREER_YEARS)


def held_share_by_area(everyone: Sequence[LabourOffer], offered: Sequence[LabourOffer]) -> Dict[str, float]:
    """The share of each area's offered hours households kept back (offers cut by withhold_hours)."""
    total: Dict[str, float] = {}
    cut: Dict[str, float] = {}
    for offer in everyone:
        total[offer.area] = total.get(offer.area, 0.0) + offer.hours
    for offer in offered:
        cut[offer.area] = cut.get(offer.area, 0.0) + offer.hours
    return {area: max(0.0, 1.0 - cut.get(area, 0.0) / hours) for area, hours in total.items() if hours > 0.0}


def _result(clearing, currency: str, offers: Sequence[LabourOffer]) -> LabourResult:
    """A core clearing as the economy settles it: employers buy the hours hired, the workers whose
    hours were offered sell them in proportion to what each offered."""
    wage = clearing.average_wage
    fills = [Fill(employer, clearing.trade, clearing.area, "", hours, wage, "buy")
             for employer, hours in sorted(clearing.hired_by_employer.items()) if hours > 0.0]
    offered = sum(offer.hours for offer in offers)
    if offered > 0.0 and clearing.hours_hired > 0.0:
        fills.extend(Fill(offer.worker, clearing.trade, clearing.area, "", clearing.hours_hired * offer.hours / offered,
                          wage, "sell") for offer in sorted(offers, key=lambda each: each.worker) if offer.hours > 0.0)
    return LabourResult(trade=clearing.trade, area=clearing.area, currency=currency, wage=wage,
                        hours_hired=clearing.hours_hired, vacant_hours=clearing.vacant_hours,
                        idle_hours=clearing.idle_hours, fills=tuple(fills))


def clear_labour(setup, record, bids: Sequence[LabourBid], offers: Sequence[LabourOffer], ledger: YearLedger,
                 context, held_share: Mapping[str, float] = None) -> None:
    """Run the core's year on the record's workforce: wages, hires, training, entry, switching and
    migration. Then settle each market's wages. `context` is the core's inputs without trades and bids
    (labour_inputs.labour_context). `held_share` is the share of each area's workers whose hours
    households keep for their own plots: the market does not see them this year."""
    core_bids = sloped_bids(bids)
    ledger.wage_floor_per_hour = mean_floor_per_hour(
        context.ask_floor_per_worker_year,
        {area: people_in(record.workforce, area) for area in context.ask_floor_per_worker_year},
        context.hours_per_worker_year)
    inputs = dataclasses.replace(context, trades=core_trades(setup, {bid.trade for bid in core_bids}),
                                 bids=core_bids)
    seen, held = hold_back(record.workforce, held_share or {})
    record.workforce, report = run_labour_year(seen, inputs)
    give_back(record.workforce, held)
    by_market: Dict[Tuple[str, str], List[LabourOffer]] = {}
    for offer in offers:
        by_market.setdefault((offer.trade, offer.area), []).append(offer)
    record.hours_hired = {}
    record.hours_idle = {}
    for clearing in sorted(report.clearings, key=lambda each: (each.trade, each.area)):
        result = _result(clearing, setup.currency_id, by_market.get((clearing.trade, clearing.area), ()))
        done = settlement.settle_labour(record.book, result)
        ledger.note_postings(done.postings, "wages")
        ledger.note_labour(result, done.postings)
        record.hours_hired[market_key(clearing.trade, clearing.area)] = clearing.hours_hired
        record.hours_idle[market_key(clearing.trade, clearing.area)] = clearing.idle_hours
    mirror_wages(record.memory.wages, record.workforce)
