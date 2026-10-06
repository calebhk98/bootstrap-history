"""Merchants: agents that buy where a good is cheap and hold it where it is dear.

The year is annual, so a merchant acts on last year's prices. In one year it
  1. `orders`    offers what it already holds at a destination, at the holding reservation of the price
                 it expects there; bids in cheap areas for goods whose expected price in another area
                 exceeds the price here plus carriage, a year's interest on the money tied up, the
                 spoilage of the held stock and a margin. Quantities are limited by cash and by a share
                 of the destination's expected market net of what it already holds there and has bid for
                 from other sources; merchants sizing one after another also share the destination
                 (`merchants_shares`). Merchants chasing one gap still overshoot it within those limits.
  2. `dispatch`  after the markets clear, carries what it holds on each route's source tile (what
                 it bought, and older stock worth more elsewhere) to the destination (`DeliveredMove`) and pays the carriage to the carrier the caller
                 names for the source tile, or to `EDGE_CARRIAGE` when it names none. Goods it
                 cannot pay to carry stay put and are offered where they are next year.
  3. `close_year` moves its price and volume expectations toward what the year showed and pays its
                 owner a share of the profit over its capital base.
Goods bought one year are sold the next, so carrying costs one year of interest and spoilage.
`Merchant.routes` is set by `orders` and read by `dispatch`.

Standalone: `sim.constants`, `sim.economy` records, the carriage table and the area map.
"""
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import inventory
from .accounts import DeliveredMove
from .households_orders import BUDGET_SAFETY_SHARE
from .market_areas import AreaMap
from .merchants_shares import RouteShares, room_left
from .protocols import AgentOrders, MarketView
from .tile_costs import CarriageTable
from .types import AgentId, AreaId, Bid, CurrencyId, Fill, GoodId, GoodSpec, Offer, TileId, Transfer
from sim.unit_conversions import KILOGRAMS_PER_TONNE

EDGE_CARRIAGE = "edge:carriage"          # carriage with no named carrier; the caller creates it

MERCHANT_MARGIN_SHARE = declare(
    "MERCHANT_MARGIN_SHARE", 0.05, kind="temporary_heuristic", unit="share of the buying price",
    source=None, confidence="D",
    why="The gain over carriage, interest and spoilage a merchant wants before it commits capital, "
        "standing for the risk of a price move. Real margins follow risk and competition; not yet derived.")
MERCHANT_MARKET_SHARE = declare(
    "MERCHANT_MARKET_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the destination's expected yearly volume", source=None, confidence="D",
    why="How much of a destination's market one merchant dares supply, over all the sources it buys "
        "from. A merchant's own estimate of rivals is not yet modelled; the group share in "
        "merchants_shares stands in for it.")
MERCHANT_EXPECTATION_SPEED = declare(
    "MERCHANT_EXPECTATION_SPEED", 0.7, kind="temporary_heuristic", unit="share of the gap closed a year",
    source=None, confidence="D",
    why="Adaptive expectation: the share of the gap between expectation and the year's outcome that "
        "is closed. Fast, because a merchant sees its own markets; not yet fitted.")
MERCHANT_BID_ELASTICITY = declare(
    "MERCHANT_BID_ELASTICITY", 6.0, kind="temporary_heuristic", unit="dimensionless",
    source=None, confidence="D",
    why="A merchant's demand falls steeply as the price rises above what it expected, since its "
        "margin is thin. The schedule form cannot express a hard price ceiling, so a steep curve stands in.")
MERCHANT_PROFIT_PAYOUT_SHARE = declare(
    "MERCHANT_PROFIT_PAYOUT_SHARE", 0.5, kind="temporary_heuristic", unit="share of the year's profit",
    source=None, confidence="D",
    why="The share of a profitable year an owner takes out while trade beats the interest rate; the "
        "rest becomes working capital. An owner's own consumption and saving choice is not modelled.")


