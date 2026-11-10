"""Bonded hours leave the labour market (Complaint 538): a bonded cohort owes its creditor a share of its working
hours (bondage.BONDED_HOURS_OWED_SHARE), and the owed hours are worked in the creditor's own works, not sold.

Before the market clears, the owed share of each bonded cohort's offered hours (no more than the debt left is worth at
the cohort's reservation wage) is placed with the creditor's producers that bid for that trade in that area: the
hours come off the cohort's offer and off the producer's bid, and the producer is credited them as hired. Owed hours
no work of the creditor wants stay in the market, where the creditor takes its share of the wages instead
(bondage.service). The credited hours come off the debt at the reservation wage, the value of the hour to the cohort.

The offers and bids are rows (`labour_offer_rows.LabourOfferRows`, `LabourBidTable`) and the rules are the kernels of
`bondage_kernels.py`; records handed over (a test) are put into rows first. Each call returns offers and bids of its own columns with
the hours cut, and leaves the ones it was given as they were."""
import dataclasses
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy

from sim.labour.api import LabourBidTable

from . import bondage_kernels, titles
from .bondage_rows import KeepRows, as_rows, market_keys, numbers_of, ranges_of
from .labour_offer_rows import LabourOfferRows
from .types import AgentId, LabourBid, LabourOffer


@dataclasses.dataclass
class Placement:
    offers: LabourOfferRows
    bids: LabourBidTable
    hired: Dict[AgentId, Dict[str, float]]          # employer -> trade -> hours worked for the creditor
    hours_placed: Dict[AgentId, float]              # cohort -> hours it worked for its creditor
    value_placed: Dict[AgentId, float]              # cohort -> those hours at its reservation wage
    cash_share: Dict[AgentId, float]                # cohort -> share of its market wages still owed in cash


def _owner_codes(names: Sequence[str], works_of: Callable[[AgentId], Optional[AgentId]]) -> Tuple[Dict[Optional[str], int], List[int]]:
    """A whole number for each distinct owner of the works the named employers run (two employers have the same number when the
    same owner has their works), and the owner number of each employer."""
    codes: Dict[Optional[str], int] = {}
    return codes, [codes.setdefault(works_of(name), len(codes)) for name in names]


def place(bonds: Mapping[AgentId, Mapping], offers: Union[LabourOfferRows, Sequence[LabourOffer]],
          bids: Union[LabourBidTable, Sequence[LabourBid]], works_of: Callable[[AgentId], Optional[AgentId]], owed_share: float) -> Placement:
    """Place bonded cohorts' owed hours with their creditors' works. `works_of(employer)` is the owner of the
    employer's works (the employer itself for an actor that is its own owner), or None."""
    offers, bids = as_rows(offers, bids)
    new_offers, new_bids = offers.copy(), bids.copy()
    result = Placement(new_offers, new_bids, {}, {}, {}, {})
    ordered = sorted(bonds.items())
    if not ordered:
        return result
    offer_columns, bid_table = new_offers.columns(), new_bids.table()
    area_count = len(bids.areas)
    worker_order, bond_first, bond_last = ranges_of(offer_columns[0], numpy.array(
        numbers_of([cohort for cohort, _bond in ordered], new_offers.workers), dtype=numpy.int64))
    market_bid_order, offer_bid_first, offer_bid_last = ranges_of(market_keys(bid_table.trade, bid_table.area, area_count),
                                                                  market_keys(offer_columns[1], offer_columns[2], area_count))
    codes, owner_of_employer = _owner_codes(bids.employers.names, works_of)
    bid_owner = numpy.array(owner_of_employer, dtype=numpy.int64)[bid_table.employer] if len(new_bids) else numpy.zeros(0, numpy.int64)
    creditors = numpy.array([codes.setdefault(bond["creditor"], len(codes)) for _cohort, bond in ordered], dtype=numpy.int64)
    count = len(ordered)
    total, placed, value, share = numpy.zeros(count), numpy.zeros(count), numpy.zeros(count), numpy.zeros(count)
    counted, took = numpy.zeros(count, dtype=numpy.bool_), numpy.zeros(count, dtype=numpy.bool_)
    running = numpy.concatenate(([0], numpy.cumsum((offer_bid_last - offer_bid_first)[worker_order])))      # bids each offer could take
    capacity = int((running[bond_last] - running[bond_first]).sum())
    take_bid, take_hours = numpy.zeros(capacity, dtype=numpy.int64), numpy.zeros(capacity)
    taken = bondage_kernels.place_bonds_kernel(
        bond_first, bond_last, creditors, numpy.array([bond["debt"] for _cohort, bond in ordered], dtype=numpy.float64), worker_order,
        offer_columns[3], offer_columns[4], offer_bid_first, offer_bid_last, market_bid_order, bid_table.hours, bid_owner, owed_share,
        titles.EPSILON, total, placed, value, share, counted, took, take_bid, take_hours, numpy.zeros(len(worker_order) + 1))
    new_offers.hours_changed()
    employers, trades = bids.employers.names, bids.trades.names
    for slot, hours in zip(take_bid[:taken].tolist(), take_hours[:taken].tolist()):
        rows = result.hired.setdefault(employers[bid_table.employer[slot]], {})
        trade = trades[bid_table.trade[slot]]
        rows[trade] = rows.get(trade, 0.0) + hours
    for index, (cohort, _bond) in enumerate(ordered):
        if took[index]:
            result.hours_placed[cohort], result.value_placed[cohort] = float(placed[index]), float(value[index])
        if counted[index]:
            result.cash_share[cohort] = float(share[index])
    return result


