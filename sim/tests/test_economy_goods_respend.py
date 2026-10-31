"""A household rationed on a good spends what it did not spend on the goods meeting the same need, then on its other
needs; money no offered good can take is not bid (Eurace@Unibi's second choice among the goods still in stock)."""
QUICK_TOPIC = True

import math
import unittest

from sim.economy.goods_respend import offers_left, rationed_money, respend_bids
from sim.economy.types import Bid, Offer
from sim.world.need_basket import Basket, NeedSpec


def basket():
    return Basket(needs=(NeedSpec("food", 1.0, 2.0, (("grain", 1.0), ("rice", 1.0))),
                         NeedSpec("tools", 0.0, 1.0, (("hammer", 1.0),))),
                  substitution=2.0, need_data={})


def area_of(good):
    return "area"


def bid(good, budget, quantity, price=1.0):
    return Bid("h", good, "area", "tile", quantity, 0.0, price, 1.0, budget)


class RationedMoneyTests(unittest.TestCase):
    def test_money_for_the_units_not_got(self):
        self.assertAlmostEqual(rationed_money([bid("grain", 100.0, 40.0)], 10.0, 10.0, 1.0), 30.0)

    def test_never_more_than_the_budget_unspent(self):
        self.assertAlmostEqual(rationed_money([bid("grain", 15.0, 40.0)], 10.0, 10.0, 1.0), 5.0)

    def test_a_bid_that_got_what_it_wanted_has_nothing(self):
        self.assertEqual(rationed_money([bid("grain", 100.0, 40.0)], 40.0, 40.0, 1.0), 0.0)


class RespendTests(unittest.TestCase):
    def test_rationed_on_one_good_spends_the_rest_on_its_substitute(self):
        bids = respend_bids("h", "tile", basket(), {"food": 50.0}, {"rice": 2.0}, area_of)
        self.assertEqual([each.good for each in bids], ["rice"])
        self.assertAlmostEqual(bids[0].budget, 50.0)
        self.assertEqual(bids[0].buyer, "h")

    def test_substitutes_share_the_money_by_the_choice_rule(self):
        bids = respend_bids("h", "tile", basket(), {"food": 90.0}, {"grain": 1.0, "rice": 2.0}, area_of)
        budgets = {each.good: each.budget for each in bids}
        self.assertAlmostEqual(sum(budgets.values()), 90.0)
        self.assertGreater(budgets["grain"], budgets["rice"])          # the cheaper per need unit takes more
        self.assertAlmostEqual(budgets["grain"] / budgets["rice"], (2.0 / 1.0) ** (basket().substitution - 1.0))

    def test_no_substitute_on_offer_passes_the_money_to_other_needs(self):
        bids = respend_bids("h", "tile", basket(), {"food": 50.0}, {"hammer": 5.0}, area_of)
        self.assertEqual([each.good for each in bids], ["hammer"])
        self.assertAlmostEqual(bids[0].budget, 50.0)

    def test_other_needs_share_the_passed_money_by_their_weights(self):
        two = Basket(needs=basket().needs + (NeedSpec("light", 0.0, 3.0, (("oil", 1.0),)),), substitution=2.0,
                     need_data={})
        bids = respend_bids("h", "tile", two, {"food": 60.0}, {"hammer": 5.0, "oil": 1.0}, area_of)
        budgets = {each.good: each.budget for each in bids}
        self.assertAlmostEqual(budgets["hammer"], 15.0)
        self.assertAlmostEqual(budgets["oil"], 45.0)

    def test_nothing_on_offer_keeps_the_money(self):
        self.assertEqual(respend_bids("h", "tile", basket(), {"food": 50.0}, {}, area_of), [])

    def test_the_bid_asks_for_the_units_the_money_buys_at_the_ask(self):
        bids = respend_bids("h", "tile", basket(), {"food": 50.0}, {"rice": 2.0}, area_of)
        self.assertAlmostEqual(bids[0].flexible_quantity * bids[0].reference_price, 50.0)
        self.assertTrue(math.isinf(bids[0].maximum_price))


class OffersLeftTests(unittest.TestCase):
    def test_sold_units_come_off_and_empty_offers_go(self):
        offers = [Offer("a", "rice", "area", "t", 10.0, 1.0), Offer("b", "rice", "area", "t", 5.0, 2.0)]
        left = offers_left(offers, {("a", "t"): 10.0, ("b", "t"): 2.0})
        self.assertEqual([(each.seller, each.quantity) for each in left], [("b", 3.0)])


if __name__ == "__main__":
    unittest.main()
