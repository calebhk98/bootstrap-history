"""Merchants: agents that buy where a good is cheap and hold it where it is dear.

The year is annual, so a merchant acts on last year's prices. In one year it
  1. `orders`    offers what it already holds at a destination, at the holding reservation of the price
                 it expects there; bids in cheap areas for goods whose expected price in another area
                 exceeds the price here plus carriage, a year's interest on the money tied up, the
                 spoilage of the held stock and a margin. Quantities are limited by cash and by a share
                 of the destination's expected market net of what it already holds there and has bid for
                 from other sources; merchants sizing one after another also share the destination
                 (`merchants_shares`). Merchants chasing one gap still overshoot it within those limits.
                 Every destination whose haul pays is a route: cash goes to routes by profit per unit of
                 outlay, and what is bought at a source is carried to each destination in proportion to
                 what was bought for it (`merchants_legs`).
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

from . import carriage_fleet, inventory, merchant_figures, merchants_news, merchants_plan, route_dues, merchants_legs, merchants_route_memo, merchants_search, merchants_transit
from sim.book import DeliveredMove
from .households_orders import BUDGET_SAFETY_SHARE
from .market_areas import AreaMap
from .market_tables import MarketTables
from .merchants_shares import RouteShares, room_left
from .protocols import AgentOrders, MarketView
from .tile_costs import CarriageTable
from .types import AgentId, AreaId, Bid, CurrencyId, GoodId, GoodSpec, Offer, TileId, Transfer
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


FIGURE_FIELDS = ("expected_prices", "expected_volumes")     # held as `merchant_figures.MarketFigures`; a mapping assigned to one is copied into it


@dataclass
class Merchant:
    agent_id: AgentId
    home_tile: TileId                    # where it keeps its purse; stocks sit on destination tiles
    owner: AgentId                       # who receives its profit
    capital_base: float                  # capital staked in trade; profit is wealth above it
    expected_prices: Dict[Tuple[GoodId, AreaId], float] = field(default_factory=dict)     # a column by goods market (`merchant_figures`); NaN: none
    expected_volumes: Dict[Tuple[GoodId, AreaId], float] = field(default_factory=dict)    # the same, of the volume it expects a market to trade
    routes: Dict[Tuple[GoodId, TileId], Tuple[merchants_legs.Leg, ...]] = field(default_factory=dict)   # (good, source tile) -> legs (destination tile, area, weight): what it holds there is shared over them by weight
    carriage_hours_wanted: Optional[Dict[str, float]] = None   # crew hours its shipments needed last year, by (trade, source tile) market key: this year's bid for carriers; None until it has shipped
    carriage_money_wanted: Dict[str, float] = field(default_factory=dict)   # the carriage money those hours stand for, by the same key: the most an hour is worth to it
    carrier_wear: Dict[str, float] = field(default_factory=dict)   # carrier units its shipments wore last year, by good (carriage_wear): this year's bid for carriers
    carrier_fleet_wanted: Dict[str, float] = field(default_factory=dict)   # wear a year its routes' stock called for last year, less what it hired, by carrier good (carriage_fleet): the fleet it bids to hold
    in_transit: List[merchants_transit.Shipment] = field(default_factory=list)   # hauls still on the road (their goods wait in the transit account)
    price_history: Dict[Tuple[GoodId, AreaId], List[float]] = field(default_factory=dict)   # prices of distant markets that news has not yet reached it, newest last

    def __setattr__(self, name, value) -> None:
        """A mapping assigned to an expectation is copied into its column (keeping the numbering it is indexed by, if it has one)."""
        if name not in FIGURE_FIELDS or isinstance(value, merchant_figures.MarketFigures):
            object.__setattr__(self, name, value)
            return
        held = self.__dict__.get(name)
        if held is not None:
            held.replace_all(value)
            return
        object.__setattr__(self, name, merchant_figures.MarketFigures(None, value))


def bind_markets(merchant: Merchant, tables: MarketTables) -> None:
    """Index the merchant's figures by this goods-market numbering (the record's), keeping what it holds."""
    for name in FIGURE_FIELDS:
        getattr(merchant, name).bind(tables)


@dataclass(frozen=True)
class CrewHire:
    """The carriers a merchant hired for the year. `hours_per_tonne(source, destination)` is the crew a tonne
    needs on that haul, as ((crew key, hours),) where a key names a trade and the tile it is hired at; `hours_hired`
    the hours hired by key (None: no plan to hire for yet, so the shipments are not limited) and `wage` their
    average pay an hour by key (already paid in the labour market; a key with nothing hired has none). `market_wage(key)` is what an hour of that crew
    key was last paid in its market (the pay inside a fee, whether or not any was hired this year) and
    `area_of(good, tile)` the price area of a tile, to read the merchant's expected prices at the haul's ends."""
    hours_per_tonne: Callable[[TileId, TileId], Tuple[Tuple[str, float], ...]]
    hours_hired: Optional[Mapping[str, float]]
    wage: Mapping[str, Optional[float]]
    market_wage: Callable[[str], float]     # `carriage_hours.crew_wage`
    area_of: Callable[[GoodId, TileId], AreaId]


@dataclass(frozen=True)
class Dispatch:
    moves: Tuple[DeliveredMove, ...]
    transfers: Tuple[Transfer, ...]
    crew_hours_wanted: Dict[str, float] = field(default_factory=dict)   # by crew key, before any cut for want of carriers
    crew_money_wanted: Dict[str, float] = field(default_factory=dict)   # the carriage money those hours stand for, by crew key
    fleet_wanted: Dict[str, float] = field(default_factory=dict)   # wear a year the routes' stock called for, by carrier good, before any cut for want of carriers
    dues: Tuple[Transfer, ...] = ()     # the route dues paid to the holders' accounts (route_dues.py), apart from the fee


def put_merchant(table: Dict[AgentId, Merchant], merchant: Merchant, tables: Optional[MarketTables] = None) -> None:
    """`merchant` is the table's row for its id (`record.merchants` is written only by this module and merchants_dispatch);
    with `tables` (the record's market memory numbering) its figures are indexed by that numbering."""
    if tables is not None:
        bind_markets(merchant, tables)
    table[merchant.agent_id] = merchant


def remap_to_areas(merchant: Merchant, expected_prices, expected_volumes, price_history, routes) -> None:
    """What the merchant expects and the routes it plans, rewritten over the market areas that replaced the old ones."""
    merchant.expected_prices = expected_prices      # figures already indexed as the merchant's are kept as they are
    merchant.expected_volumes = expected_volumes
    merchant.price_history = price_history
    merchant.routes = routes


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
    """What the merchant expects a market to pay for its good: its own expectation, else the planning price. A seller
    reads what buyers will pay, a bid ceiling included, so it follows unmet demand (`year_close.learned_prices`); a
    buyer of goods or carriers reads `offered_price`, what is on offer to buy."""
    price = merchant.expected_prices.get((good, area))
    return price if price is not None else view.price(good, area)


def orders(merchant: Merchant, view: MarketView, carriage: CarriageTable, area_map: AreaMap, cash: float,
           held_stock: Mapping[Tuple[GoodId, TileId], float], specs: Mapping[GoodId, GoodSpec],
           interest_rate: float, shares: Optional[RouteShares] = None, route=None) -> AgentOrders:
    """The merchant's offers and bids for the year. Sets `merchant.routes`. `shares` is what rival
    merchants have already committed this year; this merchant adds its own to it. Many merchants sized in one
    pass share `route` (`merchants_book.route_pass`) and `merchants_book.DenseShares` (`merchants_plan.orders`)."""
    return merchants_plan.orders(merchant, view, carriage, area_map, cash, held_stock, specs, interest_rate, shares, route)


def ships_held_stock(merchant: Merchant, held_stock: Mapping[Tuple[GoodId, TileId], float]) -> bool:
    """Whether some route of the merchant starts at a tile where it holds stock, bought this year or not."""
    return any(held_stock.get(key, 0.0) > 0.0 for key in merchant.routes)


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


def candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate, only_held=None):
    """Rows (rank, good, source, destination, price here, outlay per unit, most it pays), one per
    profitable (good, source area) at its best destination, best net gap per unit of outlay first.
    With `only_held` (`held_by_good` of stock) the rows of the goods held, from the source areas holding
    them alone: each such row is the row the full search gives.
    A good's rows are shared with any caller that sees the same prices at the same rate."""
    parts = []
    expected_by_good: dict = {}
    for (good, area_id), price in merchant.expected_prices.items():
        if price is not None:
            by_area = expected_by_good.get(good)
            if by_area is None:
                by_area = expected_by_good[good] = {}
            by_area[area_id] = price
    for good in sorted(set(specs) & set(area_map.goods()) if only_held is None
                       else set(specs) & set(area_map.goods()) & set(only_held)):
        areas = area_map.areas(good)
        if len(areas) < 2:
            continue
        spec = specs[good]
        seen = view.prices_across(good, areas)
        expected = expected_by_good.get(good, {})
        # an expectation stands in for last year's price where the merchant has one; without one it sees
        # last year's price only where the news has had time to reach it, and nothing of a farther market
        current = merchants_search.news_current_flags(good, areas, carriage, merchant.home_tile)
        seen = [expected[area.area_id] if area.area_id in expected
                else (price if reached else None)
                for area, price, reached in zip(areas, seen, current)]
        if only_held is not None:
            parts.append(_good_routes(good, spec, areas, {area.area_id: price for area, price in zip(areas, seen)},
                                      carriage, interest_rate, _areas_holding(area_map, good, only_held[good])))
            continue
        parts.append(merchants_route_memo.routes_for_good(
            carriage, good, areas, spec, tuple(seen), interest_rate,
            lambda: _good_routes(good, spec, areas, {area.area_id: price for area, price in zip(areas, seen)},
                                 carriage, interest_rate)))
    def by_rank(rows):
        return sorted(rows, key=lambda row: (row[0], row[1], row[2].area_id, row[3].area_id))

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
    """The unsorted rows of `candidate_routes` for one good, given its price in each area: one for every
    (source, destination) whose haul pays; with `source_ids` only the rows of those source areas."""
    return merchants_search.good_routes(good, spec, areas, prices, carriage, interest_rate, MERCHANT_MARGIN_SHARE,
                                        source_ids)


