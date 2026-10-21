"""Carriers as durable goods: carriage wears the stock of carts, pack saddles, animals and hulls that a mode uses,
and the merchants buy them back in the goods market. The feed the team's animals eat is used up the same way
(a row with no life: eaten by the tonne-km), so a merchant buys it in the goods market too.

A mode's team (a cart and its two oxen, a string of mules with their saddles, a hull) moves a known tonne-km
a working day (geography). A unit of a carrier good works `days_per_year` days a year for its service life, so
one tonne-km wears `count in the team / (life years * days per year * tonne-km per team-day)` units of it.
A merchant keeps its carriers in an account of their own (`account`), wears them by the tonne-km it carried, and
next year bids for as many units as this year wore (the unit shortfall, when it held fewer, is still the plan).
Fleets sized to the route's days, and an opening endowment of them, are Complaints/631's.

Standalone: the economy records and the carriage table.
"""
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .accounts import DeliveredMove
from .market_memory import KEY_SEPARATOR as MARKET_KEY_SEPARATOR
from .merchants import MERCHANT_BID_ELASTICITY, Merchant
from .types import AreaId, Bid, EDGE_CONSUMPTION, GoodId, GoodsMove, TileId

CARRIER_ACCOUNT_PREFIX = "carriers:"
CarrierRows = Tuple[Tuple[GoodId, float], ...]     # ((carrier good, units worn per tonne-km),)


def account(merchant_id: str) -> str:
    """The account a merchant's carriers sit in, apart from the goods it trades."""
    return CARRIER_ACCOUNT_PREFIX + merchant_id


def units_per_tonne_km(count: float, life_years: float, days_per_year: float, tonne_km_per_team_day: float) -> float:
    """Units of a carrier good one tonne-km wears, when `count` of it work in a team that moves
    `tonne_km_per_team_day` and a unit works `days_per_year` days a year for `life_years`."""
    capacity = life_years * days_per_year * tonne_km_per_team_day
    return count / capacity if capacity > 0.0 else 0.0


def table(teams: Mapping[str, Mapping], uses: Mapping[GoodId, Mapping], lives: Mapping[GoodId, float],
          feed: Optional[Tuple[GoodId, float]] = None) -> Dict[str, Tuple[float, CarrierRows]]:
    """{mode: (tonne-km per team-day, ((carrier good, units worn per tonne-km),))} for each mode with a team.
    `teams` is geography's carriage rates (carriers, tonne_km_per_team_day, team_payload_tonnes); `uses` the
    `carrier_use` of each good that has one; `lives` the goods' service lives. A team member no good serves,
    or a good with no life, wears nothing here. `feed` is (feed good, kilograms in a unit of it): a team with
    animals also uses up that good, at geography's `animal_feed_kg_per_tonne_km`, a row like a carrier's whose
    units are eaten rather than worn by a life."""
    served: Dict[Tuple[str, str], GoodId] = {}
    for good, use in sorted(uses.items()):
        for kind, name in sorted(use["serves"].items()):
            served[(kind, name)] = good
    found: Dict[str, Tuple[float, CarrierRows]] = {}
    for mode, team in sorted(teams.items()):
        per_day = float(team.get("tonne_km_per_team_day", 0.0))
        rows = []
        for kind, name, count in team.get("carriers", ()):
            good = served.get((kind, name))
            life = lives.get(good, 0.0) if good else 0.0
            if good is None or life <= 0.0 or per_day <= 0.0:
                continue
            use = uses[good]
            payload = use.get("payload_tonnes")
            day_tonne_km = per_day * (float(payload) / float(team["team_payload_tonnes"])
                                      if payload and team.get("team_payload_tonnes") else 1.0)
            rows.append((good, units_per_tonne_km(float(count), life, float(use["days_per_year"]), day_tonne_km)))
        eaten = float(team.get("animal_feed_kg_per_tonne_km", 0.0))
        if feed is not None and eaten > 0.0 and feed[1] > 0.0 and per_day > 0.0:
            rows.append((feed[0], eaten / feed[1]))
        if rows:
            found[mode] = (per_day, tuple(rows))
    return found


