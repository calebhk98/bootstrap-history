"""A trader's cargo at home is orders in the economy's book, so the home price moves with it (Complaints/115).

Each cargo leg that touches home gets an account in the book: a landing cargo arrives from the partner's edge and is
offered, a taking cargo is bought with funds the trader put in. After the clear the account is closed: money back to
the trader's purse, goods the market did not take back over the partner's edge. Each function is called on a stand-in
economy built here; what the cargo does to the cleared price and to customs is the market's and the tax's own rule,
measured by `python3 sim/simulator.py economy-check`."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.book import Book, GoodsMove, Transfer
from sim.economy.types import EDGE_CARGO, external_edge
from sim.engine import economy_port_cargo as cargo

PARTNER = "partner"
GRAIN = "grain"
PORT = "port"
COIN_PER_UNIT = 2.0
UNITS_PER_TONNE = 1000.0   # the grain is counted in kilograms


def tonnes_per_unit(_material):
    return 1.0 / UNITS_PER_TONNE


def stand_in_economy(book=None):
    """What the cargo functions read of an economy: the goods it trades, a port tile, the coin rate and the book."""
    return SimpleNamespace(area_map=SimpleNamespace(goods=lambda: [GRAIN], area_of=lambda good, tile: "area:" + good),
                           setup=SimpleNamespace(port_tile=PORT, coin_per_unit=COIN_PER_UNIT, currency_id="unit"),
                           record=SimpleNamespace(book=book if book is not None else Book()))


def leg(kind, tonnes, paid=0.0, received=0.0):
    return {"id": "cargo:trader:test:%s:%s:%s" % (PARTNER, GRAIN, kind), "trader": "trader:test", "kind": kind,
            "source": PARTNER if kind == "in" else "home", "destination": "home" if kind == "in" else PARTNER,
            "partner": PARTNER, "material": GRAIN, "tonnes": tonnes, "paid": paid, "received": received}


class CargoOrders(unittest.TestCase):
    def test_a_landing_cargo_arrives_from_the_partners_edge_and_is_offered_at_any_price(self):
        landing = leg("in", 400.0, paid=100.0, received=100.0)
        moves, orders, fundings = cargo.cargo_orders(stand_in_economy(), [landing], tonnes_per_unit)
        units = 400.0 * UNITS_PER_TONNE
        self.assertEqual(moves, [GoodsMove(external_edge(PARTNER), landing["id"], GRAIN, PORT, units, "cargo landed")])
        offer, = orders[landing["id"]].offers
        self.assertEqual((offer.quantity, offer.reservation_price, offer.tile), (units, 0.0, PORT))
        self.assertEqual(fundings, [])

    def test_a_taking_cargo_is_funded_and_bids_a_fixed_quantity_up_to_what_it_fetches_abroad(self):
        budget_in_coin = 0.3 * 300.0 * UNITS_PER_TONNE
        taking = leg("out", 300.0, paid=budget_in_coin, received=2.0 * budget_in_coin)
        moves, orders, fundings = cargo.cargo_orders(stand_in_economy(), [taking], tonnes_per_unit)
        units, budget = 300.0 * UNITS_PER_TONNE, budget_in_coin / COIN_PER_UNIT
        self.assertEqual(moves, [])
        self.assertEqual(fundings, [Transfer(EDGE_CARGO, taking["id"], "unit", budget, "cargo funds")])
        bid, = orders[taking["id"]].bids
        self.assertEqual((bid.floor_quantity, bid.flexible_quantity), (0.0, units))
        self.assertAlmostEqual(bid.budget, budget)
        self.assertAlmostEqual(bid.maximum_price, 2.0 * budget_in_coin / COIN_PER_UNIT / units)

    def test_a_cargo_of_a_good_the_economy_does_not_trade_is_left_out_of_the_book(self):
        outside = dict(leg("in", 50.0), material="unknown_good")
        self.assertEqual(cargo.cargo_orders(stand_in_economy(), [outside], tonnes_per_unit), ([], {}, []))
        self.assertEqual(cargo.close_cargo_accounts(stand_in_economy(), [outside], tonnes_per_unit), {})

    def test_a_cargo_between_two_partners_never_touches_the_home_book(self):
        through = dict(leg("through", 50.0), source="a", destination="b")
        self.assertEqual(cargo.cargo_orders(stand_in_economy(), [through], tonnes_per_unit), ([], {}, []))

    def test_the_accounts_that_cross_the_border_are_the_landing_and_the_taking_cargoes(self):
        landing, taking = leg("in", 10.0), leg("out", 10.0, paid=5.0, received=9.0)
        self.assertEqual(cargo.border_accounts(stand_in_economy(), [taking, landing]), ((landing["id"],), (taking["id"],)))


class CloseCargoAccounts(unittest.TestCase):
    def test_a_landing_cargo_pays_the_trader_what_sold_and_returns_the_rest_over_the_partners_edge(self):
        landing = leg("in", 400.0)
        units, unsold = 400.0 * UNITS_PER_TONNE, 100.0 * UNITS_PER_TONNE
        book = Book()
        book.move(GoodsMove(external_edge(PARTNER), landing["id"], GRAIN, PORT, unsold, "cargo landed"))
        book.transfer(Transfer("edge:market", landing["id"], "unit", 30.0, "sale"))
        results = cargo.close_cargo_accounts(stand_in_economy(book), [landing], tonnes_per_unit)
        sold = results[landing["id"]]
        self.assertAlmostEqual(sold["tonnes"], (units - unsold) / UNITS_PER_TONNE)
        self.assertAlmostEqual(sold["money"], 30.0 * COIN_PER_UNIT)
        self.assertEqual(book.holdings(landing["id"]), {"money": {}, "goods": {}})
        self.assertAlmostEqual(-book.edge_goods_net(external_edge(PARTNER), GRAIN), 0.0)
        self.assertAlmostEqual(-book.edge_net(EDGE_CARGO, "unit"), 30.0)

    def test_a_taking_cargo_returns_what_it_did_not_spend_and_hands_the_goods_bought_to_the_partner(self):
        taking = leg("out", 300.0, paid=100.0, received=200.0)
        bought_units = 120.0 * UNITS_PER_TONNE / 10.0
        book = Book()
        book.move(GoodsMove("edge:market", taking["id"], GRAIN, PORT, bought_units, "purchase"))
        book.transfer(Transfer("edge:market", taking["id"], "unit", 5.0, "unspent funds"))
        results = cargo.close_cargo_accounts(stand_in_economy(book), [taking], tonnes_per_unit)
        bought = results[taking["id"]]
        self.assertAlmostEqual(bought["tonnes"], bought_units / UNITS_PER_TONNE)
        self.assertAlmostEqual(bought["money"], 5.0 * COIN_PER_UNIT)
        self.assertAlmostEqual(book.stock(external_edge(PARTNER), GRAIN, PORT), bought_units)
        self.assertEqual(book.holdings(taking["id"]), {"money": {}, "goods": {}})


if __name__ == "__main__":
    unittest.main()