@dataclass
class Merchant:
    agent_id: AgentId
    home_tile: TileId                    # where it keeps its purse; stocks sit on destination tiles
    owner: AgentId                       # who receives its profit
    capital_base: float                  # capital staked in trade; profit is wealth above it
    expected_prices: Dict[Tuple[GoodId, AreaId], float] = field(default_factory=dict)
    expected_volumes: Dict[Tuple[GoodId, AreaId], float] = field(default_factory=dict)
    routes: Dict[Tuple[GoodId, TileId], Tuple[TileId, AreaId]] = field(default_factory=dict)   # (good, source tile) -> (destination tile, area)


@dataclass(frozen=True)
class Dispatch:
    moves: Tuple[DeliveredMove, ...]
    transfers: Tuple[Transfer, ...]
    stranded: Tuple[Tuple[GoodId, TileId, float], ...]     # (good, tile, quantity) it could not pay to carry


def expected_price(merchant: Merchant, view: MarketView, good: GoodId, area: AreaId) -> Optional[float]:
    price = merchant.expected_prices.get((good, area))
    return price if price is not None else view.price(good, area)


def gap_cost_per_unit(spec: GoodSpec, price_here: float, price_there: float,
                      carriage_per_tonne: float, interest_rate: float) -> float:
    """What carrying a unit from here to there and selling it next year costs, margin included."""
    carriage = carriage_per_tonne * spec.unit_mass_kg / KILOGRAMS_PER_TONNE
    interest = price_here * max(0.0, interest_rate)
    spoilage = price_there * min(1.0, max(0.0, spec.spoilage_per_year))
    return carriage + interest + spoilage + MERCHANT_MARGIN_SHARE * price_here


def orders(merchant: Merchant, view: MarketView, carriage: CarriageTable, area_map: AreaMap, cash: float,
           held_stock: Mapping[Tuple[GoodId, TileId], float], specs: Mapping[GoodId, GoodSpec],
           interest_rate: float, shares: Optional[RouteShares] = None) -> AgentOrders:
    """The merchant's offers and bids for the year. Sets `merchant.routes`. `shares` is what rival
    merchants have already committed this year; this merchant adds its own to it."""
    shares = shares if shares is not None else RouteShares()
    own = RouteShares()
    merchant.routes = {}
    candidates = _candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate)
    # stock already held where a route out pays is carried along it, not sold where it sits
    for _rank, good, source, destination, *_rest in candidates:
        for (held_good, tile), quantity in sorted(held_stock.items()):
            if held_good == good and quantity > 0.0 and tile in source.tiles and tile != destination.anchor_tile:
                merchant.routes[(good, tile)] = (destination.anchor_tile, destination.area_id)
    offers = [offer for offer in _holding_offers(merchant, view, area_map, held_stock, specs, interest_rate)
              if (offer.good, offer.tile) not in merchant.routes]
    bids: List[Bid] = []
    remaining = max(0.0, cash) * (1.0 - BUDGET_SAFETY_SHARE)     # a hair kept back: borrowed cash is all spent
    for _rank, good, source, destination, price_here, outlay, ceiling in candidates:
        if remaining <= 0.0:
            break
        quantity = min(remaining / outlay, shared_room(merchant, good, source, destination, held_stock, own, shares))
        if quantity <= 0.0:
            continue
        own.commit(good, source.area_id, destination.area_id, quantity)
        shares.commit(good, source.area_id, destination.area_id, quantity)
        merchant.routes[(good, source.anchor_tile)] = (destination.anchor_tile, destination.area_id)
        bids.append(Bid(merchant.agent_id, good, source.area_id, source.anchor_tile, 0.0, quantity,
                        price_here, MERCHANT_BID_ELASTICITY, quantity * price_here, maximum_price=ceiling))
        remaining -= quantity * outlay
    return AgentOrders(bids=tuple(bids), offers=tuple(offers))