def deliver(hours_hired: Dict[AgentId, Dict[str, float]], placement: Union[Placement, "HeldPlacement"]) -> None:
    """Book the hours a placement hired (worked for creditors, or by held bonded people) as hired hours of the employers."""
    for employer, by_trade in placement.hired.items():
        rows = hours_hired.setdefault(employer, {})
        for trade, hours in by_trade.items():
            rows[trade] = rows.get(trade, 0.0) + hours


def works_of_producers(record) -> Callable[[AgentId], Optional[AgentId]]:
    """Employer -> the owner of its works: a producer's owner, or the employer itself when it is no producer."""
    return lambda employer: record.producers[employer].owner if employer in record.producers else employer


def hold(held: Dict[str, Dict[str, Dict[AgentId, float]]], bought: Mapping[Tuple[str, str], Mapping[AgentId, float]]) -> None:
    """Record the bought bonded people each employer holds, by tile and trade (bonded_purchase.settle)."""
    for (tile, trade), by_employer in sorted(bought.items()):
        rows = held.setdefault(tile, {}).setdefault(trade, {})
        for employer, people in sorted(by_employer.items()):
            rows[employer] = rows.get(employer, 0.0) + people


def release(held: Dict[str, Dict[str, Dict[AgentId, float]]], employer: AgentId) -> None:
    """Drop the bought bonded people `employer` holds (it left the economy), and the tile and trade rows that leaves empty."""
    for tile in list(held):
        for trade in list(held[tile]):
            held[tile][trade].pop(employer, None)
            if not held[tile][trade]:
                del held[tile][trade]
        if not held[tile]:
            del held[tile]


def release_many(held: Dict[str, Dict[str, Dict[AgentId, float]]], employers) -> None:
    """`release` for every one of `employers` in one pass over the held rows (the result is the same as releasing them one by one)."""
    leaving = set(employers)
    if not held or not leaving:
        return
    for tile in list(held):
        for trade in list(held[tile]):
            by_employer = held[tile][trade]
            for employer in leaving.intersection(by_employer):
                del by_employer[employer]
            if not by_employer:
                del held[tile][trade]
        if not held[tile]:
            del held[tile]


@dataclasses.dataclass
class HeldPlacement:
    offers: LabourOfferRows
    bids: LabourBidTable
    hired: Dict[AgentId, Dict[str, float]]          # employer -> trade -> hours worked by the people it holds
    keep: KeepRows                                  # the keep the holder owes for those hours (employer, cohort, money)


