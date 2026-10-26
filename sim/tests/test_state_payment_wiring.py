"""Complaint 185, Complaint 640: the founder's household pays the state through the ledger: the loss is the treasury's
gain, booked by purpose, and a debt the household cannot cover is still paid (the purse goes negative). The polity module's
`pay_state` over a registry of actors; the ledger's own rules are in test_actor_treasury."""
QUICK_TOPIC = True

import unittest
from contextlib import nullcontext

from sim.agents.api import ActorRegistry, ActorsState
from sim.engine.state import ActorRecord
from sim.tests import polity_host


def society(household_money):
    registry = ActorRegistry(ActorsState(home_country="rome_100ad"))
    treasury = registry.ensure_government("rome_100ad")
    household = registry.add("household", ActorRecord(kind="firm", money=household_money))
    module = polity_host.build(state_treasury=treasury, legacy_household_actor=household, transfer_listening=nullcontext)
    return module, treasury, household


class PayState(unittest.TestCase):
    def test_the_households_loss_is_the_treasurys_gain_booked_by_purpose(self):
        game, treasury, household = society(1000.0)
        game.pay_state(300.0, {"requisition": 200.0, "office": 100.0})
        self.assertEqual(household.money, 700.0)
        self.assertEqual(treasury.money, 300.0)
        self.assertEqual(treasury.record.income, {"requisition": 200.0, "office": 100.0})

    def test_a_household_that_cannot_cover_it_is_paid_into_debt(self):
        game, treasury, household = society(100.0)
        game.pay_state(300.0, "confiscation")
        self.assertEqual(household.money, -200.0)
        self.assertEqual(treasury.money, 300.0)


if __name__ == "__main__":
    unittest.main()