def _holding_offers(merchant, view, area_map, held_stock, specs, interest_rate) -> List[Offer]:
    offers = []
    for (good, tile), quantity in sorted(held_stock.items()):
        if quantity <= 0.0 or good not in specs:
            continue
        area = area_map.area_of(good, tile)
        expected = expected_price(merchant, view, good, area)
        if expected is None:
            continue
        reservation = inventory.holding_reservation(expected, interest_rate, specs[good].spoilage_per_year, 0.0)
        offers.append(Offer(merchant.agent_id, good, area, tile, quantity, reservation))
    return offers


def _candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate):
    """Rows (rank, good, source, destination, price here, outlay per unit, most it pays), one per
    profitable (good, source area) at its best destination, best net gap per unit of outlay first."""
    rows = []
    interest = max(0.0, interest_rate)
    expected_prices = merchant.expected_prices
    for good in sorted(set(specs) & set(area_map.goods())):
        areas = area_map.areas(good)
        if len(areas) < 2:
            continue
        spec = specs[good]
        prices = {}
        for area in areas:
            price = expected_prices.get((good, area.area_id))
            prices[area.area_id] = price if price is not None else view.price(good, area.area_id)
        spoilage = min(1.0, max(0.0, spec.spoilage_per_year))
        keep = 1.0 - spoilage
        unit_mass = spec.unit_mass_kg
        # (price there, price there kept after spoilage, its spoilage cost, anchor tile, area id, area), dearest first
        dearest_first = [(prices[area.area_id], prices[area.area_id] * keep, prices[area.area_id] * spoilage,
                          area.anchor_tile, area.area_id, area)
                         for area in sorted((area for area in areas if prices[area.area_id]),
                                            key=lambda area: (-prices[area.area_id], area.area_id))]
        for source in areas:
            price_here = prices[source.area_id]
            if not price_here or price_here <= 0.0:
                continue
            best = None
            best_net = None
            floor_cost = price_here * (1.0 + interest + MERCHANT_MARGIN_SHARE)
            interest_here = price_here * interest              # the terms of gap_cost_per_unit, hoisted
            margin_here = MERCHANT_MARGIN_SHARE * price_here
            cost_to = carriage.costs_from(source.anchor_tile)
            for price_there, kept_there, spoilage_there, anchor_tile, area_id, destination in dearest_first:
                # carriage only adds cost, so no cheaper destination can beat this bound
                bound = kept_there - floor_cost
                if bound <= 0.0 or (best_net is not None and bound <= best_net):
                    break
                if area_id == source.area_id:
                    continue
                per_tonne = cost_to.get(anchor_tile, math.inf)
                if per_tonne == math.inf:
                    continue
                net = price_there - price_here - (per_tonne * unit_mass / KILOGRAMS_PER_TONNE
                                                  + interest_here + spoilage_there + margin_here)
                if net > 0.0 and (best_net is None or net > best_net):
                    best, best_net = (destination, per_tonne), net
            if best is None:
                continue
            destination, per_tonne = best
            carriage_per_unit = per_tonne * unit_mass / KILOGRAMS_PER_TONNE
            outlay = price_here + carriage_per_unit
            rows.append((-best_net / outlay, good, source, destination, price_here, outlay,
                         _break_even_price(spec, prices[destination.area_id], carriage_per_unit, interest_rate)))
    return sorted(rows, key=lambda row: (row[0], row[1], row[2].area_id))


def _break_even_price(spec: GoodSpec, price_there: float, carriage_per_unit: float, interest_rate: float) -> float:
    """The source price at which the gap just covers carriage, interest, spoilage and margin
    (gap_cost_per_unit solved for the price here): above it the trade loses money."""
    kept = price_there * (1.0 - min(1.0, max(0.0, spec.spoilage_per_year))) - carriage_per_unit
    return max(0.0, kept) / (1.0 + max(0.0, interest_rate) + MERCHANT_MARGIN_SHARE)