def _break_even_price(spec: GoodSpec, price_there: float, carriage_per_unit: float, interest_rate: float,
                      years: int = 1) -> float:
    """The source price at which the gap just covers carriage, interest, spoilage and margin
    (the net gap of `_good_routes` solved for the price here): above it the trade loses money."""
    kept = price_there * (1.0 - merchants_transit.lost_share(spec.spoilage_per_year, years)) - carriage_per_unit
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


def dispatch(merchant: Merchant, carriage: CarriageTable,
             specs: Mapping[GoodId, GoodSpec], currency: CurrencyId, cash: float,
             held_stock: Mapping[Tuple[GoodId, TileId], float],
             carrier_of: Callable[[TileId], Optional[AgentId]] = lambda _tile: EDGE_CARRIAGE,
             crew: Optional[CrewHire] = None,
             carrier_money: Optional[Callable[[TileId, TileId], Optional[float]]] = None,
             margin_kept: bool = False,
             fleet: Optional[carriage_fleet.FleetLimit] = None,
             dues: Optional[Callable[[TileId, TileId], Mapping[str, float]]] = None) -> Dispatch:
    """Carry what the merchant holds on each route's source tile (this year's purchases and older stock)
    to the route's destination, paying carriage from `cash` to `carrier_of(source tile)` (the edge when
    it names nobody).
    With `crew`, a shipment's crew hours (the hours its haul needs of each trade at the tile, `hours_per_tonne`)
    must have been hired: a route is cut by the share hired of its scarcest crew hours, and the fee is paid
    less the crew's wages, which the labour market has already paid; with `carrier_money(source, destination)`
    (what the carriers a tonne wears and the animals eat cost) the merchant buys them in the goods market, so the
    fee is paid less that too. With `margin_kept` the rest of the fee (the carriers' interest, their losses and
    the margin) stays with the merchant that owns the carriers and is paid to nobody; only crew pay owed for
    hours not yet hired (the first year of shipping, which has no plan) still goes to `carrier_of`, as before.
    With `fleet`, routes also share the carriers the merchant holds or hired: a route carries no more tonnes than
    the wear its scarcest carrier good has left allows, in route order.
    With `dues` ({holder: money per tonne} on a haul), the merchant pays the haul's tolls and port dues to each holder's
    account, in money, out of the fee: they are no part of the crew's hours or of what the owner keeps. A purse that
    cannot cover a shipment's dues and fee pays the dues first and the carrier what remains."""
    shipments = []
    planned_spare = None if fleet is None else dict(fleet.capacity)     # wear left if every route were carried at its planned size
    fleet_wanted: Dict[str, float] = {}
    remaining = max(0.0, cash)
    wanted: Dict[str, float] = {}
    worth: Dict[str, float] = {}
    hauls = [(good, tile, (destination, area), quantity)
             for (good, tile), legs in sorted(merchant.routes.items())
             for destination, area, quantity in merchants_legs.split(legs, held_stock.get((good, tile), 0.0))]
    for good, tile, route, quantity in hauls:
        if route[0] == tile:
            continue
        tonnes_per_unit = specs[good].unit_mass_kg / KILOGRAMS_PER_TONNE
        per_unit = carriage.cost_per_tonne(tile, route[0]) * tonnes_per_unit
        crew_rows = () if crew is None else tuple((key, hours * tonnes_per_unit)
                                                  for key, hours in crew.hours_per_tonne(tile, route[0]))
        crew_wages = {} if crew is None else {key: crew.market_wage(key) for key, _hours in crew_rows}
        # the wages already paid inside the fee: the hours hired, at what they were paid; a row nothing was hired for has none
        crew_money = 0.0 if crew is None else min(per_unit, math.fsum(
            hours * crew.wage[key] for key, hours in crew_rows if crew.wage.get(key) is not None))
        worn_money = None if carrier_money is None else carrier_money(tile, route[0])    # None: no carrier price to charge
        supplied_money = 0.0 if worn_money is None else min(max(0.0, per_unit - crew_money), worn_money * tonnes_per_unit)
        dues_unit = {} if dues is None else {holder: owed * tonnes_per_unit for holder, owed in dues(tile, route[0]).items()}
        payout_unit = max(0.0, per_unit - crew_money - supplied_money - math.fsum(dues_unit.values()))
        if margin_kept:     # what is left is the owner's: only crew pay for hours nobody was hired for is still paid out
            unhired = 0.0 if crew is None or crew.hours_hired is not None else math.fsum(
                hours * crew_wages[key] for key, hours in crew_rows)
            payout_unit = min(payout_unit, unhired)
        outlay_unit = payout_unit + math.fsum(dues_unit.values())
        capacity = quantity
        wear_per_tonne: Mapping[str, float] = {}
        if fleet is not None and tonnes_per_unit > 0.0:
            wear_per_tonne = fleet.units_per_tonne(tile, route[0])
            for carrier, units in wear_per_tonne.items():
                fleet_wanted[carrier] = fleet_wanted.get(carrier, 0.0) + quantity * tonnes_per_unit * units
            capacity = min(capacity, carriage_fleet.tonnes_within(planned_spare, wear_per_tonne) / tonnes_per_unit)
            for carrier in planned_spare:
                planned_spare[carrier] -= capacity * tonnes_per_unit * wear_per_tonne.get(carrier, 0.0)
        crew_hours = math.fsum(hours for _key, hours in crew_rows)
        gain = 0.0
        if crew is not None and crew_rows:      # what an hour is worth is the haul's gain once the fee's other parts (feed, carts, animals, tolls) are paid
            spread = (merchant.expected_prices.get((good, route[1]), 0.0)
                      - merchant.expected_prices.get((good, crew.area_of(good, tile)), math.inf))
            crew_pay = math.fsum(hours * crew_wages[key] for key, hours in crew_rows)
            gain = max(0.0, spread - max(0.0, per_unit - crew_pay)) if math.isfinite(spread) else 0.0
        for key, hours in crew_rows:      # shared by the route's hours
            wanted[key] = wanted.get(key, 0.0) + quantity * hours
            if crew_hours > 0.0:
                worth[key] = worth.get(key, 0.0) + quantity * gain * hours / crew_hours
        shipments.append([good, tile, route, quantity, capacity, outlay_unit, crew_rows, dues_unit,
                          payout_unit, tonnes_per_unit, wear_per_tonne])
    cut: Dict[str, float] = {}       # the share of a crew key's hours that was hired, where it falls short
    if crew is not None and crew.hours_hired is not None:
        needed: Dict[str, float] = {}
        for row in shipments:
            for key, hours in row[6]:
                needed[key] = needed.get(key, 0.0) + row[4] * hours
        cut = {key: max(0.0, crew.hours_hired.get(key, 0.0)) / total for key, total in needed.items()
               if total > crew.hours_hired.get(key, 0.0)}
    moves, transfers, dues_paid = [], [], []
    purse = max(0.0, cash) * (1.0 - PURSE_ROUNDING_MARGIN)
    spare = None if fleet is None else dict(fleet.capacity)     # wear the carts bear, drawn down by what is carried (the planned size above only sizes the crew hours)
    for good, tile, route, quantity, _planned, outlay_unit, crew_rows, dues_unit, payout_unit, tonnes_per_unit, wear_per_tonne in shipments:
        carried = quantity * min([cut[key] for key, _hours in crew_rows if key in cut], default=1.0)
        if spare is not None and tonnes_per_unit > 0.0:      # a route wears carts for what it carries, after the crew cut
            carried = min(carried, carriage_fleet.tonnes_within(spare, wear_per_tonne) / tonnes_per_unit)
        if outlay_unit > 0.0:      # cash is spent on what is carried, after the crew cut
            carried = min(carried, remaining / outlay_unit)
            remaining -= carried * outlay_unit
        if spare is not None:
            for carrier in spare:
                spare[carrier] -= carried * tonnes_per_unit * wear_per_tonne.get(carrier, 0.0)
        if carried <= 0.0:
            continue
        years = merchants_transit.years_between(carriage, tile, route[0])
        if years > 1:      # the haul outlasts the year: it waits on the road and arrives in the year its days put it in
            merchant.in_transit.append(merchants_transit.Shipment(good, carried, route[0], years - 1))
        moves.append(DeliveredMove(merchant.agent_id, merchants_transit.EDGE_TRANSIT if years > 1 else merchant.agent_id,
                                   good, tile, carried, "carried to market", route[0]))
        for holder, owed in sorted(dues_unit.items()):      # dues come out of the purse before the carrier's fee
            paid = max(0.0, min(carried * owed, purse))
            purse -= paid
            if paid > 0.0:
                dues_paid.append(Transfer(merchant.agent_id, route_dues.account(holder), currency, paid, "route dues on %s" % good))
        fee = max(0.0, min(carried * payout_unit, purse))      # never above the purse, and a rounding sliver below zero is not cash paid back
        purse -= fee
        if fee > 0.0:
            transfers.append(Transfer(merchant.agent_id, carrier_of(tile) or EDGE_CARRIAGE, currency, fee,
                                      "carriage of %s" % good))
    return Dispatch(tuple(moves), within_purse(transfers, cash), wanted, worth, fleet_wanted, tuple(dues_paid))


