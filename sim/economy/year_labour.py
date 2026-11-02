"""The year's labour market: producers and other employers bid for hours, cohorts' workers offer them, and
the labour core (`sim.labour.api`) sets each (trade, labour area) wage, hires, moves people between trades and
tiles, trains and replaces them. The economy then pays every hour hired in a market the one wage the core reports
for it (`Clearing.wage`), and the workers who offered them share the receipts by hours sold.
"""
import dataclasses
from typing import Dict, List, Sequence, Tuple

from sim.labour.api import CAREER_YEARS, people_in, run_labour_year, wages

from . import households, households_work, settlement
from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .labour_ask_floor import mean_floor_per_hour
from .labour_bids import sloped_bids
from .labour_state import core_trades, mirror_wages, people_by_trade
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


def labour_offers(setup, record, view, subsistence_by_tile, levy_hours_per_worker: float = 0.0,
                  levied_tiles: Sequence[str] = ()) -> List[LabourOffer]:
    """Each cohort's share of the tile's workers in each trade, as hours at the reservation wage. The hours a state
    levies (`levy_hours_per_worker`) come off the hours of the workers on the tiles it holds (`levied_tiles`) before
    they are offered, never below nothing for an offer."""
    danger = {trade: spec.fatality_risk_per_year for trade, spec in setup.trades.items()}
    levied = set(levied_tiles)
    offers: List[LabourOffer] = []
    working_by_tile: Dict[str, float] = {}
    for cohort in record.cohorts.values():
        working_by_tile[cohort.tile] = working_by_tile.get(cohort.tile, 0.0) + cohort.working_people
    people_by_area: Dict[str, Dict[str, float]] = {}
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        tile_working = working_by_tile.get(cohort.tile, 0.0)
        share = cohort.working_people / tile_working if tile_working > 0.0 else 0.0
        area = labour_area(cohort.tile)
        if area not in people_by_area:
            people_by_area[area] = people_by_trade(record.labour.workforce, area)
        workers = {trade: count * share for trade, count in people_by_area[area].items()}
        made = households.labour_offers(cohort, workers, view, subsistence_by_tile.get(cohort.tile, 0.0),
                                        setup.working_hours_per_year, danger)
        if cohort.tile in levied and levy_hours_per_worker > 0.0:
            kept = max(0.0, 1.0 - levy_hours_per_worker / setup.working_hours_per_year)
            made = [dataclasses.replace(offer, hours=offer.hours * kept) for offer in made]
        offers.extend(made)
    return offers


def trade_premium(setup, trade) -> float:
    """What a trade's training years add to the pay a worker asks, as a share over the unskilled wage: the core's
    training premium (a multiple, labour/market/premium.py) less one, at the family's own time preference, since the
    family pays for training by going without, not by borrowing. Quotes of a wage for a trade nobody has bid for yet
    use it; the clearing reads the same multiple at the same rate (`labour_context`)."""
    spec = setup.trades.get(trade)
    if spec is None or spec.training_years <= 0.0:
        return 0.0
    return wages.training_premium(spec.training_years, HOUSEHOLD_TIME_PREFERENCE, CAREER_YEARS) - 1.0


def _result(clearing, currency: str, offers: Sequence[LabourOffer]) -> LabourResult:
    """A core clearing as the economy settles it: employers buy the hours hired, the workers whose
    hours were offered sell them in proportion to what each offered, all at the market's one wage."""
    wage = clearing.wage
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
                 context, supply=None):
    """Run the core's year on the record's workforce: wages, hires, training, entry, switching and migration;
    returns the core's report. Then settle each market. `context` is the core's inputs without trades and bids
    (labour_inputs.labour_context). With `supply` (labour_supply.HourSupply) the hours each market sells are the hours
    its offers hold, rising with the wage, and the offers settled are those sold at the wage the market cleared at
    (`supply.sold`); without it the core sells every worker's whole year and `offers` are the sellers."""
    core_bids = sloped_bids(bids)
    ledger.wage_floor_per_hour = mean_floor_per_hour(
        context.ask_floor_per_worker_year,
        {area: people_in(record.labour.workforce, area) for area in context.ask_floor_per_worker_year},
        context.hours_per_worker_year)
    inputs = dataclasses.replace(context, trades=core_trades(setup, {bid.trade for bid in core_bids}),
                                 bids=core_bids, hours_sold_at=supply.schedules() if supply is not None else None)
    record.labour.workforce, report = run_labour_year(record.labour.workforce, inputs, owned=True)
    by_market: Dict[Tuple[str, str], List[LabourOffer]] = {}
    if supply is not None:
        offers = supply.settle({(clearing.trade, clearing.area): clearing.wage for clearing in report.clearings})
    for offer in offers:
        by_market.setdefault((offer.trade, offer.area), []).append(offer)
    record.labour.hours_idle = {}
    for clearing in sorted(report.clearings, key=lambda each: (each.trade, each.area)):
        key = market_key(clearing.trade, clearing.area)
        result = _result(clearing, setup.currency_id, by_market.get((clearing.trade, clearing.area), ()))
        done = settlement.settle_labour(record.book, result)
        ledger.note_postings(done.postings, "wages")
        ledger.note_labour(result, done.postings)
        record.labour.hours_idle[key] = clearing.idle_hours
        if clearing.hours_hired + clearing.idle_hours > 0.0:
            record.labour.sold_share_expected[key] = households_work.smoothed_sold_share(
                record.labour.sold_share_expected.get(key, 1.0), households_work.sold_share(clearing.hours_hired, clearing.idle_hours))
    mirror_wages(record.memory.wages, record.labour.workforce)
    return report