def shared_room(merchant, good, source, destination, held_stock, own: RouteShares, group: RouteShares) -> float:
    """Units this merchant may still bid for into a destination: its share of the expected volume less
    what it holds there and has bid for already, and merchants' share of it less what they have bid."""
    held = sum(quantity for (held_good, tile), quantity in held_stock.items()
               if held_good == good and tile in destination.tiles)
    return room_left(merchant.expected_volumes, good, source.area_id, destination.area_id, MERCHANT_MARKET_SHARE,
                     own, group, held)


def dispatch(merchant: Merchant, fills: Sequence[Fill], carriage: CarriageTable,
             specs: Mapping[GoodId, GoodSpec], currency: CurrencyId, cash: float,
             held_stock: Mapping[Tuple[GoodId, TileId], float],
             carrier_of: Callable[[TileId], Optional[AgentId]] = lambda _tile: EDGE_CARRIAGE) -> Dispatch:
    """Carry what the merchant holds on each route's source tile (this year's purchases and older stock)
    to the route's destination, paying carriage from `cash` to `carrier_of(source tile)` (the edge when
    it names nobody). `fills` are not needed: what settled is what is held."""
    moves, transfers, stranded = [], [], []
    remaining = max(0.0, cash)
    for (good, tile), route in sorted(merchant.routes.items()):
        if route[0] == tile:
            continue
        per_unit = carriage.cost_per_tonne(tile, route[0]) * specs[good].unit_mass_kg / KILOGRAMS_PER_TONNE
        quantity = held_stock.get((good, tile), 0.0)
        affordable = quantity if per_unit <= 0.0 else min(quantity, remaining / per_unit)
        if affordable < quantity:
            stranded.append((good, tile, quantity - affordable))
        if affordable <= 0.0:
            continue
        moves.append(DeliveredMove(merchant.agent_id, merchant.agent_id, good, tile, affordable,
                                   "carried to market", route[0]))
        fee = affordable * per_unit
        if fee > 0.0:
            transfers.append(Transfer(merchant.agent_id, carrier_of(tile) or EDGE_CARRIAGE, currency, fee,
                                      "carriage of %s" % good))
            remaining -= fee
    return Dispatch(tuple(moves), tuple(transfers), tuple(stranded))


def close_year(merchant: Merchant, prices: Mapping[Tuple[GoodId, AreaId], float],
               volumes: Mapping[Tuple[GoodId, AreaId], float], cash: float,
               held_stock: Mapping[Tuple[GoodId, TileId], float],
               area_of: Callable[[GoodId, TileId], AreaId], currency: CurrencyId,
               interest_rate: float) -> Tuple[Transfer, ...]:
    """Update expectations from this year's clearing prices and volumes (by (good, area)), then settle
    the year's profit (wealth, cash plus stock at expected prices, above the capital base). While
    trading earns more on its capital than the interest rate, the owner takes a share and the rest
    becomes capital; otherwise the owner takes all of it. A loss shrinks the capital."""
    for expectation, observed in ((merchant.expected_prices, prices), (merchant.expected_volumes, volumes)):
        for key, value in sorted(observed.items()):
            old = expectation.get(key)
            expectation[key] = value if old is None else old + MERCHANT_EXPECTATION_SPEED * (value - old)
    stock_value = math.fsum(quantity * merchant.expected_prices.get((good, area_of(good, tile)), 0.0)
                            for (good, tile), quantity in held_stock.items() if quantity > 0.0)
    wealth = cash + stock_value
    profit = wealth - merchant.capital_base
    if profit <= 0.0:
        merchant.capital_base = max(0.0, wealth)
        return ()
    earns_more = merchant.capital_base > 0.0 and profit / merchant.capital_base > interest_rate
    payout = min(max(0.0, cash), (MERCHANT_PROFIT_PAYOUT_SHARE if earns_more else 1.0) * profit)
    if earns_more:
        merchant.capital_base = wealth - payout
    if payout <= 0.0:
        return ()
    return (Transfer(merchant.agent_id, merchant.owner, currency, payout, "merchant profit"),)
