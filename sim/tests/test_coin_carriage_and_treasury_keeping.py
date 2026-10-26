"""Complaint 273: coin moved across a route pays carriage by its mass, and a state's or firm's coin pays the
yearly keeping cost the household's does. The foreign settlement is called on a stub game
(`ForeignPaymentsMixin._settle_flow`) whose carriage is the coin module's `coin_carriage_units` quote; the actors' keeping is
the coin module's `charge_keeping` command handler over plain actors; the household's own charge in a step is
test_coin_keeping_charged."""
QUICK_TOPIC = True

import types
import unittest

import sim.engine.core  # noqa: F401  (loads the engine in its import order)
from sim.agents.edges import EDGE_COIN_GUARDS
from sim.coin.commands import ChargeKeeping
from sim.coin.constants import COIN_GUARD_HOURS_PER_TONNE_YEAR, KEEPING_CAUSE
from sim.coin.module import Coin
from sim.engine.foreign_payments import ForeignPaymentsMixin
from sim.ledger.api import PayEdgeFrom
from sim.tests import module_harness
from sim.world import coin_metal

KG_PER_UNIT = 4.0
PER_COIN = 2.0          # home money per partner coin unit
HOME_STOCK_UNITS = 1.0e6
MONEY_PER_HOUR = 2.0
HOME_COIN = {"id": "home", "coin_standard": {"material": "silver_kg", "kg_per_unit": KG_PER_UNIT, "source": "test"}}


def settlement_game(carriage_share):
    """A stub game for `_settle_flow` with a partner whose coin weighs KG_PER_UNIT, carried by a route that takes
    `carriage_share` of the coin's own value per tonne-equivalent."""
    ledger_book = {"goods_in_value": 0.0, "goods_out_value": 0.0, "home_coin_units": 0.0, "partner_coin_units": 0.0,
                   "coin_carriage_units": 0.0}
    per_tonne = carriage_share * PER_COIN * 1000.0 / KG_PER_UNIT
    coin = module_harness.build(Coin, views={"partner_coin_standard": {"partner": {"kg_per_unit": KG_PER_UNIT}},
                                             "partner_route_cost": {"partner": per_tonne}})
    game = types.SimpleNamespace(
        _foreign_ledger=lambda _civ, create=False: ledger_book, _note_trade_value=lambda *_args: None,
        home_coin_stock_units=lambda: HOME_STOCK_UNITS, _partner_coin_opening_units=lambda _civ: 1.0e9,
        coin_carriage_units=coin.coin_carriage_units)
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

    def test_a_partner_with_no_known_route_is_carried_for_nothing(self):
        coin = module_harness.build(Coin, views={"partner_coin_standard": {"partner": {"kg_per_unit": KG_PER_UNIT}},
                                                 "partner_route_cost": {"partner": None}})
        self.assertEqual(coin.coin_carriage_units("partner", 10.0, PER_COIN), 0.0)

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
        return types.SimpleNamespace(money=money, record=record)

    def charged(self, **actors):
        """What each named actor is charged by one `ChargeKeeping`: {actor id: (edge, money, cause)}."""
        registry = types.SimpleNamespace(actors=actors, state=types.SimpleNamespace(home_country="home"))
        world = types.SimpleNamespace(pay_per_person_year=lambda trade: 100.0)
        module = module_harness.build(Coin, views={"civilisation": HOME_COIN, "money_per_labour_hour": MONEY_PER_HOUR,
                                                   "legacy_actor_registry": registry, "legacy_agent_world": world})
        module.charge_keeping(ChargeKeeping())
        commands = module_harness.sent(module)
        self.assertTrue(all(isinstance(command, PayEdgeFrom) for command in commands))
        return {command.actor: (command.edge, command.amount, command.purpose) for command in commands}

    def test_a_state_and_a_firm_holding_coin_are_charged_to_the_guards(self):
        paid = self.charged(state=self.actor(1.0e8), firm=self.actor(1.0e8))
        expected = coin_metal.keeping_cost_per_year(1.0e8, KG_PER_UNIT, COIN_GUARD_HOURS_PER_TONNE_YEAR, MONEY_PER_HOUR)
        self.assertEqual(paid["state"], (EDGE_COIN_GUARDS, expected, KEEPING_CAUSE))
        self.assertEqual(paid["firm"], paid["state"])
        self.assertEqual(KEEPING_CAUSE, EDGE_COIN_GUARDS)

    def test_a_larger_treasury_is_charged_more(self):
        paid = self.charged(poor=self.actor(1.0e3), rich=self.actor(1.0e8))
        self.assertGreater(paid["rich"][1], paid["poor"][1])
        self.assertGreater(paid["poor"][1], 0.0)

    def test_an_actor_with_no_money_or_that_has_left_or_is_a_stratum_pays_nothing(self):
        paid = self.charged(broke=self.actor(0.0), gone=self.actor(1.0e8, exited=90),
                            people=self.actor(1.0e8, stratum="peasants"))
        self.assertEqual(paid, {})


if __name__ == "__main__":
    unittest.main()
