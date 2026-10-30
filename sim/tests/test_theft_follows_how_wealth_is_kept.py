"""Complaint 273: expected theft loss depends on the kind of holding, its guarding, how visible the holder is and
the state's order, not on the money held alone; stolen money goes to the thieves, never destroyed."""

QUICK_TOPIC = True

import unittest

from sim.agents.edges import EDGE_THIEVES
from sim.coin import theft_exposure
from sim.coin.exposure import Exposure
from sim.coin.module import Coin
from sim.ledger.api import PayEdge
from sim.tests import module_harness

VALUE = 1000.0
ANNUAL = theft_exposure.THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE
CALM = dict(guard_hours_per_tonne_year=0.0, visible_scale=0.5, state_reach=0.0, protection=0.0)


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
        self.assertLess(loss_of({"coin": VALUE}, state_reach=0.9), loss_of({"coin": VALUE}, state_reach=0.1))
        self.assertLess(loss_of({"coin": VALUE}, protection=0.8), loss_of({"coin": VALUE}))

    def test_a_more_visible_holder_loses_more(self):
        self.assertGreater(loss_of({"coin": VALUE}, visible_scale=1.0), loss_of({"coin": VALUE}, visible_scale=0.0))

    def test_loss_is_by_kind_and_never_more_than_held(self):
        holdings = {"coin": VALUE, "land": VALUE, "loans": -50.0}
        by_kind = theft_exposure.theft_loss_by_kind(holdings, **CALM)
        self.assertEqual(by_kind["loans"], 0.0)
        self.assertLessEqual(by_kind["coin"], VALUE)
        self.assertAlmostEqual(sum(by_kind.values()), loss_of(holdings))


class TheftPaidToThieves(unittest.TestCase):

    def test_stolen_money_is_asked_of_the_purse_for_the_thieves(self):
        module = module_harness.build(Coin)
        stolen = module.steal_from(None, Exposure(values={"coin": VALUE}, purse=VALUE), ANNUAL, **CALM)
        self.assertGreater(stolen, 0.0)
        self.assertLess(stolen, VALUE)
        self.assertEqual(module_harness.sent(module), [PayEdge(EDGE_THIEVES, stolen, "theft")])

    def test_nothing_is_stolen_from_a_purse_holding_no_coin(self):
        module = module_harness.build(Coin)
        self.assertEqual(module.steal_from(None, Exposure(values={}, purse=0.0), ANNUAL, **CALM), 0.0)
        self.assertEqual(module_harness.sent(module), [])


if __name__ == "__main__":
    unittest.main()