class Wear:
    """The carrier units and team-days a tonne wears on any haul of a carriage table, at the return-trip
    emptiness `imbalance` leaves (the carriers' empty legs home wear them too)."""

    def __init__(self, setup, carriage, imbalance: float):
        self.setup, self.carriage, self.imbalance = setup, carriage, imbalance
        self._rows: Dict[Tuple[TileId, TileId], Tuple[Dict[GoodId, float], Dict[str, float]]] = {}

    def _worn(self, source: TileId, destination: TileId):
        found = self._rows.get((source, destination))
        if found is None:
            units: Dict[GoodId, float] = {}
            days: Dict[str, float] = {}
            haul = self.carriage.haul(source, destination)
            geography_days = dict(haul.team_days_by_mode)
            tonne_km_by_mode = dict(haul.km_by_mode)
            for mode, money in haul.money_by_mode:
                per_day, rows = self.setup.carriage_carriers.get(mode, (0.0, ()))
                if not rows or money <= 0.0 or tonne_km_by_mode.get(mode, 0.0) <= 0.0:
                    continue
                # the days are geography's, at each leg's pace; the carriers' empty legs home work them too
                worked = geography_days.get(mode, tonne_km_by_mode[mode] / per_day) * (1.0 + self.imbalance)
                days[mode] = days.get(mode, 0.0) + worked
                for good, per_tonne_km in rows:
                    units[good] = units.get(good, 0.0) + worked * per_tonne_km * per_day
            found = self._rows[(source, destination)] = (units, days)
        return found

    def units_per_tonne(self, source: TileId, destination: TileId) -> Dict[GoodId, float]:
        """{carrier good: units worn} carrying one tonne from `source` to `destination`."""
        return self._worn(source, destination)[0]

    def team_days_per_tonne(self, source: TileId, destination: TileId) -> Dict[str, float]:
        """{mode: team-days worked} carrying one tonne from `source` to `destination`."""
        return self._worn(source, destination)[1]


def wears(setup) -> bool:
    """Whether the setup's carriage wears any carrier."""
    return bool(setup.carriage_carriers)


def exposure(wear: Wear, moves: Sequence[DeliveredMove], specs) -> Tuple[Dict[GoodId, float], Dict[str, float]]:
    """({carrier good: units worn}, {mode: team-days}) by the shipments `moves` carried."""
    units: Dict[GoodId, float] = {}
    days: Dict[str, float] = {}
    for move in moves:
        tonnes = move.quantity * specs[move.good].unit_mass_kg / 1000.0
        for good, per_tonne in wear.units_per_tonne(move.tile, move.receiver_tile).items():
            units[good] = units.get(good, 0.0) + tonnes * per_tonne
        for mode, per_tonne in wear.team_days_per_tonne(move.tile, move.receiver_tile).items():
            days[mode] = days.get(mode, 0.0) + tonnes * per_tonne
    return units, days


def carrier_goods(setup) -> List[GoodId]:
    """Every good some mode's carriage wears."""
    return sorted({good for _day, rows in setup.carriage_carriers.values() for good, _units in rows})


def settle(merchant: Merchant, book, goods: Sequence[GoodId], units_worn: Mapping[GoodId, float]) -> List[GoodsMove]:
    """The moves that put the carriers (`goods`) the merchant bought into its carrier account and wear the stock there
    by `units_worn` (at most what it holds; the rest is the shortfall, unmet wear)."""
    mine = account(merchant.agent_id)
    moves: List[GoodsMove] = []
    for good in goods:
        for tile, quantity in sorted(book.holdings(merchant.agent_id)["goods"].get(good, {}).items()):
            if quantity > 0.0:
                moves.append(GoodsMove(merchant.agent_id, mine, good, tile, quantity, "carriers kept"))
    book.move_many(moves)
    worn: List[GoodsMove] = []
    for good, wanted in sorted(units_worn.items()):
        left = wanted
        for tile, quantity in sorted(book.holdings(mine)["goods"].get(good, {}).items()):
            take = min(left, quantity)
            if take > 0.0:
                worn.append(GoodsMove(mine, EDGE_CONSUMPTION, good, tile, take, "carriage wear"))
                left -= take
    book.move_many(worn)
    return moves + worn


def bids(setup, record, view, area_map, merchants_cash: Optional[Dict[str, float]] = None) -> Tuple[List[Bid], Dict[str, float]]:
    """Each merchant's bids for the carriers its shipments wore last year, delivered to its home tile, and the
    money each bid sets aside ({merchant: budget}), which the caller takes off the cash the merchant trades with."""
    found: List[Bid] = []
    budget: Dict[str, float] = {}
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        for good, units in sorted((merchant.carrier_wear or {}).items()):
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


def last_prices(setup, record) -> Dict[GoodId, float]:
    """Each carrier good's price last year, averaged over the areas that cleared it, else the opening's."""
    wanted = set(carrier_goods(setup))
    seen: Dict[GoodId, List[float]] = {}
    for key, price in sorted(record.memory.prices.items()):
        good = key.split(MARKET_KEY_SEPARATOR, 1)[0]
        if good in wanted and price > 0.0:
            seen.setdefault(good, []).append(price)
    return {good: math.fsum(seen[good]) / len(seen[good]) if good in seen else setup.opening_prices.get(good, 0.0)
            for good in wanted}


def money_per_tonne(prices: Mapping[GoodId, float], wear: Wear, source: TileId, destination: TileId) -> float:
    """What the carriers a tonne wears on this haul cost at `prices` (`last_prices`)."""
    return math.fsum(units * prices.get(good, 0.0) for good, units in wear.units_per_tonne(source, destination).items())
