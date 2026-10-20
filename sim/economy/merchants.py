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
Goods bought one year are sold the next, so carrying costs one year of interest and spoilage; a haul
whose travel time spans more years waits on the road for them (`merchants_transit`), costing that many
years of both, and a distant market's price reaches the merchant that many years late.
`Merchant.routes` is set by `orders` and read by `dispatch`.

Standalone: `sim.constants`, `sim.economy` records, the carriage table and the area map.
"""
import dataclasses
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import inventory, merchants_route_memo, merchants_transit
from .accounts import DeliveredMove
from .households_orders import BUDGET_SAFETY_SHARE
from .market_areas import AreaMap
from .merchants_shares import RouteShares, room_left
from .protocols import AgentOrders, MarketView
from .tile_costs import CarriageTable
from .types import AgentId, AreaId, Bid, CurrencyId, Fill, GoodId, GoodSpec, Offer, TileId, Transfer
from sim.unit_conversions import KILOGRAMS_PER_TONNE

PURSE_ROUNDING_MARGIN = 1e-12             # share of the purse kept back so float sums of fees never overdraw it
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
    carriage_hours_wanted: Optional[Dict[str, float]] = None   # crew hours its shipments needed last year, by (trade, source tile) market key: this year's bid for carriers; None until it has shipped
    carriage_money_wanted: Dict[str, float] = field(default_factory=dict)   # the carriage money those hours stand for, by the same key: the most an hour is worth to it
    carrier_wear: Dict[str, float] = field(default_factory=dict)   # carrier units its shipments wore last year, by good (carriage_wear): this year's bid for carriers
    carrier_team_days: Dict[str, float] = field(default_factory=dict)   # team-days its shipments worked last year, by carriage mode
    in_transit: List[merchants_transit.Shipment] = field(default_factory=list)   # hauls still on the road (their goods wait in the transit account)
    price_history: Dict[Tuple[GoodId, AreaId], List[float]] = field(default_factory=dict)   # prices of distant markets that news has not yet reached it, newest last


@dataclass(frozen=True)
class CrewHire:
    """The carriers a merchant hired for the year. `hours_per_tonne(source, destination)` is the crew a tonne
    needs on that haul, as ((crew key, hours),) where a key names a trade and the tile it is hired at; `hours_hired`
    the hours hired by key (None: no plan to hire for yet, so the shipments are not limited) and `wage` their
    average pay an hour by key (already paid in the labour market). `reference_wage` is the wage an hour of crew
    was priced at in the carriage table's rates: it sets how much of a fee is the crew's."""
    hours_per_tonne: Callable[[TileId, TileId], Tuple[Tuple[str, float], ...]]
    hours_hired: Optional[Mapping[str, float]]
    wage: Mapping[str, float]
    reference_wage: float


@dataclass(frozen=True)
class Dispatch:
    moves: Tuple[DeliveredMove, ...]
    transfers: Tuple[Transfer, ...]
    stranded: Tuple[Tuple[GoodId, TileId, float], ...]     # (good, tile, quantity) it could not pay or find carriers to carry
    crew_hours_wanted: Dict[str, float] = field(default_factory=dict)   # by crew key, before any cut for want of carriers
    crew_money_wanted: Dict[str, float] = field(default_factory=dict)   # the carriage money those hours stand for, by crew key


def within_purse(transfers: Sequence[Transfer], balance: float) -> Tuple[Transfer, ...]:
    """The transfers as posted against a purse holding `balance`: all of them when their sum fits the purse (less the
    rounding margin), else each cut by the same share so the sum does."""
    total = math.fsum(transfer.amount for transfer in transfers)
    allowed = max(0.0, balance) * (1.0 - PURSE_ROUNDING_MARGIN)
    if total <= allowed:
        return tuple(transfers)
    share = allowed / total
    return tuple(dataclasses.replace(transfer, amount=transfer.amount * share) for transfer in transfers)


def expected_price(merchant: Merchant, view: MarketView, good: GoodId, area: AreaId) -> Optional[float]:
    price = merchant.expected_prices.get((good, area))
    return price if price is not None else view.price(good, area)


def gap_cost_per_unit(spec: GoodSpec, price_here: float, price_there: float,
                      carriage_per_tonne: float, interest_rate: float, years: int = 1) -> float:
    """What carrying a unit from here to there and selling it `years` years on costs, margin included."""
    carriage = carriage_per_tonne * spec.unit_mass_kg / KILOGRAMS_PER_TONNE
    interest = price_here * max(0.0, interest_rate) * years
    spoilage = price_there * merchants_transit.lost_share(spec.spoilage_per_year, years)
    return carriage + interest + spoilage + merchants_transit.storage_per_unit(spec, years) + MERCHANT_MARGIN_SHARE * price_here


def orders(merchant: Merchant, view: MarketView, carriage: CarriageTable, area_map: AreaMap, cash: float,
           held_stock: Mapping[Tuple[GoodId, TileId], float], specs: Mapping[GoodId, GoodSpec],
           interest_rate: float, shares: Optional[RouteShares] = None) -> AgentOrders:
    """The merchant's offers and bids for the year. Sets `merchant.routes`. `shares` is what rival
    merchants have already committed this year; this merchant adds its own to it."""
    shares = shares if shares is not None else RouteShares()
    own = RouteShares()
    merchant.routes = {}
    held_index = held_by_good(held_stock)
    remaining = max(0.0, cash) * (1.0 - BUDGET_SAFETY_SHARE)     # a hair kept back: borrowed cash is all spent
    # with nothing to spend only the stock already held can use a route
    candidates = _candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate,
                                   None if remaining > 0.0 else held_index)
    held_sorted: Dict[GoodId, list] = {}
    # stock already held where a route out pays is carried along it, not sold where it sits
    for _rank, good, source, destination, *_rest in candidates:
        held_tiles = held_sorted.get(good)
        if held_tiles is None:
            held_tiles = held_sorted[good] = sorted(held_index.get(good, ()))
        for tile, quantity in held_tiles:
            if quantity > 0.0 and tile in source.tiles and tile != destination.anchor_tile:
                merchant.routes[(good, tile)] = (destination.anchor_tile, destination.area_id)
    offers = [offer for offer in _holding_offers(merchant, view, area_map, held_stock, specs, interest_rate)
              if (offer.good, offer.tile) not in merchant.routes]
    bids: List[Bid] = []
    for _rank, good, source, destination, price_here, outlay, ceiling in candidates:
        if remaining <= 0.0:
            break
        quantity = min(remaining / outlay, shared_room(merchant, good, source, destination, held_stock, own, shares, held_index))
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


def _candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate, only_held=None):
    """Rows (rank, good, source, destination, price here, outlay per unit, most it pays), one per
    profitable (good, source area) at its best destination, best net gap per unit of outlay first.
    With `only_held` (`held_by_good` of stock) the rows of the goods held, from the source areas holding
    them alone: each such row is the row the full search gives.
    A good's rows are shared with any caller that sees the same prices at the same rate."""
    parts = []
    prices_across = getattr(view, "prices_across", None)
    expected_by_good: dict = {}
    for (good, area_id), price in merchant.expected_prices.items():
        if price is not None:
            by_area = expected_by_good.get(good)
            if by_area is None:
                by_area = expected_by_good[good] = {}
            by_area[area_id] = price
    news_current_at: Dict[TileId, bool] = {}     # whether last year's price at a tile has reached the merchant's home

    def news_current(tile: TileId) -> bool:
        current = news_current_at.get(tile)
        if current is None:
            current = news_current_at[tile] = merchants_transit.news_lag(carriage, merchant.home_tile, tile) == 0
        return current

    for good in sorted(set(specs) & set(area_map.goods()) if only_held is None
                       else set(specs) & set(area_map.goods()) & set(only_held)):
        areas = area_map.areas(good)
        if len(areas) < 2:
            continue
        spec = specs[good]
        if prices_across is None:
            seen = [view.price(good, area.area_id) for area in areas]
        else:
            seen = prices_across(good, areas)
        expected = expected_by_good.get(good, {})
        # an expectation stands in for last year's price where the merchant has one; without one it sees
        # last year's price only where the news has had time to reach it, and nothing of a farther market
        seen = [expected[area.area_id] if area.area_id in expected
                else (price if news_current(area.anchor_tile) else None)
                for area, price in zip(areas, seen)]
        if only_held is not None:
            parts.append(_good_routes(good, spec, areas, {area.area_id: price for area, price in zip(areas, seen)},
                                      carriage, interest_rate, _areas_holding(area_map, good, only_held[good])))
            continue
        parts.append(merchants_route_memo.routes_for_good(
            carriage, good, areas, spec, tuple(seen), interest_rate,
            lambda: _good_routes(good, spec, areas, {area.area_id: price for area, price in zip(areas, seen)},
                                 carriage, interest_rate)))
    def by_rank(rows):
        return sorted(rows, key=lambda row: (row[0], row[1], row[2].area_id))

    if only_held is not None:      # a partial search stays out of the memo the full searches share
        return by_rank([row for part in parts for row in part])
    return merchants_route_memo.sorted_rows(carriage, parts, by_rank)


