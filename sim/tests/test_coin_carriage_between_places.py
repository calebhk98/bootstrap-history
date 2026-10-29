"""Complaint 273: coin moved between actors of the home country in different places pays carriage by its mass and
the distance, to the carriers; one place, credit and a party with no place cost nothing; a foreign country's actors
pay the keeping cost at their own country's pay to their own guards (that half is test_coin_carriage_and_treasury_keeping).

The coin module answers the ledger's `transfer_surcharge` point; the ledger module posts the answer while it listens."""

QUICK_TOPIC = True

import types
import unittest

import sim.engine.core  # noqa: F401  (loads the engine in its import order)
from sim.agents import ledger
from sim.agents.purses import Purses
from sim.agents.edges import Edge, EDGE_FREIGHT
from sim.coin import rules
from sim.coin.module import Coin
from sim.ledger.api import LedgerSeat, SeatAccount, SeatActor
from sim.ledger.ledger import Ledger
from sim.tests import module_harness

KG_PER_UNIT = 2.0
PER_TONNE = 100.0
HOME_COIN = {"id": "home", "coin_standard": {"material": "silver_kg", "kg_per_unit": KG_PER_UNIT, "source": "test"}}


class Party:
    def __init__(self, money, place=None, country=None):
        self.money = money
        self.place = place
        self.record = types.SimpleNamespace(country=country, exited_year=None, money=money, stratum=None)

    def location(self):
        return self.place

    def credit(self, amount, purpose):
        self.money += amount

    def debit(self, amount, purpose):
        self.money -= amount


def world(home_place=None):
    """(the coin module, the ledger module listening through it, the book the edges keep)."""
    balances = Purses()
    coin = module_harness.build(Coin, views={
        "civilisation": HOME_COIN, "home_country": {"id": "home", "location": home_place},
        "tile_known": lambda tile: tile in ("a", "b"),
        "tile_haul_cost": lambda origin, destination: PER_TONNE})
    book = module_harness.build(Ledger, views={
        "transfer_surcharge": lambda *call: [coin.carriage_surcharge(*call)],
        "cast_state": types.SimpleNamespace(edge=lambda name: Edge(name, balances))})
    return coin, book, balances


class Carriage(unittest.TestCase):

    def pay(self, book, payer, payee, amount, purpose="wages"):
        with ledger.listening(book.after_transfer):
            ledger.transfer(payer, payee, amount, purpose)

    def test_the_mass_of_the_coin_and_the_haul_set_the_price(self):
        self.assertAlmostEqual(rules.carriage_money(1000.0, KG_PER_UNIT, PER_TONNE),
                               1000.0 * KG_PER_UNIT / 1000.0 * PER_TONNE)
        self.assertEqual(rules.carriage_money(1.0, 1e6, PER_TONNE), 1.0)

    def test_payment_between_places_pays_the_carriers_and_conserves_money(self):
        _coin, book, balances = world()
        payer, payee = Party(1000.0, "a", "home"), Party(0.0, "b", "home")
        self.pay(book, payer, payee, 500.0)
        carriage = balances.purse(EDGE_FREIGHT)
        self.assertAlmostEqual(carriage, 500.0 * KG_PER_UNIT / 1000.0 * PER_TONNE)
        self.assertAlmostEqual(payer.money + payee.money + carriage, 1000.0)

    def test_a_seats_own_purse_stands_at_the_home_countrys_centre(self):
        coin, _book, _balances = world(home_place="a")
        purse = SeatAccount(LedgerSeat(), Purses(), "founder")
        charge = coin.carriage_surcharge(purse, Party(0.0, "b", "home"), 500.0, "wages")
        self.assertEqual(charge, (EDGE_FREIGHT, 500.0 * KG_PER_UNIT / 1000.0 * PER_TONNE, "coin carriage"))

    def test_a_seat_as_a_party_in_the_book_has_no_place_of_its_own(self):
        coin, _book, _balances = world(home_place="a")
        party = SeatActor(LedgerSeat(), Purses(), "founder")
        self.assertIsNone(coin.carriage_surcharge(party, Party(0.0, "b", "home"), 500.0, "wages"))

    def test_the_surcharge_names_the_freight_edge_the_carriage_and_the_cause(self):
        coin, _book, _balances = world()
        charge = coin.carriage_surcharge(Party(1000.0, "a", "home"), Party(0.0, "b", "home"), 500.0, "wages")
        self.assertEqual(charge, (EDGE_FREIGHT, 500.0 * KG_PER_UNIT / 1000.0 * PER_TONNE, "coin carriage"))

    def test_one_place_credit_and_a_party_with_no_place_cost_nothing(self):
        coin, _book, _balances = world()
        self.assertIsNone(coin.carriage_surcharge(Party(1000.0, "a"), Party(0.0, "a"), 500.0, "wages"))
        self.assertIsNone(coin.carriage_surcharge(Party(1000.0, "a"), Party(0.0, "b"), 500.0, "interest"))
        self.assertIsNone(coin.carriage_surcharge(Party(1000.0, "a"), Party(0.0, None), 500.0, "wages"))

    def test_a_place_the_map_does_not_know_is_no_place(self):
        coin, _book, _balances = world()
        self.assertIsNone(coin.carriage_surcharge(Party(1000.0, "a"), Party(0.0, "nowhere"), 500.0, "wages"))

    def test_a_foreign_party_is_settled_by_the_foreign_route_instead(self):
        coin, _book, _balances = world()
        self.assertIsNone(coin.carriage_surcharge(Party(1000.0, "a", "home"), Party(0.0, "b", "abroad"), 500.0, "wages"))

    def test_the_carriage_is_not_itself_charged_carriage(self):
        _coin, book, balances = world()
        self.pay(book, Party(1000.0, "a", "home"), Party(0.0, "b", "home"), 500.0)
        self.assertAlmostEqual(balances.purse(EDGE_FREIGHT), 500.0 * KG_PER_UNIT / 1000.0 * PER_TONNE)


if __name__ == "__main__":
    unittest.main()
