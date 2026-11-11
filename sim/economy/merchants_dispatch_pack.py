"""One year's dispatch of every merchant as columns (`merchants_dispatch_tables`): the Python edge that packs the merchants' routes, the
hauls' figures and the purses into tables and calls `merchants_dispatch_settle_kernel.dispatch_all` once.

`dispatch_year` is the batch. Its answer is read by `merchants_dispatch_answer.Dispatched`."""
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import merchants_dispatch_tables as tables
from .carriage_fleet import FleetLimit
from .merchants import PURSE_ROUNDING_MARGIN, CrewHire, Merchant
from .merchants_dispatch_kernel import wear_needed_all
from .merchants_dispatch_settle_kernel import dispatch_all


@dataclass
class MerchantYear:
    """What one merchant brings to the year's dispatch: its purse, what it holds, its crew hired (None: no crew hired in this setup) and its
    fleet (None: no fleet bounds it; `own` and `hired` are the wear a year its own and hired carriers bear)."""
    merchant: Merchant
    cash: float
    held: Mapping[Tuple[str, str], float]
    dispatching: bool = True
    crew: Optional[CrewHire] = None
    fleet: Optional[FleetLimit] = None
    own: Mapping[str, float] = field(default_factory=dict)
    hired: Mapping[str, float] = field(default_factory=dict)


@dataclass
class YearHauls:
    """The year's figures for a haul: what carrying a tonne from a tile to another costs, wears and owes, and who is paid."""
    carriage: object
    specs: Mapping
    carrier_of: Callable
    currency: str
    dues: Callable
    wear_units: Optional[Callable] = None            # None: no carriers are owned or worn
    carrier_money: Optional[Callable] = None
    lent: Mapping = field(default_factory=dict)      # {carrier good: {lessor merchant: wear lent}}
    carrier_prices: Mapping = field(default_factory=dict)


@dataclass
class Packed:
    """The tables of a year's dispatch and the names their numbers stand for."""
    entries: Sequence[MerchantYear]
    hauls: YearHauls
    pairs: object
    routes: object
    legs: object
    merchants: object
    flags: numpy.ndarray
    in_fleet: numpy.ndarray
    lent_share: numpy.ndarray
    lent_total: numpy.ndarray
    carrier_price: numpy.ndarray
    key_names: List[str]
    carrier_names: List[str]
    pair_holders: List[Tuple[str, ...]]
    leg_info: List[Tuple[str, str, str]]          # (good, source tile, destination tile) of each leg


def _pair_figures(entries: Sequence[MerchantYear], hauls: YearHauls, crew):
    """The distinct hauls of the dispatching merchants' routes (number by (source tile, destination tile)) and each one's figures:
    (cost, carrier money, crew rows, wear rows, dues rows)."""
    numbers: Dict[Tuple[str, str], int] = {}
    figures: List[tuple] = []
    for entry in entries:
        if not entry.dispatching:
            continue
        for (_good, tile), legs in sorted(entry.merchant.routes.items()):
            for destination, _area, _weight in legs:
                if destination == tile or (tile, destination) in numbers:
                    continue
                numbers[(tile, destination)] = len(figures)
                money = hauls.carrier_money(tile, destination) if hauls.carrier_money is not None else None
                figures.append((hauls.carriage.cost_per_tonne(tile, destination), math.nan if money is None else money,
                                crew.hours_per_tonne(tile, destination) if crew is not None else (),
                                tuple(hauls.wear_units(tile, destination).items()) if hauls.wear_units is not None else (),
                                tuple(sorted(hauls.dues(tile, destination).items()))))
    return numbers, figures


def _pair_table(figures, key_number: Mapping[str, int], carrier_number: Mapping[str, int]):
    crew_width = max([len(each[2]) for each in figures], default=0)
    wear_width = max([len(each[3]) for each in figures], default=0)
    table = tables.new(tables.PAIRS, tables.DispatchPairs, len(figures), crew_key=crew_width, crew_hours=crew_width,
                       wear_carrier=wear_width, wear_units=wear_width, dues_owed=max([len(each[4]) for each in figures], default=0))
    for row, (cost, money, crew_rows, wear_rows, dues_rows) in enumerate(figures):
        table.cost[row], table.money[row] = cost, money
        table.crew_count[row], table.wear_count[row], table.dues_count[row] = len(crew_rows), len(wear_rows), len(dues_rows)
        for place, (key, hours) in enumerate(crew_rows):
            table.crew_key[row, place], table.crew_hours[row, place] = key_number[key], hours
        for place, (carrier, units) in enumerate(wear_rows):
            table.wear_carrier[row, place], table.wear_units[row, place] = carrier_number[carrier], units
        for place, (_holder, owed) in enumerate(dues_rows):
            table.dues_owed[row, place] = owed
    return table


