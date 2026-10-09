"""Actors' sales and purchases as orders in the economy's book: a sale's goods are offered and its proceeds come back
as the seller's money, a purchase's budget is held by a bid and its unspent part returns, and goods and money are
conserved. Built on the hand-made economy; no game."""

QUICK_TOPIC = True

import unittest

from sim.economy import api as economy_api
from sim.engine import economy_port_actors as actors_port
from sim.tests import economy_fixture
from sim.tests.economy_fixture import FARMS, GRAIN, TOWN


def per_unit(good):
    return 1.0


def tile_of(actor):
    return FARMS


def reservation_of(seller, node, material, tile):
    return 0.0


def opened():
    economy, _outcomes = economy_fixture.run(years=3)
    return economy


def run_with(economy, orders):
    return economy.step(economy_fixture.quiet_year(economy.setup, engine_orders=orders))


class ActorTradeInTheBook(unittest.TestCase):
    def test_a_sale_is_offered_and_its_proceeds_come_back_with_the_unsold_goods(self):
        economy = opened()
        sales = []
        actors_port.note_sale(sales, "firm:a", GRAIN, 4000.0, [("node", 4000.0)])
        moves, orders = actors_port.sale_orders(economy, sales, per_unit, tile_of, reservation_of)
        economy_api.move_goods(economy, moves)
        run_with(economy, orders)
        proceeds, refunds, bought = actors_port.close(economy, sales, [])
        self.assertGreater(proceeds["firm:a"], 0.0)
        self.assertEqual(refunds, {})
        self.assertEqual(bought, {})
        book = economy_api.economy_book(economy)
        self.assertEqual(book.stock("sale:firm:a", GRAIN, FARMS), 0.0)          # nothing left in the account
        self.assertEqual(book.balance("sale:firm:a", economy.setup.currency_id), 0.0)
        self.assertEqual(book.check_conservation(1e-6).breaches, ())
        self.assertAlmostEqual(book.edge_net("edge:exchange", economy.setup.currency_id), -proceeds["firm:a"])   # it left over the exchange

    def test_a_good_the_economy_does_not_trade_is_not_offered(self):
        economy = opened()
        sales = []
        actors_port.note_sale(sales, "firm:a", "unknown_kg", 10.0, None)
        moves, orders = actors_port.sale_orders(economy, sales, per_unit, tile_of, reservation_of)
        self.assertEqual((moves, orders), ([], {}))

    def test_a_purchase_holds_its_budget_and_returns_what_it_does_not_spend(self):
        economy = opened()
        purchases = []
        actors_port.note_purchase(purchases, "state:a", "grain", 300.0, 400.0)
        orders, funding = actors_port.purchase_orders(
            economy, purchases, per_unit, tile_of, lambda commodity: [GRAIN], economy.setup.coin_per_unit)
        self.assertEqual(len(funding), 1)
        actors_port.fund(economy, funding)
        book = economy_api.economy_book(economy)
        currency = economy.setup.currency_id
        self.assertEqual(book.balance("buy:state:a", currency), funding[0][2])
        run_with(economy, orders)
        proceeds, refunds, bought = actors_port.close(economy, [], purchases)
        self.assertEqual(proceeds, {})
        self.assertGreater(bought.get("state:a", 0.0), 0.0)                       # it got some grain, now used up
        self.assertLessEqual(refunds.get("state:a", 0.0), funding[0][2])
        spent = funding[0][2] - refunds.get("state:a", 0.0)
        self.assertGreater(spent, 0.0)
        self.assertEqual(book.balance("buy:state:a", currency), 0.0)
        self.assertEqual(book.stock("buy:state:a", GRAIN, FARMS), 0.0)
        self.assertEqual(book.check_conservation(1e-6).breaches, ())

    def test_a_sale_and_a_purchase_of_the_same_actor_use_separate_accounts(self):
        self.assertNotEqual(actors_port.sale_account("x"), actors_port.buy_account("x"))

    def test_the_same_seller_and_material_join_into_one_sale(self):
        sales = []
        actors_port.note_sale(sales, "firm:a", GRAIN, 1.0, [("n", 1.0)])
        actors_port.note_sale(sales, "firm:a", GRAIN, 2.0, [("m", 2.0)])
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0]["tonnes"], 3.0)
        self.assertEqual(sales[0]["concerns"], [["n", 1.0], ["m", 2.0]])


if __name__ == "__main__":
    unittest.main()