def place_held(held: Dict[str, Dict[str, Dict[AgentId, float]]], workers: Callable[[Sequence[str], Sequence[str]], numpy.ndarray],
               offers: Union[LabourOfferRows, Sequence[LabourOffer]], bids: Union[LabourBidTable, Sequence[LabourBid]],
               hours_per_worker: float, keep_per_worker_year: Mapping[str, float], area_of: Callable[[str], str]) -> HeldPlacement:
    """The hours of bought bonded people are their holders': for each (tile, trade) the people held (no more than the
    trade's workers there, so deaths and retirements thin them) work for the employer that holds them, off the
    market, as far as that employer bids hours for the trade there. They come off the offers of the households the
    workers live in, in proportion, and the holder pays the keep of the people working for it, which the hours no
    longer earn their households. `workers(areas, trades)` gives the working people of each (area, trade) pair at once."""
    offers, bids = as_rows(offers, bids)
    new_offers, new_bids = offers.copy(), bids.copy()
    if not held:
        return HeldPlacement(new_offers, new_bids, {}, KeepRows([], [], []))
    triples, group_areas, group_trades, group_of, area_names = [], [], [], [], []
    for tile in sorted(held):
        area = area_of(tile)
        for trade in sorted(held[tile]):
            group_areas.append(area)
            group_trades.append(trade)
            for employer in sorted(held[tile][trade]):
                triples.append((tile, trade, employer))
                group_of.append(len(group_areas) - 1)
                area_names.append(area)
    group_available = workers(group_areas, group_trades)
    triple_trade = numpy.array(numbers_of([trade for _tile, trade, _employer in triples], bids.trades), dtype=numpy.int64)
    triple_area = numpy.array(numbers_of(area_names, bids.areas), dtype=numpy.int64)
    triple_employer = numpy.array(numbers_of([employer for _tile, _trade, employer in triples], bids.employers), dtype=numpy.int64)
    area_count, trade_count = len(bids.areas), len(bids.trades)
    table, columns = new_bids.table(), new_offers.columns()
    bid_keys = table.employer * (trade_count * area_count) + market_keys(table.trade, table.area, area_count)
    asked_market = market_keys(triple_trade, triple_area, area_count)
    asked = numpy.where((triple_employer < 0) | (asked_market < 0), -1, triple_employer * (trade_count * area_count) + asked_market)
    bid_order, bid_first, bid_last = ranges_of(bid_keys, asked)
    offer_order, offer_first, offer_last = ranges_of(market_keys(columns[1], columns[2], area_count), asked_market)
    keep_capacity = int(((bid_last - bid_first) * (offer_last - offer_first)).sum())
    take_capacity = int((bid_last - bid_first).sum())
    people_after = numpy.zeros(len(triples))
    keep_triple, keep_offer, keep_amount = numpy.zeros(keep_capacity, numpy.int64), numpy.zeros(keep_capacity, numpy.int64), numpy.zeros(keep_capacity)
    take_triple, take_hours = numpy.zeros(take_capacity, numpy.int64), numpy.zeros(take_capacity)
    keeps, takes = bondage_kernels.place_held_kernel(
        numpy.array(group_of, dtype=numpy.int64), numpy.asarray(group_available, dtype=numpy.float64),
        numpy.array([held[tile][trade][employer] for tile, trade, employer in triples], dtype=numpy.float64), bid_first, bid_last,
        bid_order, offer_first, offer_last, offer_order, columns[3], table.hours, hours_per_worker,
        numpy.array([keep_per_worker_year.get(area, 0.0) for area in area_names], dtype=numpy.float64), people_after, keep_triple, keep_offer,
        keep_amount, take_triple, take_hours, numpy.zeros(int((offer_last - offer_first).max(initial=0)) + 1))
    new_offers.hours_changed()
    for (tile, trade, employer), people in zip(triples, people_after.tolist()):
        held[tile][trade][employer] = people
    hired: Dict[AgentId, Dict[str, float]] = {}
    for triple, hours in zip(take_triple[:takes].tolist(), take_hours[:takes].tolist()):
        _tile, trade, employer = triples[triple]
        rows = hired.setdefault(employer, {})
        rows[trade] = rows.get(trade, 0.0) + hours
    worker_names = new_offers.workers.names
    keep = KeepRows([triples[each][2] for each in keep_triple[:keeps].tolist()],
                    [worker_names[columns[0][each]] for each in keep_offer[:keeps].tolist()], keep_amount[:keeps])
    return HeldPlacement(new_offers, new_bids, hired, keep)


def payable_keep(keep: Union[KeepRows, Sequence[Tuple[AgentId, AgentId, float]]], balance_of: Callable[[AgentId], float]) -> KeepRows:
    """The keep rows a holder can pay from what it holds: rows are paid in order until the holder's balance is spent, so
    several rows of one holder never overdraw it."""
    keep = keep if isinstance(keep, KeepRows) else KeepRows.of_tuples(keep)
    holders = list(dict.fromkeys(keep.employers))
    number = {holder: place for place, holder in enumerate(holders)}
    balance = numpy.array([max(0.0, balance_of(holder)) for holder in holders], dtype=numpy.float64)
    paid = numpy.zeros(len(keep))
    bondage_kernels.payable_keep_kernel(numpy.array([number[holder] for holder in keep.employers], dtype=numpy.int64), keep.amounts,
                                        balance, paid)
    paying = numpy.flatnonzero(paid > 0.0)
    return KeepRows([keep.employers[each] for each in paying.tolist()], [keep.cohorts[each] for each in paying.tolist()], paid[paying])