def learn_year(merchants: Sequence[Merchant], news: merchants_news.YearNews, lags: Sequence) -> None:
    """Move every merchant's expectations toward the year's prices and volumes (`close_year` with `learned=True` follows);
    `lags[i]` is `news.lags_at(...)` for `merchants[i]`."""
    merchants_news.learn_all(merchants, news, lags, MERCHANT_EXPECTATION_SPEED)


def close_year(merchant: Merchant, prices: Mapping[Tuple[GoodId, AreaId], float],
               volumes: Mapping[Tuple[GoodId, AreaId], float], cash: float,
               held_stock: Mapping[Tuple[GoodId, TileId], float],
               area_of: Callable[[GoodId, TileId], AreaId], currency: CurrencyId,
               interest_rate: float, news: Optional[merchants_news.YearNews] = None,
               lag_years: Callable[[GoodId, AreaId], Optional[int]] = lambda good, area: 0,
               lags=None, learned: bool = False) -> Tuple[Transfer, ...]:
    """Update expectations from this year's clearing prices and volumes (by (good, area)), then settle
    the year's profit (wealth, cash plus priced stock at expected prices, above the capital base; stock with no learned price
    is left out, and while any is held a shortfall is not booked as a loss). While
    trading earns more on its capital than the interest rate, the owner takes a share and the rest
    becomes capital; otherwise the owner takes all of it. A loss shrinks the capital. `news` is the year's prices
    and volumes sorted into arrays (`merchants_news.YearNews`), for a caller closing many merchants on the same year.
    A price from a market `lag_years(good, area)` years of news away is learned that many years late; a market
    with no lag (None: its area no longer exists in the current map) is not heard from. `lags` is that figure for
    each price of `news` (`YearNews.lags_at`), when the caller has it. With `learned` the caller has already moved the
    expectations (`learn_year`, for many merchants at once)."""
    if not learned:
        if news is None:
            news = merchants_news.YearNews(prices, volumes)
        merchants_news.learn(merchant, news, news.lags_by(lag_years) if lags is None else lags, MERCHANT_EXPECTATION_SPEED)
    # stock is valued at the expected price of its destination area; stock with no learned price there is left out
    # of wealth (the record holds no cost basis), and then a shortfall below the capital base is not taken as a loss
    held_stock_areas = [(good, area_of(good, tile), quantity) for (good, tile), quantity in held_stock.items() if quantity > 0.0]
    held_stock_areas += [(each.good, area_of(each.good, each.destination_tile), each.quantity) for each in merchant.in_transit]
    expected_prices = merchant.expected_prices
    stock_value = math.fsum(quantity * expected_prices[(good, area)] for good, area, quantity in held_stock_areas
                            if (good, area) in expected_prices)
    has_unpriced_stock = any((good, area) not in expected_prices for good, area, _quantity in held_stock_areas)
    wealth = cash + stock_value
    profit = wealth - merchant.capital_base
    if profit <= 0.0:
        if not has_unpriced_stock:
            merchant.capital_base = max(0.0, wealth)
        return ()
    earns_more = merchant.capital_base > 0.0 and profit / merchant.capital_base > interest_rate
    payout = min(max(0.0, cash), (MERCHANT_PROFIT_PAYOUT_SHARE if earns_more else 1.0) * profit)
    if earns_more:
        merchant.capital_base = wealth - payout
    if payout <= 0.0:
        return ()
    return (Transfer(merchant.agent_id, merchant.owner, currency, payout, "merchant profit"),)
