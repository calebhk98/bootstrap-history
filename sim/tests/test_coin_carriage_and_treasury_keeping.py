"""Complaint 273: coin moved across a route pays carriage by its mass, and a state's or firm's coin pays the
yearly keeping cost the household's does. Both rules are called on a stub game (`ForeignPaymentsMixin._settle_flow`,
`CoinHoardMixin.charge_actors_for_keeping_coin`); the household's own charge in a step is test_coin_keeping_charged."""
QUICK_TOPIC = True

import types
import unittest

import sim.engine.core  # noqa: F401  (loads the engine in its import order)
from sim.agents import ledger
from sim.agents.edges import EDGE_COIN_GUARDS, Edge
from sim.agents.purses import Purses
from sim.engine.coin_hoard import KEEPING_CAUSE, CoinHoardMixin
from sim.engine.foreign_payments import ForeignPaymentsMixin
from sim.world import coin_metal

KG_PER_UNIT = 4.0
PER_COIN = 2.0          # home money per partner coin unit
HOME_STOCK_UNITS = 1.0e6
GUARD_HOURS = 60.0
MONEY_PER_HOUR = 2.0


def settlement_game(carriage_share):
    """A stub game for `_settle_flow` with a partner whose coin weighs KG_PER_UNIT, carried by a route that takes
    `carriage_share` of the coin's own value per tonne-equivalent."""
    ledger_book = {"goods_in_value": 0.0, "goods_out_value": 0.0, "home_coin_units": 0.0, "partner_coin_units": 0.0,
                   "coin_carriage_units": 0.0}
    per_tonne = carriage_share * PER_COIN * 1000.0 / KG_PER_UNIT
    game = types.SimpleNamespace(
        _foreign_ledger=lambda _civ, create=False: ledger_book, _note_trade_value=lambda *_args: None,
        home_coin_stock_units=lambda: HOME_STOCK_UNITS, _partner_coin_opening_units=lambda _civ: 1.0e9,
        _coin_carriage_money_per_tonne=lambda _civ: per_tonne, partner_civ=lambda _civ: {"coin_standard": {"kg_per_unit": KG_PER_UNIT}})
    game.coin_carriage_units = lambda civ, units, rate: CoinHoardMixin.coin_carriage_units(game, civ, units, rate)
    game.ledger = ledger_book
    return game


def settled(carriage_share, flow_tonnes):
    """(the ledger after one settlement of 5% of the home coin stock, the units owed)."""
    game = settlement_game(carriage_share)
    value = 0.05 * HOME_STOCK_UNITS * PER_COIN
    ForeignPaymentsMixin._settle_flow(game, "partner", flow_tonnes, value, PER_COIN)
    return game.ledger, value / PER_COIN


class Carriage(unittest.TestCase):

    def test_with_free_carriage_the_partner_receives_the_whole_payment(self):
        book, owed = settled(0.0, 5.0)
        self.assertAlmostEqual(book["partner_coin_units"], owed)
        self.assertEqual(book["coin_carriage_units"], 0.0)

    def test_coin_carried_over_a_route_pays_carriage_so_the_partner_receives_less(self):
        free, _owed = settled(0.0, 5.0)
        dear, _owed = settled(0.2, 5.0)
        self.assertGreater(dear["partner_coin_units"], 0.0)
        self.assertLess(dear["partner_coin_units"], free["partner_coin_units"])

    def test_the_carriage_paid_is_recorded_in_coin_units(self):
        free, owed = settled(0.0, 5.0)
        dear, _owed = settled(0.2, 5.0)
        self.assertGreater(dear["coin_carriage_units"], 0.0)
        self.assertAlmostEqual(dear["coin_carriage_units"], free["partner_coin_units"] - dear["partner_coin_units"], delta=1e-6 * owed)

    def test_dearer_carriage_takes_proportionally_more_of_the_coin(self):
        free, _owed = settled(0.0, 5.0)
        dear, _owed = settled(0.2, 5.0)
        dearer, _owed = settled(0.4, 5.0)
        self.assertAlmostEqual(free["partner_coin_units"] - dearer["partner_coin_units"],
                               2.0 * (free["partner_coin_units"] - dear["partner_coin_units"]), places=6)

    def test_carriage_never_takes_more_coin_than_is_moved(self):
        self.assertEqual(coin_metal.carriage_units(10.0, KG_PER_UNIT, 1.0e12, PER_COIN), 10.0)

    def test_carriers_are_paid_so_an_import_or_an_export_leaves_the_total_coin_unchanged(self):
        for flow in (5.0, -5.0):
            game = settlement_game(0.2)
            ForeignPaymentsMixin._settle_flow(game, "partner", flow, 0.05 * HOME_STOCK_UNITS * PER_COIN, PER_COIN)
            book = game.ledger
            total = book["home_coin_units"] + book["partner_coin_units"] * PER_COIN
            self.assertGreater(book["coin_carriage_units"], 0.0, flow)
            self.assertAlmostEqual(total, 0.0, delta=1e-9 * book["coin_carriage_units"] * KG_PER_UNIT * 1e6, msg=flow)


class KeepingByAnyActor(unittest.TestCase):

    @staticmethod
    def actor(money, stratum=None, exited=None):
        record = types.SimpleNamespace(country=None, exited_year=exited, money=money, stratum=stratum)
        return types.SimpleNamespace(money=money, record=record, credit=lambda *_args: None, debit=lambda *_args: None)

    def charged(self, **actors):
        """What each named actor pays the guards in one year of `charge_actors_for_keeping_coin`."""
        balances = Purses()
        paid = {}
        for name, actor in actors.items():
            actor.debit = lambda amount, _purpose, name=name: paid.__setitem__(name, paid.get(name, 0.0) + amount)
            actor.credit = lambda *_args: None
        game = types.SimpleNamespace(
            actors=types.SimpleNamespace(actors=actors, state=types.SimpleNamespace(home_country="home")),
            coin_keeping_cost_per_year=lambda money: coin_metal.keeping_cost_per_year(money, KG_PER_UNIT, GUARD_HOURS, MONEY_PER_HOUR),
            edge=lambda name: Edge(name, balances))
        import sim.engine.agents_port as port
        original = port.SimWorld
        port.SimWorld = lambda _sim: types.SimpleNamespace(pay_per_person_year=lambda trade: 100.0)
        try:
            with ledger.listening(lambda *_args: None):
                CoinHoardMixin.charge_actors_for_keeping_coin(game)
        finally:
            port.SimWorld = original
        return paid, balances

    def test_a_state_and_a_firm_holding_coin_are_charged(self):
        paid, balances = self.charged(state=self.actor(1.0e8), firm=self.actor(1.0e8))
        self.assertGreater(paid["state"], 0.0)
        self.assertAlmostEqual(paid["firm"], paid["state"])
        self.assertAlmostEqual(balances.purse(EDGE_COIN_GUARDS), paid["state"] + paid["firm"])
        self.assertEqual(KEEPING_CAUSE, EDGE_COIN_GUARDS)

    def test_a_larger_treasury_is_charged_more(self):
        paid, _balances = self.charged(poor=self.actor(1.0e3), rich=self.actor(1.0e8))
        self.assertGreater(paid["rich"], paid["poor"])
        self.assertGreater(paid["poor"], 0.0)

    def test_an_actor_with_no_money_or_that_has_left_or_is_a_stratum_pays_nothing(self):
        paid, _balances = self.charged(broke=self.actor(0.0), gone=self.actor(1.0e8, exited=90),
                                       people=self.actor(1.0e8, stratum="peasants"))
        self.assertEqual(paid, {})


if __name__ == "__main__":
    unittest.main()
