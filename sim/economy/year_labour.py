"""The year's labour market: producers and other employers bid for hours, cohorts' workers offer them, and
the labour core (`sim.labour.api`) sets each (trade, labour area) wage, hires, moves people between trades and
tiles, trains and replaces them. The economy then pays every hour hired in a market the one wage the core reports
for it (`LabourClearing.wage`), and the workers who offered them share the receipts by hours sold.
"""
import dataclasses
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from sim.labour.api import LabourBidTable, TrancheBids, people_in_areas, run_labour_year

from . import cohort_people, cohort_prime, household_work_year, households_basket, labour_settle_year
from .cohort_store import table_of
from .household_offer_kernels import sum_in_order_by_group
from .labour_ask_floor import mean_floor_per_hour
from .labour_bids import BID_TRANCHES, BID_VALUE_SPREAD
from .labour_idle_hours import note_idle_hours
from .labour_fills import fills_of, rows_from_clearings, rows_from_objects
from .labour_offer_rows import LabourOfferRows
from .labour_offers_write import write_cohort_offers
from .labour_results_table import LabourResults
from .labour_state import core_trades, mirror_wages, people_by_trade_matrix
from .setup import labour_area
from .types import Fill, LabourBid, LabourOffer, LabourResult
from .year_ledger import YearLedger


def subsistence_cost_by_tile(setup, record, view) -> Dict[str, float]:
    """Money a person needs a year for the floors of every need, at last year's prices on each tile: each cohort's own
    basket (its hearth's cooking fuel, its hired household work, ready-to-eat food where it has no hearth) at its tile's
    prices, averaged over the tile's people."""
    cohort_prime.prime_cohort_baskets(setup, record, view, False)
    store = table_of(record.cohorts)
    order = store.order()
    priced = {}                  # cohorts of one signature share one priced basket and its cost
    costs = []
    for signature in household_work_year.signatures_of(record, store, order, buying=False):
        if signature not in priced:
            priced[signature] = household_work_year.priced_basket_of(setup, view, signature[0], signature).subsistence_cost_per_person()
        costs.append(priced[signature])
    people = store.column("people")[order]
    tiles = np.ascontiguousarray(store.tile_numbers()[order])
    cost_sum = sum_in_order_by_group(tiles, len(store.names["tiles"]), np.array(costs, dtype=np.float64) * people).tolist()
    people_sum = sum_in_order_by_group(tiles, len(store.names["tiles"]), np.ascontiguousarray(people)).tolist()
    names = store.names["tiles"].name_list
    return {tile: (cost_sum[number] / people_sum[number] if people_sum[number] > 0.0 else
                   households_basket.tile_need_prices(setup, view, tile).subsistence_cost_per_person())
            for tile, number in sorted((names[number], number) for number in np.unique(tiles).tolist())}


def outside_option_by_tile(setup, record, view) -> Dict[str, float]:
    """What a worker must earn in a year to keep the people he supports at their floors, per tile: the
    classical floor under wages. Hours nobody hires go to the household's own plot (households_own.py)."""
    floors = subsistence_cost_by_tile(setup, record, view)
    store = table_of(record.cohorts)
    number_of = store.names["tiles"].numbers
    people = cohort_people.total_by_tile(store, "people").tolist()
    working = cohort_people.total_by_tile(store, "working_people").tolist()
    return {tile: floor * (people[number_of[tile]] / working[number_of[tile]] if working[number_of[tile]] else 1.0)
            for tile, floor in floors.items()}


def labour_offer_rows(setup, record, view, subsistence_by_tile, levy_hours_per_worker: float = 0.0,
                      levied_tiles: Sequence[str] = (), rows: Optional[LabourOfferRows] = None) -> LabourOfferRows:
    """Each cohort's share of the tile's workers in each trade, as hours at the reservation wage, appended to `rows` (a new set
    when none is given). The hours a state levies (`levy_hours_per_worker`) come off the hours of the workers on the tiles it holds
    (`levied_tiles`) before they are offered: the hours left are asked at a dearer wage, and a levy of the whole year leaves nothing
    to offer."""
    rows = LabourOfferRows() if rows is None else rows
    danger = {trade: spec.fatality_risk_per_year for trade, spec in setup.trades.items()}
    write_cohort_offers(rows, record.cohorts, lambda areas: people_by_trade_matrix(record.labour.workforce, areas), labour_area,
                        subsistence_by_tile, setup.working_hours_per_year, danger, levy_hours_per_worker, levied_tiles)
    return rows


def labour_offers(setup, record, view, subsistence_by_tile, levy_hours_per_worker: float = 0.0,
                  levied_tiles: Sequence[str] = ()) -> List[LabourOffer]:
    """`labour_offer_rows` as records (an edge: the opening's plans, a test)."""
    return list(labour_offer_rows(setup, record, view, subsistence_by_tile, levy_hours_per_worker, levied_tiles).objects())


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


def clearing_rows(clearings):
    """The cleared markets and the employers' hours as columns (labour_fills.py): from the core's `Clearings`, or from a plain
    list of `LabourClearing`s."""
    return rows_from_clearings(clearings) if hasattr(clearings, "slot_offsets") else rows_from_objects(clearings)


def clear_labour(setup, record, bids: Union[LabourBidTable, Sequence[LabourBid]], offers: Sequence[LabourOffer], ledger: YearLedger,
                 context, supply=None):
    """Run the core's year on the record's workforce: wages, hires, training, entry, switching and migration;
    returns the core's report. Then settle each market. `context` is the core's inputs without trades and bids
    (labour_inputs.labour_context). With `supply` (labour_supply.HourSupply) the hours each market sells are the hours
    its offers hold, rising with the wage, and the offers settled are those sold at the wage the market cleared at
    (`supply.sold`); without it the core sells every worker's whole year and `offers` are the sellers."""
    if not isinstance(bids, LabourBidTable):      # bids handed over as records (a test) are put into rows
        found = LabourBidTable()
        found.add_objects(bids)
        bids = found
    core_bids = TrancheBids(bids, BID_TRANCHES, BID_VALUE_SPREAD)      # the core cuts each bid into its tranches (labour_bids.sloped_bids is the same rule as objects)
    floor_areas = list(context.ask_floor_per_worker_year)
    ledger.wage_floor_per_hour = mean_floor_per_hour(
        context.ask_floor_per_worker_year, dict(zip(floor_areas, people_in_areas(record.labour.workforce, floor_areas).tolist())),
        context.hours_per_worker_year)
    inputs = dataclasses.replace(context, trades=core_trades(setup, core_bids.trade_names()),
                                 bids=core_bids, hours_sold_at=supply.schedules() if supply is not None else None)
    record.labour.workforce, report = run_labour_year(record.labour.workforce, inputs, owned=True)
    rows = clearing_rows(report.clearings)
    if supply is not None:
        offers = supply.settle(dict(zip(zip(rows[0].trade, rows[0].area), rows[0].wage.tolist())))
    fills = fills_of(*rows, offers)
    labour_settle_year.settle_year(record.book, ledger, fills, setup.currency_id)
    ledger.labour_results = LabourResults(fills, setup.currency_id, ledger.labour_results)
    markets = fills.markets
    record.labour.hours_idle = note_idle_hours(record.labour.sold_share_expected, markets.trade, markets.area, markets.hours_hired, markets.idle_hours)
    mirror_wages(record.memory.wages, record.labour.workforce)
    return report