def _areas_holding(area_map, good, held) -> set:
    """Ids of the good's areas holding any of `held` ((tile, quantity) pairs)."""
    found = set()
    for tile, _quantity in held:
        try:
            found.add(area_map.area_of(good, tile))
        except KeyError:                       # a tile outside every area
            pass
    return found


def _good_routes(good, spec, areas, prices, carriage, interest_rate, source_ids=None) -> list:
    """The unsorted rows of `_candidate_routes` for one good, given its price in each area; with `source_ids`
    only the rows of those source areas."""
    rows = []
    years_between = merchants_transit.years_between
    kept_years = merchants_transit.years_kept_for(carriage)    # years_between's memo for this table; None when it keeps none
    interest = max(0.0, interest_rate)
    spoilage = min(1.0, max(0.0, spec.spoilage_per_year))
    keep = 1.0 - spoilage
    unit_mass = spec.unit_mass_kg
    priced = [(area, price) for area, price in zip(areas, map(prices.get, [area.area_id for area in areas])) if price]
    positive = [price for _area, price in priced if price > 0.0]
    if not positive or max(price for _area, price in priced) * keep - min(positive) * (
            1.0 + interest + MERCHANT_MARGIN_SHARE) <= 0.0:
        return rows      # even the dearest destination, kept after spoilage, cannot cover the cheapest source's floor cost
    # (minus price there, area id, price there, price there kept after spoilage, its spoilage cost, anchor tile, area),
    # dearest first
    dearest_first = sorted([(-price, area.area_id, price, price * keep, price * spoilage, area.anchor_tile, area)
                            for area, price in priced])
    dearest_kept = dearest_first[0][3]
    for source in areas:
        if source_ids is not None and source.area_id not in source_ids:
            continue
        price_here = prices[source.area_id]
        if not price_here or price_here <= 0.0:
            continue
        floor_cost = price_here * (1.0 + interest + MERCHANT_MARGIN_SHARE)
        if dearest_kept - floor_cost <= 0.0:
            continue                                       # no destination, however near, covers this source's floor cost
        best = None
        best_net = -math.inf
        best_years = 1
        storage_a_year = merchants_transit.storage_per_unit(spec, 2)    # one extra year's storage
        interest_here = price_here * interest              # the terms of gap_cost_per_unit, hoisted
        margin_here = MERCHANT_MARGIN_SHARE * price_here
        source_tile = source.anchor_tile
        cost_to_get = carriage.costs_from(source_tile).get
        worth_beating = 0.0                                # no cheaper destination can beat this (the best net so far, once positive)
        for _minus, _area_id, price_there, kept_there, spoilage_there, anchor_tile, destination in dearest_first:
            # carriage only adds cost, so no cheaper destination can beat this bound
            if kept_there - floor_cost <= worth_beating:
                break
            # the source's own area nets a loss (equal prices, positive margin) and an unreachable tile nets -inf
            per_tonne = cost_to_get(anchor_tile, math.inf)
            net = price_there - price_here - (per_tonne * unit_mass / KILOGRAMS_PER_TONNE
                                              + interest_here + spoilage_there + margin_here)
            if net > 0.0:       # a haul held more years pays interest and spoilage for each
                held_years = kept_years.get((source_tile, anchor_tile)) if kept_years is not None else None
                if held_years is None:
                    held_years = years_between(carriage, source_tile, anchor_tile)
                if held_years > 1:
                    net -= (interest_here + storage_a_year) * (held_years - 1) + price_there * (
                        merchants_transit.lost_share(spec.spoilage_per_year, held_years) - spoilage)
                if net > worth_beating:
                    best, best_net, best_years = (destination, per_tonne), net, held_years
                    worth_beating = net
        if best is None:
            continue
        destination, per_tonne = best
        carriage_per_unit = per_tonne * unit_mass / KILOGRAMS_PER_TONNE
        outlay = price_here + carriage_per_unit
        rows.append((-best_net / outlay, good, source, destination, price_here, outlay,
                     _break_even_price(spec, prices[destination.area_id], carriage_per_unit, interest_rate, best_years)))
    return rows


