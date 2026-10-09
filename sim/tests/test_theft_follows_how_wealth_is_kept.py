"""Complaint 273: expected theft loss depends on the kind of holding, its guarding, how visible the holder is and
the state's order, not on the money held alone; stolen money goes to the thieves, never destroyed."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents.purses import Purses
from sim.agents.edges import Edge, EDGE_THIEVES
from sim.engine import theft_exposure
from sim.engine.holdings_exposure import Exposure
from sim.engine.theft_charge import TheftChargeMixin

VALUE = 1000.0
ANNUAL = theft_exposure.THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE
CALM = dict(guard_hours_per_tonne_year=0.0, visible_scale=0.5, state_capacity=0.0, protection=0.0)


def loss_of(holdings, **overrides):
    return theft_exposure.expected_theft_loss(holdings, **dict(CALM, **overrides))


class TheftExposure(unittest.TestCase):

    def test_the_same_value_is_more_exposed_as_coin_than_as_land_or_loans(self):
        coin = loss_of({"coin": VALUE})
        for kept in ("land", "loans"):
            self.assertGreater(coin, loss_of({kept: VALUE}))
        self.assertGreater(coin, loss_of({"goods": VALUE}))
        self.assertGreater(loss_of({"goods": VALUE}), loss_of({"land": VALUE}))

    def test_more_guarding_lowers_exposure(self):
        self.assertLess(loss_of({"coin": VALUE}, guard_hours_per_tonne_year=60.0), loss_of({"coin": VALUE}))
        self.assertLess(loss_of({"coin": VALUE}, guard_hours_per_tonne_year=600.0),
                        loss_of({"coin": VALUE}, guard_hours_per_tonne_year=60.0))

    def test_a_well_ordered_state_lowers_it(self):
        self.assertLess(loss_of({"coin": VALUE}, state_capacity=0.9), loss_of({"coin": VALUE}, state_capacity=0.1))
        self.assertLess(loss_of({"coin": VALUE}, protection=0.8), loss_of({"coin": VALUE}))

    def test_a_more_visible_holder_loses_more(self):
        self.assertGreater(loss_of({"coin": VALUE}, visible_scale=1.0), loss_of({"coin": VALUE}, visible_scale=0.0))

    def test_loss_is_by_kind_and_never_more_than_held(self):
        holdings = {"coin": VALUE, "land": VALUE, "loans": -50.0}
        by_kind = theft_exposure.theft_loss_by_kind(holdings, **CALM)
        self.assertEqual(by_kind["loans"], 0.0)
        self.assertLessEqual(by_kind["coin"], VALUE)
        self.assertAlmostEqual(sum(by_kind.values()), loss_of(holdings))


class FakePurse:
    def __init__(self, money):
        self.money = money

    def credit(self, amount, purpose):
        self.money += amount

    def debit(self, amount, purpose):
        self.money -= amount


class TheftPaidToThieves(unittest.TestCase):

    def test_stolen_money_is_conserved_and_lands_with_the_thieves(self):
        balances = Purses()
        thieves = Edge(EDGE_THIEVES, balances)
        purse = FakePurse(VALUE)
        world = types.SimpleNamespace(edge=lambda name: thieves)
        exposure = Exposure(values={"coin": purse.money}, purse=purse.money)
        stolen = TheftChargeMixin.steal_from(world, purse, exposure, ANNUAL, **CALM)
        self.assertGreater(stolen, 0.0)
        self.assertAlmostEqual(purse.money + balances.purse(EDGE_THIEVES), VALUE)
        self.assertAlmostEqual(balances.purse(EDGE_THIEVES), stolen)

    def test_nothing_is_stolen_from_a_purse_holding_no_coin(self):
        purse = FakePurse(-20.0)
        world = types.SimpleNamespace(edge=lambda name: Edge(EDGE_THIEVES, Purses()))
        exposure = Exposure(values={}, purse=0.0)
        self.assertEqual(TheftChargeMixin.steal_from(world, purse, exposure, ANNUAL, **CALM), 0.0)
        self.assertEqual(purse.money, -20.0)


if __name__ == "__main__":
    unittest.main()
