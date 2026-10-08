"""A seller that moves the clearing price chooses its reservation to maximise (price - cost) times what it
sells against the rest of the market's book; one that does not move it keeps the price-taking rule."""
import math
import unittest
from unittest import mock

from sim.economy import goods_market, seller_pricing
from sim.economy.types import Bid, Offer

GOOD, AREA, TILE = "coffee", "area", "tile"
OWN = "own"


def demand(budget=150.0, elasticity=0.5):
    """One buyer whose want falls with price: flexible demand around a reference price of one."""
    return [Bid("buyer", GOOD, AREA, TILE, 0.0, 100.0, 1.0, elasticity, budget)]


def rival(quantity, price, name="rival"):
    return Offer(name, GOOD, AREA, TILE, quantity, price)


def own(quantity, price=0.0):
    return Offer(OWN, GOOD, AREA, TILE, quantity, price)


class MaterialityTests(unittest.TestCase):
    def test_a_seller_among_a_deep_market_does_not_move_the_price(self):
        rivals = [rival(1e6, 1.0)]
        self.assertFalse(seller_pricing.moves_the_price(demand(), rivals, own(1e-6), 1.0))

    def test_a_seller_that_is_the_market_moves_the_price(self):
        self.assertTrue(seller_pricing.moves_the_price(demand(), [], own(60.0), 1.0))


class ChoiceTests(unittest.TestCase):
    def test_a_price_taker_keeps_its_reservation(self):
        rivals = [rival(1e6, 1.0)]
        self.assertIsNone(seller_pricing.best_reservation(demand(), rivals, own(1e-6), 0.1, 1.0))

    def test_a_sole_seller_with_ample_stock_holds_back_to_a_price_above_the_one_that_sells_all(self):
        everything = seller_pricing.profit_at(demand(), [], own(500.0), 0.0, 0.1, 1.0)
        choice = seller_pricing.best_reservation(demand(), [], own(500.0), 0.1, 1.0)
        self.assertIsNotNone(choice)
        self.assertGreater(seller_pricing.profit_at(demand(), [], own(500.0), choice, 0.1, 1.0), everything)

    def test_the_choice_is_at_least_as_good_as_selling_everything(self):
        rivals = [rival(30.0, 1.2), rival(30.0, 2.0, "other")]
        offer = own(80.0)
        choice = seller_pricing.best_reservation(demand(), rivals, offer, 0.05, 1.0)
        chosen = 0.0 if choice is None else choice
        self.assertGreaterEqual(seller_pricing.profit_at(demand(), rivals, offer, chosen, 0.05, 1.0),
                                seller_pricing.profit_at(demand(), rivals, offer, 0.0, 0.05, 1.0) - 1e-9)

    def test_a_cheap_seller_with_rivals_dearer_than_its_cost_wins_their_customers_by_pricing_below_them(self):
        rivals = [rival(40.0, 1.0)]
        offer = own(200.0)
        choice = seller_pricing.best_reservation(demand(), rivals, offer, 0.01, 1.0)
        chosen = 0.0 if choice is None else choice
        sold_own, price = seller_pricing.sold_and_price(demand(), rivals, offer, chosen, 1.0)
        self.assertGreater(sold_own, 0.0)
        # its price is below what the rivals ask, so they sell nothing: demand left to them is zero
        self.assertLess(price, 1.0)


class RestraintTests(unittest.TestCase):
    def test_a_sole_seller_asking_below_its_best_price_raises_its_ask(self):
        offer = own(500.0)
        choice = seller_pricing.best_reservation(demand(), [], offer, 0.1, 1.0, ceiling=2.0, floor=0.5, current=0.5)
        self.assertIsNotNone(choice)
        self.assertGreater(choice, 0.5)
        self.assertLessEqual(choice, 2.0)

    def test_the_raise_is_bounded_by_the_ceiling(self):
        offer = own(500.0)
        choice = seller_pricing.best_reservation(demand(), [], offer, 0.1, 1.0, ceiling=0.6, floor=0.4, current=0.5)
        self.assertLessEqual(choice, 0.6)

    def test_a_seller_already_at_its_best_ask_within_its_bounds_keeps_it(self):
        offer = own(500.0)
        best = seller_pricing.best_reservation(demand(), [], offer, 0.1, 1.0)
        self.assertIsNone(seller_pricing.best_reservation(demand(), [], offer, 0.1, 1.0,
                                                          ceiling=best, floor=best * 0.9, current=best))

    def test_a_seller_with_a_dear_rival_does_not_raise_past_a_price_that_sells_less_for_less(self):
        rivals = [rival(1e6, 1.0)]
        self.assertIsNone(seller_pricing.best_reservation(demand(), rivals, own(1e-6), 0.1, 1.0, ceiling=2.0,
                                                          floor=0.5, current=1.0))


def reference_choice(bids, rivals, offer, unit_value, last_price, ceiling, floor, current):
    """The search written out with every candidate cleared on its own, to hold the shared-clear version to it."""
    if not seller_pricing.moves_the_price(bids, rivals, offer, last_price):
        return None
    best, best_profit = None, seller_pricing.profit_at(bids, rivals, offer, current, unit_value, last_price)
    bounds = [bound for bound in (floor, ceiling) if math.isfinite(bound)]
    for reservation in sorted({*bounds, *seller_pricing._candidates(rivals, last_price, unit_value)}):
        if reservation > ceiling or reservation < floor or reservation == current:
            continue
        profit = seller_pricing.profit_at(bids, rivals, offer, reservation, unit_value, last_price)
        if profit > best_profit + seller_pricing.ROUNDING_SHARE * max(abs(best_profit), 1e-300):
            best, best_profit = reservation, profit
    return best


class SharedClearTests(unittest.TestCase):
    SCENARIOS = [
        ([], 500.0, 0.0, 0.0, 2.0),
        ([], 500.0, 0.5, 0.4, 0.6),
        ([rival(30.0, 1.2), rival(30.0, 2.0, "other")], 80.0, 0.0, 0.0, 1.5),
        ([rival(40.0, 1.0)], 200.0, 1.0, 0.85, 1.15),
        ([rival(40.0, 1.0)], 200.0, 0.0, 0.0, math.inf),
    ]

    def test_the_choice_is_the_one_clearing_every_candidate_separately_gives(self):
        for rivals, quantity, current, floor, ceiling in self.SCENARIOS:
            offer = own(quantity)
            self.assertEqual(
                seller_pricing.best_reservation(demand(), rivals, offer, 0.05, 1.0, ceiling=ceiling, floor=floor,
                                                current=current),
                reference_choice(demand(), rivals, offer, 0.05, 1.0, ceiling, floor, current))

    def test_no_reservation_is_cleared_twice_and_the_book_without_the_offer_once(self):
        for rivals, quantity, current, floor, ceiling in self.SCENARIOS:
            seen = []
            real = goods_market.clear

            def recording(bids, offers, *rest):
                seen.append(next((offer.reservation_price for offer in offers if offer.seller == OWN), None))
                return real(bids, offers, *rest)

            with mock.patch.object(goods_market, "clear", recording):
                seller_pricing.best_reservation(demand(), rivals, own(quantity), 0.05, 1.0, ceiling=ceiling,
                                                floor=floor, current=current)
            self.assertEqual(len(seen), len(set(seen)), (rivals, current, seen))


if __name__ == "__main__":
    unittest.main()