def _break_even_price(spec: GoodSpec, price_there: float, carriage_per_unit: float, interest_rate: float,
                      years: int = 1) -> float:
    """The source price at which the gap just covers carriage, interest, spoilage and margin
    (gap_cost_per_unit solved for the price here): above it the trade loses money."""
    kept = price_there * (1.0 - merchants_transit.lost_share(spec.spoilage_per_year, years)) - carriage_per_unit
    kept -= merchants_transit.storage_per_unit(spec, years)
    return max(0.0, kept) / (1.0 + max(0.0, interest_rate) * years + MERCHANT_MARGIN_SHARE)


def held_by_good(held_stock) -> Dict[GoodId, List[Tuple[TileId, float]]]:
    """Held stock as {good: [(tile, quantity)]}, in the stock's own order."""
    index: Dict[GoodId, List[Tuple[TileId, float]]] = {}
    for (good, tile), quantity in held_stock.items():
        index.setdefault(good, []).append((tile, quantity))
    return index


def shared_room(merchant, good, source, destination, held_stock, own: RouteShares, group: RouteShares,
                held_index=None) -> float:
    """Units this merchant may still bid for into a destination: its share of the expected volume less
    what it holds there and has bid for already, and merchants' share of it less what they have bid.
    `held_index` is `held_by_good(held_stock)` when the caller asks many times."""
    if held_index is None:
        held_index = held_by_good(held_stock)
    held = 0
    held_here = held_index.get(good)
    if held_here:
        held = sum(quantity for tile, quantity in held_here if tile in destination.tiles)
    if merchant.in_transit:
        held += sum(each.quantity for each in merchant.in_transit if each.good == good and each.destination_tile in destination.tiles)
    return room_left(merchant.expected_volumes, good, source.area_id, destination.area_id, MERCHANT_MARKET_SHARE,
                     own, group, held)


