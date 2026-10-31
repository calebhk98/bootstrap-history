"""A merchant's fleet in the book: what it holds, the capacity of others it hires, what the carriers it needs cost to
keep, and the fleets merchants open with (Complaints/631). The arithmetic is carriage_fleet's; the wear of the
held carriers by service life is booked with every other durable (year_close.wear_and_spoilage).
"""
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import carriage_fleet, carriage_wear, merchants_legs
from .carriage_fleet import FleetLimit
from .merchants import MERCHANT_BID_ELASTICITY
from .types import AgentId, Bid, EDGE_PRODUCTION, GoodId, GoodsMove, Transfer

FLEET_OPENING_TILES = 12     # populated tiles a merchant's opening hauls are averaged over, the most populous first
FLEET_OPENING_REASON = "opening stock of a durable in use"


def fleet_lives(setup) -> Dict[GoodId, float]:
    """{carrier good: service life in years} of each carrier good a merchant holds (a feed that is eaten has none)."""
    lives = {good: setup.specs[good].service_life_years for good in carriage_wear.carrier_goods(setup) if good in setup.specs}
    return {good: life for good, life in lives.items() if life > 0.0}


def held(book, merchant_id: AgentId, goods: Sequence[GoodId]) -> Dict[GoodId, float]:
    """Units of each carrier good the merchant keeps in its carrier account."""
    mine = book.holdings(carriage_wear.account(merchant_id))["goods"]
    return {good: math.fsum(mine.get(good, {}).values()) for good in goods}


def keep(merchant, book, goods: Sequence[GoodId]) -> None:
    """Put the carriers the merchant bought into its carrier account."""
    carriage_wear.settle(merchant, book, goods, {})


def own_capacity(book, merchant_id: AgentId, lives: Mapping[GoodId, float]) -> Dict[GoodId, float]:
    """Units of wear a year each fleet good the merchant holds can bear (every fleet good: none held is zero)."""
    units = held(book, merchant_id, sorted(lives))
    return {good: units.get(good, 0.0) / lives[good] for good in lives}


def limit_for(wear, own: Mapping[GoodId, float], hired: Mapping[GoodId, float]) -> FleetLimit:
    """The limit on a merchant's dispatch: its own capacity and what it hired."""
    return FleetLimit(wear.units_per_tonne, {good: units + hired.get(good, 0.0) for good, units in own.items()})


def wear_needed(merchant, held_stock: Mapping[Tuple[GoodId, str], float], specs, wear, goods) -> Dict[GoodId, float]:
    """Units of wear a year of each fleet good in `goods` that carrying the stock on the merchant's routes puts on it."""
    needed: Dict[GoodId, float] = {}
    for (good, tile), legs in sorted(merchant.routes.items()):
        held = held_stock.get((good, tile), 0.0)
        for destination, _area, quantity in merchants_legs.split(legs, held):
            if destination == tile or quantity <= 0.0:
                continue
            tonnes = quantity * specs[good].unit_mass_kg / 1000.0
            for carrier, units in wear.units_per_tonne(tile, destination).items():
                if carrier in goods:
                    needed[carrier] = needed.get(carrier, 0.0) + tonnes * units
    return needed


def share_idle(capacity: Mapping[AgentId, Mapping[GoodId, float]],
               needed: Mapping[AgentId, Mapping[GoodId, float]]) -> Tuple[Dict[AgentId, Dict[GoodId, float]], Dict[GoodId, Dict[AgentId, float]]]:
    """The idle capacity of merchants whose fleet bears more wear than their routes need, lent to those short of it.
    Returns ({lessee: {good: wear hired}}, {good: {lessor: wear lent}}); when more is wanted than is idle, every
    lessee gets the same share of what it lacks."""
    hired: Dict[AgentId, Dict[GoodId, float]] = {}
    lent: Dict[GoodId, Dict[AgentId, float]] = {}
    goods = sorted({good for each in capacity.values() for good in each})
    for good in goods:
        idle = {agent: capacity[agent].get(good, 0.0) - needed.get(agent, {}).get(good, 0.0) for agent in capacity}
        spare = {agent: gap for agent, gap in idle.items() if gap > 0.0}
        short = {agent: -gap for agent, gap in idle.items() if gap < 0.0}
        total_spare, total_short = math.fsum(spare.values()), math.fsum(short.values())
        if total_spare <= 0.0 or total_short <= 0.0:
            continue
        filled = min(1.0, total_spare / total_short)
        for agent, lack in short.items():
            hired.setdefault(agent, {})[good] = lack * filled
        lent[good] = {agent: gap / total_spare * filled * total_short for agent, gap in spare.items()}
    return hired, lent