def _routes_and_legs(entries, hauls, numbers, figures):
    """The routes (the merchant's stock at each (good, source tile)) and legs, in merchant order and route order, as lists of columns."""
    route_rows, leg_rows, leg_info, first_routes = [], [], [], []
    for row, entry in enumerate(entries):
        first_routes.append((len(route_rows), 0))
        if not entry.dispatching:
            continue
        for (good, tile), legs in sorted(entry.merchant.routes.items()):
            route_rows.append((row, hauls.specs[good].unit_mass_kg, entry.held.get((good, tile), 0.0), len(leg_rows), len(legs)))
            prices = entry.merchant.expected_prices
            leaving = None     # the price expected where the goods leave, read once for the route
            for destination, area, weight in legs:
                pair = -1 if destination == tile else numbers[(tile, destination)]
                spread = 0.0     # what the haul gains a unit by the merchant's expectations; only a haul with crew rows is valued
                if entry.crew is not None and pair >= 0 and len(figures[pair][2]) > 0:
                    if leaving is None:     # a source with no expectation is worth nothing to leave
                        leaving = prices.get((good, entry.crew.area_of(good, tile)), math.inf)
                    spread = prices.get((good, area), 0.0) - leaving
                leg_rows.append((pair, weight, spread))
                leg_info.append((good, tile, destination))
        first_routes[-1] = (first_routes[-1][0], len(route_rows) - first_routes[-1][0])
    return route_rows, leg_rows, leg_info, first_routes


def _fill(table, **columns) -> None:
    for name, values in columns.items():
        if len(values):
            getattr(table, name)[:len(values)] = values


def pack(entries: Sequence[MerchantYear], hauls: YearHauls, fleet_goods: Sequence[str] = ()) -> Packed:
    """The tables of the year's dispatch for the merchants `entries` (all the record's merchants, in the order their purses move);
    `fleet_goods` are the carrier goods held as a fleet. The fleet each merchant has is fitted (`fit_fleet`) once it is known."""
    crew = next((entry.crew for entry in entries if entry.crew is not None and entry.dispatching), None)
    numbers, figures = _pair_figures(entries, hauls, crew)
    key_names = sorted({key for each in figures for key, _hours in each[2]})
    carrier_names = sorted({carrier for each in figures for carrier, _units in each[3]}
                           | set(fleet_goods))
    key_number = {name: place for place, name in enumerate(key_names)}
    carrier_number = {name: place for place, name in enumerate(carrier_names)}
    route_rows, leg_rows, leg_info, first_routes = _routes_and_legs(entries, hauls, numbers, figures)
    routes = tables.new(tables.ROUTES, tables.DispatchRoutes, len(route_rows))
    legs = tables.new(tables.LEGS, tables.DispatchLegs, len(leg_rows))
    for place, name in enumerate(("merchant", "unit_mass_kg", "held", "first_leg", "leg_count")):
        _fill(routes, **{name: [each[place] for each in route_rows]})
    for place, name in enumerate(("pair", "weight", "spread")):
        _fill(legs, **{name: [each[place] for each in leg_rows]})
    merchants = _merchant_table(entries, crew, first_routes, key_number, carrier_number, numbers, figures)
    count = len(carrier_names)
    in_fleet = numpy.array([name in fleet_goods for name in carrier_names], numpy.bool_)
    lent_share = numpy.zeros((count, len(entries)))
    lent_total = numpy.zeros(count)
    carrier_price = numpy.full(count, math.nan)
    flags = numpy.array([crew is not None, hauls.wear_units is not None, len(fleet_goods) > 0], numpy.int64)
    holders = [tuple(holder for holder, _owed in each[4]) for each in figures]
    return Packed(entries, hauls, _pair_table(figures, key_number, carrier_number), routes, legs, merchants, flags, in_fleet, lent_share,
                  lent_total, carrier_price, key_names, carrier_names, holders, leg_info)