def dispatch(merchant: Merchant, fills: Sequence[Fill], carriage: CarriageTable,
             specs: Mapping[GoodId, GoodSpec], currency: CurrencyId, cash: float,
             held_stock: Mapping[Tuple[GoodId, TileId], float],
             carrier_of: Callable[[TileId], Optional[AgentId]] = lambda _tile: EDGE_CARRIAGE,
             crew: Optional[CrewHire] = None,
             carrier_money: Optional[Callable[[TileId, TileId], float]] = None) -> Dispatch:
    """Carry what the merchant holds on each route's source tile (this year's purchases and older stock)
    to the route's destination, paying carriage from `cash` to `carrier_of(source tile)` (the edge when
    it names nobody). `fills` are not needed: what settled is what is held.
    With `crew`, a shipment's crew hours (the hours its haul needs of each trade at the tile, `hours_per_tonne`)
    must have been hired: a route is cut by the share hired of its scarcest crew hours, and the fee is paid
    less the crew's wages, which the labour market has already paid; with `carrier_money(source, destination)`
    (what the carriers a tonne wears cost) the merchant buys them in the goods market, so the fee is paid
    less that too."""
    shipments = []
    remaining = max(0.0, cash)
    wanted: Dict[str, float] = {}
    worth: Dict[str, float] = {}
    for (good, tile), route in sorted(merchant.routes.items()):
        if route[0] == tile:
            continue
        tonnes_per_unit = specs[good].unit_mass_kg / KILOGRAMS_PER_TONNE
        per_unit = carriage.cost_per_tonne(tile, route[0]) * tonnes_per_unit
        crew_rows = () if crew is None else tuple((key, hours * tonnes_per_unit)
                                                  for key, hours in crew.hours_per_tonne(tile, route[0]))
        crew_money = 0.0 if crew is None else min(per_unit, math.fsum(hours * crew.wage.get(key, 0.0)
                                                                      for key, hours in crew_rows))
        quantity = held_stock.get((good, tile), 0.0)
        if carrier_money is not None:
            crew_money += min(max(0.0, per_unit - crew_money), carrier_money(tile, route[0]) * tonnes_per_unit)
        net_unit = per_unit - crew_money
        affordable = quantity if net_unit <= 0.0 else min(quantity, remaining / net_unit)
        route_hours = math.fsum(hours for _key, hours in crew_rows)
        crew_part = per_unit
        if crew is not None and crew_rows and crew.reference_wage > 0.0:      # feed, carts and animals are paid to others, so only the crew's part of the fee is what its hours stand for (rates not priced at a wage: all of it)
            others_part = max(0.0, carriage.unscaled_cost_per_tonne(tile, route[0]) * tonnes_per_unit
                              - route_hours * crew.reference_wage)
            crew_part = max(0.0, per_unit - others_part)
        for key, hours in crew_rows:      # shared by the route's hours
            wanted[key] = wanted.get(key, 0.0) + quantity * hours
            worth[key] = worth.get(key, 0.0) + quantity * crew_part * hours / route_hours
        shipments.append([good, tile, route, quantity, affordable, per_unit, crew_money, crew_rows])
        remaining -= affordable * net_unit
    cut: Dict[str, float] = {}       # the share of a crew key's hours that was hired, where it falls short
    if crew is not None and crew.hours_hired is not None:
        needed: Dict[str, float] = {}
        for row in shipments:
            for key, hours in row[7]:
                needed[key] = needed.get(key, 0.0) + row[4] * hours
        cut = {key: max(0.0, crew.hours_hired.get(key, 0.0)) / total for key, total in needed.items()
               if total > crew.hours_hired.get(key, 0.0)}
    moves, transfers, stranded = [], [], []
    purse = max(0.0, cash) * (1.0 - PURSE_ROUNDING_MARGIN)
    for good, tile, route, quantity, affordable, per_unit, crew_money, crew_rows in shipments:
        carried = affordable * min([cut[key] for key, _hours in crew_rows if key in cut], default=1.0)
        if carried < quantity:
            stranded.append((good, tile, quantity - carried))
        if carried <= 0.0:
            continue
        years = merchants_transit.years_between(carriage, tile, route[0])
        if years > 1:      # the haul outlasts the year: it waits on the road and arrives in the year its days put it in
            merchant.in_transit.append(merchants_transit.Shipment(good, carried, route[0], years - 1))
        moves.append(DeliveredMove(merchant.agent_id, merchants_transit.EDGE_TRANSIT if years > 1 else merchant.agent_id,
                                   good, tile, carried, "carried to market", route[0]))
        fee = max(0.0, min(carried * (per_unit - crew_money), purse))      # never above the purse, and a rounding sliver below zero is not cash paid back
        purse -= fee
        if fee > 0.0:
            transfers.append(Transfer(merchant.agent_id, carrier_of(tile) or EDGE_CARRIAGE, currency, fee,
                                      "carriage of %s" % good))
    return Dispatch(tuple(moves), within_purse(transfers, cash), tuple(stranded), wanted, worth)


