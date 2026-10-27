"""Actors' sales and purchases as orders in the economy's book: a sale's goods are offered at its reservation, a
purchase's budget is held by a bid, and `close` returns the proceeds, refunds and deliveries. Each rule is called on a
stand-in economy written out here; the economy's own functions are replaced by recorders."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.markets import port_actors as actors_port

GRAIN, FARMS, COIN = "grain_kg", "farms", "coin"


class AreaMap:
    def goods(self):
        return {GRAIN}

    def area_of(self, good, tile):
        return "area:" + tile


def stand_in_economy(specs=None):
    setup = types.SimpleNamespace(currency_id=COIN, specs=specs or {})
    return types.SimpleNamespace(area_map=AreaMap(), setup=setup)


def per_unit(good):
    return 2.0


def tile_of(actor):
    return FARMS


class Book:
    """Holdings and balances per account, as `close` reads them."""
    def __init__(self, goods, money):
        self.goods, self.money = goods, money

    def holdings(self, account):
        return {"goods": self.goods.get(account, {})}

    def balance(self, account, currency):
        return self.money.get(account, 0.0)


def closed(sales, purchases, book, specs=None):
    moves, transfers = [], []
    with mock.patch.object(actors_port.economy_api, "economy_book", lambda economy: book), \
            mock.patch.object(actors_port.economy_api, "move_goods", lambda economy, made: moves.extend(made)), \
            mock.patch.object(actors_port.economy_api, "post_transfers", lambda economy, made: transfers.extend(made)):
        result = actors_port.close(stand_in_economy(specs), sales, purchases)
    return result, moves, transfers


class SaleOrdersTests(unittest.TestCase):
    def test_a_sale_is_put_in_its_account_and_offered_at_the_weighted_reservation(self):
        sales = [{"seller": "firm:a", "material": GRAIN, "tonnes": 8.0, "concerns": [["n1", 6.0], ["n2", 2.0]]}]
        costs = {"n1": 1.0, "n2": 5.0}
        moves, orders = actors_port.sale_orders(stand_in_economy(), sales, per_unit, tile_of,
                                                lambda seller, node, material, tile: costs[node])
        self.assertEqual([(move.giver, move.receiver, move.good, move.tile, move.quantity) for move in moves],
                         [("edge:legacy", "sale:firm:a", GRAIN, FARMS, 4.0)])
        offer = orders[actors_port.sale_account("firm:a")].offers[0]
        self.assertEqual((offer.good, offer.area, offer.tile, offer.quantity, offer.reservation_price),
                         (GRAIN, "area:farms", FARMS, 4.0, 2.0))

    def test_a_good_the_economy_does_not_trade_is_not_offered(self):
        sales = [{"seller": "firm:a", "material": "unknown_kg", "tonnes": 10.0, "concerns": []}]
        self.assertEqual(actors_port.sale_orders(stand_in_economy(), sales, per_unit, tile_of,
                                                 lambda seller, node, material, tile: 0.0), ([], {}))


class PurchaseOrdersTests(unittest.TestCase):
    def test_a_purchase_is_a_fixed_quantity_bid_that_pays_up_to_the_whole_budget(self):
        purchases = [{"buyer": "state:a", "commodity": "grain", "tonnes": 6.0, "budget": 40.0}]
        orders, funding = actors_port.purchase_orders(stand_in_economy(), purchases, per_unit, tile_of,
                                                      lambda commodity: [GRAIN], 4.0)
        bid = orders[actors_port.buy_account("state:a")].bids[0]
        self.assertEqual((bid.good, bid.area, bid.tile), (GRAIN, "area:farms", FARMS))
        self.assertEqual(funding, [("state:a", 40.0, 10.0)])

    def test_a_commodity_with_no_traded_material_is_skipped(self):
        purchases = [{"buyer": "state:a", "commodity": "grain", "tonnes": 6.0, "budget": 40.0}]
        self.assertEqual(actors_port.purchase_orders(stand_in_economy(), purchases, per_unit, tile_of,
                                                     lambda commodity: ["other"], 4.0), ({}, []))


class FundTests(unittest.TestCase):
    def test_each_bid_is_funded_from_the_exchange_edge_into_its_buy_account(self):
        posted = []
        with mock.patch.object(actors_port.economy_api, "post_transfers", lambda economy, made: posted.extend(made)):
            actors_port.fund(stand_in_economy(), [("state:a", 40.0, 10.0)])
        self.assertEqual([(each.payer, each.payee, each.currency, each.amount) for each in posted],
                         [("edge:exchange", "buy:state:a", COIN, 10.0)])


class CloseTests(unittest.TestCase):
    def test_a_sale_account_returns_its_money_as_proceeds_and_its_unsold_goods_go_back_out(self):
        book = Book({"sale:firm:a": {GRAIN: {FARMS: 1.5}}}, {"sale:firm:a": 7.0})
        (proceeds, refunds, bought, delivered), moves, transfers = closed(
            [{"seller": "firm:a", "material": GRAIN, "tonnes": 4.0, "concerns": []}], [], book)
        self.assertEqual((proceeds, refunds, bought, delivered), ({"firm:a": 7.0}, {}, {}, {}))
        self.assertEqual([(move.giver, move.receiver, move.quantity) for move in moves],
                         [("sale:firm:a", "edge:legacy", 1.5)])
        self.assertEqual([(each.payer, each.payee, each.amount) for each in transfers],
                         [("sale:firm:a", "edge:exchange", 7.0)])

    def test_a_buy_account_returns_the_unspent_budget_and_reports_what_was_delivered(self):
        book = Book({"buy:state:a": {GRAIN: {FARMS: 3.0}}}, {"buy:state:a": 2.0})
        (proceeds, refunds, bought, delivered), _moves, _transfers = closed(
            [], [{"buyer": "state:a", "commodity": "grain", "tonnes": 6.0, "budget": 40.0}], book)
        self.assertEqual((proceeds, refunds, bought, delivered),
                         ({}, {"state:a": 2.0}, {"state:a": 3.0}, {"state:a": {GRAIN: 3.0}}))

    def test_a_bought_capital_asset_with_a_service_life_is_kept_in_the_held_account(self):
        specs = {GRAIN: types.SimpleNamespace(capital_asset=True, service_life_years=10.0)}
        book = Book({"buy:state:a": {GRAIN: {FARMS: 3.0}}}, {})
        _result, moves, _transfers = closed(
            [], [{"buyer": "state:a", "commodity": "grain", "tonnes": 6.0, "budget": 40.0}], book, specs)
        self.assertEqual([(move.giver, move.receiver, move.quantity) for move in moves],
                         [("buy:state:a", actors_port.held_account("state:a"), 3.0)])


class NoteTests(unittest.TestCase):
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
