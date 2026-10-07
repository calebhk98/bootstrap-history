"""A seller that moves the clearing price chooses its reservation to maximise (price - cost) times what it
sells against the rest of the market's book; one that does not move it keeps the price-taking rule."""
import unittest

from sim.economy import seller_pricing
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


if __name__ == "__main__":
    unittest.main()
