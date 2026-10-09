"""Complaint 273: coin moved between actors of the home country in different places pays carriage by its mass and
the distance, to the carriers; one place, credit and a party with no place cost nothing; a foreign country's actors
pay the keeping cost at their own country's pay to their own guards."""

QUICK_TOPIC = True

import types
import unittest

import sim.engine.core  # noqa: F401  (loads the engine in its import order)
from sim.agents import ledger
from sim.agents.edges import Edge, EDGE_COIN_GUARDS, EDGE_FREIGHT
from sim.engine import coin_carriage
from sim.engine.coin_carriage import CoinCarriageMixin
from sim.engine.coin_hoard import CoinHoardMixin

KG_PER_UNIT = 2.0
PER_TONNE = 100.0


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


def world():
    balances = {}
    sim = types.SimpleNamespace(
        state=types.SimpleNamespace(household=Party(0.0)), world_map=types.SimpleNamespace(tiles={"a": 1, "b": 2}),
        actors=types.SimpleNamespace(state=types.SimpleNamespace(home_country="home", countries={})),
        coin_kg_per_unit=lambda: KG_PER_UNIT, home_carriage_per_tonne=lambda origin, destination: PER_TONNE,
        edge=lambda name: Edge(name, balances, {}), balances=balances)
    sim.place_of = lambda actor: CoinCarriageMixin.place_of(sim, actor)
    sim.charge = lambda *args: CoinCarriageMixin.charge_coin_carriage(sim, *args)
    return sim


class Carriage(unittest.TestCase):

    def pay(self, sim, payer, payee, amount, purpose="wages"):
        with ledger.listening(sim.charge):
            ledger.transfer(payer, payee, amount, purpose)

    def test_the_mass_of_the_coin_and_the_haul_set_the_price(self):
        self.assertAlmostEqual(coin_carriage.carriage_money(1000.0, KG_PER_UNIT, PER_TONNE),
                               1000.0 * KG_PER_UNIT / 1000.0 * PER_TONNE)
        self.assertEqual(coin_carriage.carriage_money(1.0, 1e6, PER_TONNE), 1.0)

    def test_payment_between_places_pays_the_carriers_and_conserves_money(self):
        sim = world()
        payer, payee = Party(1000.0, "a", "home"), Party(0.0, "b", "home")
        self.pay(sim, payer, payee, 500.0)
        carriage = sim.balances[EDGE_FREIGHT]
        self.assertAlmostEqual(carriage, 500.0 * KG_PER_UNIT / 1000.0 * PER_TONNE)
        self.assertAlmostEqual(payer.money + payee.money + carriage, 1000.0)

    def test_one_place_credit_and_a_party_with_no_place_cost_nothing(self):
        sim = world()
        self.pay(sim, Party(1000.0, "a"), Party(0.0, "a"), 500.0)
        self.pay(sim, Party(1000.0, "a"), Party(0.0, "b"), 500.0, "interest")
        self.pay(sim, Party(1000.0, "a"), Party(0.0, None), 500.0)
        self.assertNotIn(EDGE_FREIGHT, sim.balances)

    def test_a_foreign_party_is_settled_by_the_foreign_route_instead(self):
        sim = world()
        self.pay(sim, Party(1000.0, "a", "home"), Party(0.0, "b", "abroad"), 500.0)
        self.assertNotIn(EDGE_FREIGHT, sim.balances)


class ForeignKeeping(unittest.TestCase):

    def test_a_foreign_actor_pays_its_own_countrys_guards_at_its_pay(self):
        balances = {}
        home, abroad = Party(1000.0, country="home"), Party(1000.0, country="abroad")
        scoped = types.SimpleNamespace(pay_per_person_year=lambda trade: 50.0)
        sim = types.SimpleNamespace(
            actors=types.SimpleNamespace(actors={"h": home, "f": abroad},
                                         state=types.SimpleNamespace(home_country="home"),
                                         world_for=lambda actor, shared: scoped if actor is abroad else shared),
            coin_keeping_cost_per_year=lambda money: 10.0, edge=lambda name: Edge(name, balances, {}))
        import sim.engine.agents_port as port
        original = port.SimWorld
        port.SimWorld = lambda _sim: types.SimpleNamespace(pay_per_person_year=lambda trade: 100.0)
        try:
            CoinHoardMixin.charge_actors_for_keeping_coin(sim)
        finally:
            port.SimWorld = original
        self.assertAlmostEqual(balances[EDGE_COIN_GUARDS], 10.0)
        self.assertAlmostEqual(balances[EDGE_COIN_GUARDS + ":abroad"], 5.0)


if __name__ == "__main__":
    unittest.main()
