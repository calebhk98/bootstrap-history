"""Complaint 632: the parts of a carriage fee go to those who supply them. The crew is paid by the labour market, the
carriers worn and the feed the animals eat are bought in the goods market, and the rest stays with the merchant that
owns the carriers; none of it is paid to the poorest households of the source tile. Each rule is called on built inputs;
that a whole economy conserves money is `money_audit`'s own test."""

QUICK_TOPIC = True
import types
import unittest

from sim.economy import carriage_fleet_book, carriage_wear, merchants
from sim.economy.accounts import Book
from sim.economy.types import Fill, GoodSpec
from sim.tests import test_economy_merchants as basic

FEED_GOOD = "grain"
FEED_KG_PER_TONNE_KM = 1.0


class FeedIsARowOfTheTable(unittest.TestCase):
    TEAM = {"cart": {"carriers": [["animal", "ox", 2.0], ["vehicle", "cart", 1.0]], "tonne_km_per_team_day": 20.0,
                     "team_payload_tonnes": 1.0, "animal_feed_kg_per_tonne_km": 1.5}}
    USES = {"cart": {"serves": {"vehicle": "cart"}, "days_per_year": 150.0}}

    def test_a_team_with_animals_uses_up_feed_by_the_tonne_km(self):
        found = carriage_wear.table(self.TEAM, self.USES, {"cart": 10.0}, ("wheat", 2.0))
        rows = dict(found["cart"][1])
        self.assertAlmostEqual(rows["wheat"], 1.5 / 2.0)       # units of the feed good, whose unit is 2 kg
        self.assertIn("cart", rows)

    def test_a_team_without_animals_eats_nothing(self):
        team = {"sail": dict(self.TEAM["cart"], carriers=[["vehicle", "cart", 1.0]], animal_feed_kg_per_tonne_km=0.0)}
        rows = dict(carriage_wear.table(team, self.USES, {"cart": 10.0}, ("wheat", 2.0))["sail"][1])
        self.assertNotIn("wheat", rows)

    def test_no_feed_good_means_no_feed_row(self):
        rows = dict(carriage_wear.table(self.TEAM, self.USES, {"cart": 10.0})["cart"][1])
        self.assertEqual(list(rows), ["cart"])


class WhatIsLeftOfAFee(unittest.TestCase):
    def dispatch(self, cash=100.0, **kwargs):
        carriage, _map, area_a, _b = basic.world()
        who = basic.merchant()
        basic.plan(who, 2.0, 5.0)
        fills = (Fill("m1", "salt", area_a["salt"], "a", 10.0, 2.0, "buy"),)
        return merchants.dispatch(who, fills, carriage, basic.SPECS, "coin", cash, {("salt", "a"): 10.0},
                                  carrier_of={"a": "the poorest of a"}.get, **kwargs)

    def test_without_a_decomposed_fee_the_poorest_are_paid_as_before(self):
        result = self.dispatch()
        self.assertEqual([each.payee for each in result.transfers], ["the poorest of a"])

    def test_the_part_the_merchant_buys_is_not_paid_to_the_poorest(self):
        result = self.dispatch(carrier_money=lambda source, destination: 0.4, margin_kept=True)
        self.assertEqual(result.transfers, ())

    def test_the_part_the_merchant_buys_is_taken_off_the_fee_when_the_margin_is_not_kept(self):
        result = self.dispatch(carrier_money=lambda source, destination: 0.4)
        self.assertAlmostEqual(result.transfers[0].amount, 10.0 * (basic.CARRIAGE_PER_UNIT - 0.4))

    def test_the_margin_is_not_a_cash_need_so_a_poor_merchant_still_ships(self):
        result = self.dispatch(cash=0.0, carrier_money=lambda source, destination: 0.4, margin_kept=True)
        self.assertAlmostEqual(result.moves[0].quantity, 10.0)
        self.assertEqual(result.stranded, ())


class MerchantsBidForFeed(unittest.TestCase):
    """A merchant's carrier wear in a feed good is bid for in the goods market (`carriage_fleet_book.bids`), on built inputs."""

    def inputs(self, price):
        setup = types.SimpleNamespace(carriage_carriers={"cart": (20.0, (("cart", 0.1), (FEED_GOOD, FEED_KG_PER_TONNE_KM)))},
                                      specs={"cart": GoodSpec("cart", 200.0, 0.0, 10.0, "carrier", capital_asset=True),
                                             FEED_GOOD: GoodSpec(FEED_GOOD, 1.0, 0.0, 0.0, "food")},
                                      opening_prices={FEED_GOOD: 2.0})
        record = types.SimpleNamespace(book=Book(), merchants={"m1": basic.merchant()})
        record.merchants["m1"].carrier_wear = {FEED_GOOD: 3.0}
        record.merchants["m1"].carrier_fleet_wanted = {}
        view = types.SimpleNamespace(price=lambda good, area: price)
        area_map = types.SimpleNamespace(goods=lambda: [FEED_GOOD], area_of=lambda good, tile: "area:" + tile)
        return setup, record, view, area_map

    def test_the_feed_the_animals_ate_is_bid_for_by_the_unit_and_its_money_set_aside(self):
        bids, budget = carriage_fleet_book.bids(*self.inputs(price=4.0))
        self.assertEqual([(bid.buyer, bid.good, bid.floor_quantity, bid.area) for bid in bids], [("m1", FEED_GOOD, 3.0, "area:a")])
        self.assertAlmostEqual(budget["m1"], 12.0)

    def test_a_feed_with_no_price_yet_is_bid_for_at_the_opening_price(self):
        _bids, budget = carriage_fleet_book.bids(*self.inputs(price=None))
        self.assertAlmostEqual(budget["m1"], 6.0)

    def test_a_merchant_with_no_cash_sets_nothing_aside_and_bids_for_nothing(self):
        bids, budget = carriage_fleet_book.bids(*self.inputs(price=4.0), merchants_cash={"m1": 0.0})
        self.assertEqual((bids, budget), ([], {}))

if __name__ == "__main__":
    unittest.main()
