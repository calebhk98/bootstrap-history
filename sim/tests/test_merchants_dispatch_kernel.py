"""`merchants_dispatch_answer.dispatch_all_merchants` (every merchant's haul loop in one kernel) gives what `merchants.dispatch`
gives one merchant at a time, for the same crew hired, fleet, dues, carrier money and purse; rents move purses in merchant order."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import carriage_fleet_book, merchants, merchants_dispatch_pack
from sim.economy.carriage_fleet import FleetLimit
from sim.economy.merchants_dispatch_answer import dispatch_all_merchants
from sim.economy.merchants_dispatch_pack import MerchantYear, YearHauls
from sim.economy.types import GoodSpec
from sim.tests.test_economy_merchants import SPECS, merchant, world

CART = "cart"
FEED = "feed"
WEAR = {CART: 0.1, FEED: 0.5}
SPECS_HERE = dict(SPECS, brick=GoodSpec("brick", 1000.0, 0.0, 0.0, "material"), feather=GoodSpec("feather", 1.0, 0.0, 0.0, "material"))


def routed(name="m1"):
    carriage, _map, _area_a, area_b = world()
    who = merchant(name)
    destination = ("b", area_b["salt"], 1.0)
    who.routes = {("salt", "a"): (destination,), ("brick", "a"): (destination,), ("feather", "a"): (("a", "x", 1.0), destination)}
    who.expected_prices = {("brick", area_b["salt"]): 5.0}
    return carriage, who


def crew_for(hired, wage):
    return merchants.CrewHire(lambda _source, _destination: (("hand|a", 2.0), ("sail|a", 0.5)), hired, wage, lambda _key: 1.5,
                              lambda _good, tile: "area_" + tile)


def both(cash=1000.0, held=None, crew=None, fleet=None, carrier_money=None, margin_kept=False, dues=None, with_wear=False):
    """(the per-merchant dispatch, the batch's answer for the same merchant)."""
    held = held or {("salt", "a"): 10.0, ("brick", "a"): 10.0, ("feather", "a"): 400.0}
    carriage, old = routed()
    _, new = routed()
    reference = merchants.dispatch(old, carriage, SPECS_HERE, "coin", cash, held, carrier_of=lambda tile: "carter", crew=crew,
                                   carrier_money=carrier_money, margin_kept=margin_kept, fleet=fleet, dues=dues)
    hauls = YearHauls(carriage, SPECS_HERE, lambda tile: "carter", "coin", dues or (lambda _source, _destination: {}),
                      wear_units=(lambda _source, _destination: WEAR) if with_wear else None, carrier_money=carrier_money)
    answer = dispatch_all_merchants([MerchantYear(new, cash, held, True, crew, fleet)], hauls)
    return reference, answer.dispatch_of(0), answer


class BatchGivesWhatOneMerchantGets(unittest.TestCase):
    def assert_same(self, reference, found):
        self.assertEqual(found.moves, reference.moves)
        self.assertEqual(found.transfers, reference.transfers)
        self.assertEqual(found.dues, reference.dues)
        self.assertEqual(found.crew_hours_wanted, reference.crew_hours_wanted)
        self.assertEqual(found.crew_money_wanted, reference.crew_money_wanted)
        self.assertEqual(found.fleet_wanted, reference.fleet_wanted)

    def test_plain_shipments(self):
        reference, found, _answer = both()
        self.assertTrue(reference.moves)
        self.assert_same(reference, found)

    def test_a_purse_that_cannot_pay_every_fee(self):
        reference, found, _answer = both(cash=3.3)
        self.assert_same(reference, found)

    def test_crew_hired_short_cuts_what_is_carried(self):
        reference, found, _answer = both(crew=crew_for({"hand|a": 5.0, "sail|a": 1.0}, {"hand|a": 0.2}))
        self.assertTrue(reference.crew_hours_wanted)
        self.assert_same(reference, found)

    def test_no_plan_yet_pays_the_crew_outright(self):
        reference, found, _answer = both(crew=crew_for(None, {}), carrier_money=lambda _s, _d: 0.4, margin_kept=True, with_wear=True)
        self.assert_same(reference, found)

    def test_carrier_money_dues_and_margin(self):
        dues = lambda _source, _destination: {"town": 0.05, "fort": 0.01}
        reference, found, _answer = both(crew=crew_for({"hand|a": 50.0, "sail|a": 50.0}, {"hand|a": 0.3, "sail|a": 0.1}),
                                         carrier_money=lambda _s, _d: 0.4, margin_kept=True, dues=dues, with_wear=True)
        self.assertTrue(reference.dues)
        self.assert_same(reference, found)

    def test_a_purse_pays_dues_first(self):
        dues = lambda _source, _destination: {"town": 0.4}
        reference, found, _answer = both(cash=2.0, dues=dues)
        self.assert_same(reference, found)

    def test_a_fleet_bounds_what_is_carried(self):
        wear = lambda _source, _destination: WEAR
        reference, found, _answer = both(fleet=FleetLimit(wear, {CART: 0.3}), with_wear=True, carrier_money=lambda _s, _d: None,
                                        margin_kept=True)
        self.assert_same(reference, found)

    def test_a_merchant_that_does_not_carry_moves_nothing(self):
        carriage, who = routed()
        hauls = YearHauls(carriage, SPECS_HERE, lambda tile: "carter", "coin", lambda _s, _d: {})
        answer = dispatch_all_merchants([MerchantYear(who, 10.0, {}, False)], hauls)
        self.assertEqual(answer.dispatch_of(0).moves, ())


class WearNeededAsTheFleetBookGivesIt(unittest.TestCase):
    def test_the_wear_the_routes_stock_calls_for(self):
        carriage, old = routed()
        _, new = routed()
        held = {("salt", "a"): 10.0, ("brick", "a"): 3.0, ("feather", "a"): 400.0}
        wear = types.SimpleNamespace(units_per_tonne=lambda _source, _destination: WEAR)
        reference = carriage_fleet_book.wear_needed(old, held, SPECS_HERE, wear, [CART])
        hauls = YearHauls(carriage, SPECS_HERE, lambda tile: "carter", "coin", lambda _s, _d: {}, wear_units=wear.units_per_tonne)
        found = merchants_dispatch_pack.wear_needed(merchants_dispatch_pack.pack([MerchantYear(new, 5.0, held)], hauls, [CART]))
        self.assertEqual(found, [reference])
        self.assertTrue(reference)


class RentsMovePursesInOrder(unittest.TestCase):
    def test_a_lessor_paid_by_an_earlier_merchant_dispatches_with_it(self):
        carriage, first = routed("m1")
        _, second = routed("m2")
        wear = lambda _source, _destination: {CART: 0.1}
        fleet_first = FleetLimit(wear, {CART: 0.5})
        fleet_second = FleetLimit(wear, {CART: 5.0})
        held = {("salt", "a"): 10.0}
        entries = [MerchantYear(first, 100.0, held, True, None, fleet_first, own={CART: 0.0}, hired={CART: 0.5}),
                   MerchantYear(second, 0.0, held, True, None, fleet_second, own={CART: 5.0})]
        hauls = YearHauls(carriage, SPECS_HERE, lambda tile: "carter", "coin", lambda _s, _d: {}, wear_units=wear,
                          lent={CART: {"m2": 0.5}}, carrier_prices={CART: 3.0})
        answer = dispatch_all_merchants(entries, hauls)
        paid = answer.rent_of(0)
        self.assertEqual([(each.payer, each.payee) for each in paid], [("m1", "m2")])
        self.assertGreater(paid[0].amount, 0.0)
        self.assertAlmostEqual(answer.results.cash_after[1], 0.0 + paid[0].amount - sum(each.amount for each in answer.dispatch_of(1).transfers))


if __name__ == "__main__":
    unittest.main()