def _merchant_table(entries, crew, first_routes, key_number, carrier_number, numbers, figures):
    keys, carriers = len(key_number), len(carrier_number)
    table = tables.new(tables.MERCHANTS, tables.DispatchMerchants, len(entries), market_wage=keys, hired_hours=keys, paid_wage=keys,
                       fleet_capacity=carriers, own_capacity=carriers, fleet_hired=carriers, fleet_hired_named=carriers)  # fitted by fit_fleet
    table.paid_wage[:] = math.nan
    for row, entry in enumerate(entries):
        table.dispatching[row], table.cash[row] = entry.dispatching, entry.cash
        table.first_route[row], table.route_count[row] = first_routes[row]
        if entry.dispatching and entry.crew is not None:
            _crew_columns(table, row, entry, key_number, {key for pair in _pairs_of(entry) if pair in numbers
                                                          for key, _hours in figures[numbers[pair]][2]})
    return table


def _pairs_of(entry: MerchantYear):
    return {(tile, destination) for (_good, tile), legs in entry.merchant.routes.items() for destination, _area, _weight in legs}


def _crew_columns(table, row: int, entry: MerchantYear, key_number, keys_used) -> None:
    crew = entry.crew
    table.has_plan[row] = crew.hours_hired is not None
    for key in keys_used:
        number = key_number[key]
        table.market_wage[row, number] = crew.market_wage(key)
        table.hired_hours[row, number] = 0.0 if crew.hours_hired is None else crew.hours_hired.get(key, 0.0)
        wage = crew.wage.get(key)
        table.paid_wage[row, number] = math.nan if wage is None else wage


def fit_fleet(packed: Packed) -> None:
    """Fit each merchant's fleet (what its own and hired carriers bear), and the wear idle fleets lend and their price, into the tables."""
    number = {name: place for place, name in enumerate(packed.carrier_names)}
    entries, table = packed.entries, packed.merchants
    for row, entry in enumerate(entries):
        if entry.fleet is not None:
            for good, units in entry.fleet.capacity.items():
                table.fleet_capacity[row, number[good]] = units
        for good, units in entry.own.items():
            table.own_capacity[row, number[good]] = units
        for good, units in entry.hired.items():
            table.fleet_hired[row, number[good]], table.fleet_hired_named[row, number[good]] = units, 1
    row_of = {entry.merchant.agent_id: row for row, entry in enumerate(entries)}
    for good, lessors in packed.hauls.lent.items():
        for lessor, amount in lessors.items():
            packed.lent_share[number[good], row_of[lessor]] = amount
    for good, place in number.items():
        packed.lent_total[place] = math.fsum(packed.hauls.lent.get(good, {}).values())
        packed.carrier_price[place] = packed.hauls.carrier_prices.get(good, math.nan)


def wear_needed(packed: Packed) -> List[Dict[str, float]]:
    """For each merchant, the wear a year of each fleet good that carrying the stock on its routes puts on it (`carriage_fleet_book.wear_needed`)."""
    needed = wear_needed_all(packed.pairs, packed.routes, packed.legs, packed.merchants, packed.in_fleet, KILOGRAMS_PER_TONNE)
    return [{name: float(needed[row, place]) for place, name in enumerate(packed.carrier_names) if packed.in_fleet[place] and needed[row, place] != 0.0}
            for row in range(len(packed.entries))]


def dispatch_year(entries: Sequence[MerchantYear], hauls: YearHauls):
    """Pack the merchants `entries`, fit their fleets and dispatch every one that carries in one kernel call."""
    packed = pack(entries, hauls, sorted({good for entry in entries if entry.fleet is not None for good in entry.fleet.capacity}))
    fit_fleet(packed)
    return run(packed)


def run(packed: Packed):
    """Dispatch every merchant of the packed tables that carries: (the packed tables, the leg results, the merchant results)."""
    leg_results = tables.new(tables.LEG_RESULTS, tables.DispatchLegResults, int(packed.legs.row_count[0]),
                             dues_paid=packed.pairs.dues_owed.shape[1])
    keys, carriers = len(packed.key_names), len(packed.carrier_names)
    results = tables.new(tables.MERCHANT_RESULTS, tables.DispatchMerchantResults, len(packed.entries),
                         hours_wanted=keys, hours_wanted_named=keys, money_wanted=keys, money_wanted_named=keys,
                         fleet_wanted=carriers, fleet_wanted_named=carriers, worn=carriers, worn_named=carriers, rent=len(packed.entries))
    dispatch_all(packed.pairs, packed.routes, packed.legs, packed.merchants, leg_results, results, packed.flags, packed.in_fleet,
                 packed.lent_share, packed.lent_total, packed.carrier_price, KILOGRAMS_PER_TONNE, PURSE_ROUNDING_MARGIN)
    return packed, leg_results, results
