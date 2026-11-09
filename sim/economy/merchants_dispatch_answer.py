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

    def _legs_of(self, row: int):
        """(leg row, good, source tile, destination tile) of the merchant's legs that go somewhere, in route order."""
        packed = self.packed
        routes = packed.routes
        first = int(packed.merchants.first_route[row])
        for route in range(first, first + int(packed.merchants.route_count[row])):
            for leg in range(int(routes.first_leg[route]), int(routes.first_leg[route] + routes.leg_count[route])):
                if packed.legs.pair[leg] >= 0:
                    yield (leg,) + packed.leg_info[leg]

    def dispatch_of(self, row: int) -> Dispatch:
        """The merchant's moves, fees and dues, and what its shipments asked of crew and fleet; a haul that outlasts the year is
        added to the merchant's shipments on the road."""
        packed, hauls = self.packed, self.packed.hauls
        merchant = packed.entries[row].merchant
        moves, transfers, dues = [], [], []
        for leg, good, tile, destination in self._legs_of(row):
            carried = float(self.leg_results.carried[leg])
            if carried <= 0.0:
                continue
            years = merchants_transit.years_between(hauls.carriage, tile, destination)
            if years > 1:
                merchant.add_shipment(merchants_transit.Shipment(good, carried, destination, years - 1))
            moves.append(DeliveredMove(merchant.agent_id, merchants_transit.EDGE_TRANSIT if years > 1 else merchant.agent_id,
                                       good, tile, carried, "carried to market", destination))
            for place, holder in enumerate(packed.pair_holders[int(packed.legs.pair[leg])]):
                paid = float(self.leg_results.dues_paid[leg, place])
                if paid > 0.0:
                    dues.append(Transfer(merchant.agent_id, route_dues.account(holder), hauls.currency, paid, "route dues on %s" % good))
            fee = float(self.leg_results.fee[leg])
            if fee > 0.0:
                transfers.append(Transfer(merchant.agent_id, hauls.carrier_of(tile) or EDGE_CARRIAGE, hauls.currency, fee,
                                          "carriage of %s" % good))
        return Dispatch(tuple(moves), tuple(transfers), self._named(row, "hours_wanted", "crew_key", False),
                        self._named(row, "money_wanted", "crew_key", False), self._named(row, "fleet_wanted", "wear_carrier", False),
                        tuple(dues))

    def _named(self, row: int, column: str, pair_column: str, carried_only: bool) -> Dict[str, float]:
        """The figures of `column` by name, in the order the merchant's shipments first asked for each (a pair's rows in its own order)."""
        packed = self.packed
        names = packed.key_names if pair_column == "crew_key" else packed.carrier_names
        values, named = getattr(self.results, column)[row], getattr(self.results, column + "_named")[row]
        counts = packed.pairs.crew_count if pair_column == "crew_key" else packed.pairs.wear_count
        found: Dict[str, float] = {}
        for leg, _good, _tile, _destination in self._legs_of(row):
            if carried_only and self.leg_results.carried[leg] <= 0.0:
                continue
            pair = int(packed.legs.pair[leg])
            for place in range(int(counts[pair])):
                number = int(getattr(packed.pairs, pair_column)[pair, place])
                if named[number] and names[number] not in found:
                    found[names[number]] = float(values[number])
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