def rent_transfers(lessee: AgentId, hired: Mapping[GoodId, float], used: Mapping[GoodId, float],
                   own: Mapping[GoodId, float], lent: Mapping[GoodId, Mapping[AgentId, float]],
                   prices: Mapping[GoodId, float], currency: str, cash: float) -> List[Transfer]:
    """What a lessee pays the merchants it hired from: the wear its shipments put beyond its own fleet (at most what
    it hired) at the price of the carrier, shared by the wear each lessor lent; never above `cash`."""
    owed: Dict[AgentId, float] = {}
    for good, units in sorted(hired.items()):
        beyond = min(units, max(0.0, used.get(good, 0.0) - own.get(good, 0.0)))
        total = math.fsum(lent.get(good, {}).values())
        if beyond <= 0.0 or total <= 0.0:
            continue
        for lessor, amount in lent[good].items():
            owed[lessor] = owed.get(lessor, 0.0) + beyond * prices.get(good, 0.0) * amount / total
    sum_owed = math.fsum(owed.values())
    scale = min(1.0, max(0.0, cash) / sum_owed) if sum_owed > 0.0 else 0.0
    return [Transfer(lessee, lessor, currency, money * scale, "carriers hired") for lessor, money in sorted(owed.items())
            if money * scale > 0.0]


def opening_fleet(setup, record, wear, final_value_per_tonne: float) -> List[GoodsMove]:
    """The carriers each merchant opens holding: enough to carry its capital's worth of goods (at the value a tonne
    of the opening's goods has) the average haul from its home tile to the populous tiles, the fleet's wear a year
    over its service life. Placed with the other opening durables."""
    lives = fleet_lives(setup)
    if not lives or final_value_per_tonne <= 0.0:
        return []
    tiles = sorted(setup.opening_population_by_tile, key=lambda tile: (-setup.opening_population_by_tile[tile], tile))[:FLEET_OPENING_TILES]
    moves: List[GoodsMove] = []
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        tonnes = merchant.capital_base / final_value_per_tonne
        hauls = [wear.units_per_tonne(merchant.home_tile, tile) for tile in tiles if tile != merchant.home_tile]
        if not hauls:
            continue
        for good, life in sorted(lives.items()):
            per_tonne = math.fsum(each.get(good, 0.0) for each in hauls) / len(hauls)
            units = tonnes * per_tonne * life
            if units > 0.0:
                moves.append(GoodsMove(EDGE_PRODUCTION, carriage_wear.account(merchant.agent_id), good, merchant.home_tile,
                                       units, FLEET_OPENING_REASON))
    return moves


def endow(setup, record, carriage, prices: Mapping[GoodId, float], final_by_tile) -> None:
    """Give the merchants their opening fleets, sized to the opening's trade: a tonne of what the households buy is
    worth the national demand's value over its mass."""
    if not carriage_wear.wears(setup):
        return
    totals: Dict[GoodId, float] = {}
    for demand in final_by_tile.values():
        for good, quantity in demand.items():
            totals[good] = totals.get(good, 0.0) + quantity
    tonnes = math.fsum(quantity * setup.specs[good].unit_mass_kg / 1000.0 for good, quantity in totals.items() if good in setup.specs)
    value = math.fsum(quantity * prices.get(good, 0.0) for good, quantity in totals.items())
    if tonnes <= 0.0:
        return
    moves = opening_fleet(setup, record, carriage_wear.Wear(setup, carriage, record.area_imbalance), value / tonnes)
    if moves:
        record.book.move_many(moves)


def to_buy(setup, record, merchant) -> Dict[GoodId, float]:
    """Units of each carrier good the merchant bids for (see `bids`)."""
    lives = fleet_lives(setup)
    holding = held(record.book, merchant.agent_id, sorted(lives))
    wanted = carriage_fleet.wanted_fleet(merchant.carrier_fleet_wanted, lives)
    found = {good: max(0.0, wanted.get(good, 0.0) - holding.get(good, 0.0)) for good in lives}
    found.update({good: units for good, units in (merchant.carrier_wear or {}).items() if good not in lives})
    return found


def bids(setup, record, view, area_map, merchants_cash: Optional[Dict[str, float]] = None) -> Tuple[List[Bid], Dict[str, float]]:
    """Each merchant's bids for the carriers it is short of, delivered to its home tile, and the money each bid
    sets aside ({merchant: budget}), which the caller takes off the cash the merchant trades with. A carrier with a
    life is bid for up to the fleet its routes called for last year (`carrier_fleet_wanted`) less what it holds, so a
    paying haul buys carriers and age is replaced; a feed, for the units last year's shipments used up."""
    found: List[Bid] = []
    budget: Dict[str, float] = {}
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        for good, units in sorted(to_buy(setup, record, merchant).items()):
            if units <= 0.0 or good not in area_map.goods():
                continue
            area = area_map.area_of(good, merchant.home_tile)
            price = view.price(good, area) or setup.opening_prices.get(good, 0.0)
            if price <= 0.0 or not math.isfinite(price):
                continue
            money = min(units * price, max(0.0, (merchants_cash or {}).get(merchant.agent_id, math.inf)) - budget.get(merchant.agent_id, 0.0))
            if money <= 0.0:
                continue
            found.append(Bid(merchant.agent_id, good, area, merchant.home_tile, units, 0.0, price,
                             MERCHANT_BID_ELASTICITY, money))
            budget[merchant.agent_id] = budget.get(merchant.agent_id, 0.0) + money
    return found, budget