def close_year(merchant: Merchant, prices: Mapping[Tuple[GoodId, AreaId], float],
               volumes: Mapping[Tuple[GoodId, AreaId], float], cash: float,
               held_stock: Mapping[Tuple[GoodId, TileId], float],
               area_of: Callable[[GoodId, TileId], AreaId], currency: CurrencyId,
               interest_rate: float, ordered: Optional[Tuple[Sequence, Sequence]] = None,
               lag_years: Callable[[GoodId, AreaId], Optional[int]] = lambda good, area: 0) -> Tuple[Transfer, ...]:
    """Update expectations from this year's clearing prices and volumes (by (good, area)), then settle
    the year's profit (wealth, cash plus stock at expected prices, above the capital base). While
    trading earns more on its capital than the interest rate, the owner takes a share and the rest
    becomes capital; otherwise the owner takes all of it. A loss shrinks the capital. `ordered` is the
    sorted items of `prices` and of `volumes`, for a caller closing many merchants on the same year.
    A price from a market `lag_years(good, area)` years of news away is learned that many years late; a market
    with no lag (None: its area no longer exists in the current map) is not heard from."""
    if ordered is None:
        ordered = (sorted(prices.items()), sorted(volumes.items()))
    expected_prices, speed = merchant.expected_prices, MERCHANT_EXPECTATION_SPEED
    for key, value in ordered[0]:
        lag = lag_years(*key)
        if lag is None:
            continue
        news = value if lag <= 0 else merchants_transit.heard(merchant, key, value, lag)
        if news is not None:           # `_expect`, inline: this runs for every market every year
            old = expected_prices.get(key)
            expected_prices[key] = news if old is None else old + speed * (news - old)
    expected_volumes = merchant.expected_volumes
    for key, value in ordered[1]:
        old = expected_volumes.get(key)
        expected_volumes[key] = value if old is None else old + speed * (value - old)
    stock_value = math.fsum(quantity * merchant.expected_prices.get((good, area_of(good, tile)), 0.0)
                            for (good, tile), quantity in held_stock.items() if quantity > 0.0)
    stock_value += math.fsum(each.quantity * merchant.expected_prices.get((each.good, area_of(each.good, each.destination_tile)), 0.0)
                             for each in merchant.in_transit)
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


def _expect(expectation: Dict, key, value: float) -> None:
    old = expectation.get(key)
    expectation[key] = value if old is None else old + MERCHANT_EXPECTATION_SPEED * (value - old)
