"""A year's dispatch of every merchant, read back as objects: `Dispatched` is the handle on the kernel's answer
(`merchants_dispatch_pack.dispatch_year`), one merchant at a time as the `merchants.Dispatch` the per-merchant `merchants.dispatch` gives."""
from typing import Dict, List

from sim.book import DeliveredMove

from . import merchants_transit, route_dues
from .merchants import EDGE_CARRIAGE, Dispatch
from .merchants_dispatch_pack import dispatch_year, MerchantYear, Packed, YearHauls
from .types import Transfer


class Dispatched:
    """The answer for the merchants of a year's `entries`, by their position in it."""

    def __init__(self, packed: Packed, leg_results, results) -> None:
        self.packed, self.leg_results, self.results = packed, leg_results, results
        routes, merchants, legs = packed.routes, packed.merchants, packed.legs     # the columns read many times, as lists
        self._first_route, self._route_count = merchants.first_route.tolist(), merchants.route_count.tolist()
        self._first_leg, self._leg_count = routes.first_leg.tolist(), routes.leg_count.tolist()
        self._pair = legs.pair.tolist()
        self._carried, self._fee = leg_results.carried.tolist(), leg_results.fee.tolist()
        self._dues_paid = leg_results.dues_paid.tolist()
        self._figures = {name: getattr(results, name).tolist() for name in ("hours_wanted", "money_wanted", "fleet_wanted", "worn")}
        self._named_flags = {name: getattr(results, name + "_named").tolist() for name in self._figures}
        self._pair_places = {"crew_key": (packed.key_names, packed.pairs.crew_count.tolist(), packed.pairs.crew_key.tolist()),
                             "wear_carrier": (packed.carrier_names, packed.pairs.wear_count.tolist(), packed.pairs.wear_carrier.tolist())}

    def _legs_of(self, row: int):
        """(leg row, good, source tile, destination tile) of the merchant's legs that go somewhere, in route order."""
        found = []
        pair, leg_info = self._pair, self.packed.leg_info
        first = self._first_route[row]
        for route in range(first, first + self._route_count[row]):
            for leg in range(self._first_leg[route], self._first_leg[route] + self._leg_count[route]):
                if pair[leg] >= 0:
                    found.append((leg,) + leg_info[leg])
        return found

    def dispatch_of(self, row: int) -> Dispatch:
        """The merchant's moves, fees and dues, and what its shipments asked of crew and fleet; a haul that outlasts the year is
        added to the merchant's shipments on the road."""
        packed, hauls = self.packed, self.packed.hauls
        merchant = packed.entries[row].merchant
        moves, transfers, dues = [], [], []
        legs = self._legs_of(row)
        for leg, good, tile, destination in legs:
            carried = self._carried[leg]
            if carried <= 0.0:
                continue
            years = merchants_transit.years_between(hauls.carriage, tile, destination)
            if years > 1:
                merchant.add_shipment(merchants_transit.Shipment(good, carried, destination, years - 1))
            moves.append(DeliveredMove(merchant.agent_id, merchants_transit.EDGE_TRANSIT if years > 1 else merchant.agent_id,
                                       good, tile, carried, "carried to market", destination))
            for place, holder in enumerate(packed.pair_holders[self._pair[leg]]):
                paid = self._dues_paid[leg][place]
                if paid > 0.0:
                    dues.append(Transfer(merchant.agent_id, route_dues.account(holder), hauls.currency, paid, "route dues on %s" % good))
            fee = self._fee[leg]
            if fee > 0.0:
                transfers.append(Transfer(merchant.agent_id, hauls.carrier_of(tile) or EDGE_CARRIAGE, hauls.currency, fee,
                                          "carriage of %s" % good))
        return Dispatch(tuple(moves), tuple(transfers), self._named(row, "hours_wanted", "crew_key", False, legs),
                        self._named(row, "money_wanted", "crew_key", False, legs), self._named(row, "fleet_wanted", "wear_carrier", False, legs),
                        tuple(dues))

    def _named(self, row: int, column: str, pair_column: str, carried_only: bool, legs=None) -> Dict[str, float]:
        """The figures of `column` by name, in the order the merchant's shipments first asked for each (a pair's rows in its own order)."""
        names, counts, numbers = self._pair_places[pair_column]
        values, named = self._figures[column][row], self._named_flags[column][row]
        found: Dict[str, float] = {}
        for leg, _good, _tile, _destination in (self._legs_of(row) if legs is None else legs):
            if carried_only and self._carried[leg] <= 0.0:
                continue
            pair = self._pair[leg]
            for place in range(counts[pair]):
                number = numbers[pair][place]
                if named[number] and names[number] not in found:
                    found[names[number]] = values[number]
        return found

    def worn_of(self, row: int) -> Dict[str, float]:
        """The carrier units the merchant's shipments wore, by carrier good (`carriage_wear.exposure`)."""
        return self._named(row, "worn", "wear_carrier", True)

    def rent_of(self, row: int) -> List[Transfer]:
        """What the merchant paid the merchants it hired carriers from, in lessor order."""
        packed = self.packed
        payer = packed.entries[row].merchant.agent_id
        return [Transfer(payer, packed.entries[lessor].merchant.agent_id, packed.hauls.currency, float(money), "carriers hired")
                for lessor, money in enumerate(self.results.rent[row, :len(packed.entries)].tolist()) if money > 0.0]


def dispatch_all_merchants(entries, hauls: YearHauls) -> Dispatched:
    """`dispatch_year` with its answer read by merchant."""
    return Dispatched(*dispatch_year(entries, hauls))
