"""Complaint 185, Complaint 640: the founder's household pays the state through the ledger: the loss is the treasury's
gain, booked by purpose, and a debt the household cannot cover is still paid (the purse goes negative). The ledger's
own rules are in test_actor_treasury."""
QUICK_TOPIC = True

import types
import unittest
from contextlib import nullcontext

from sim.agents.api import ActorRegistry, ActorsState
from sim.engine.society_actors import ActorsMixin
from sim.engine.state import ActorRecord


class Society(ActorsMixin):
    def __init__(self, treasury, household):
        self._treasury = treasury
        self.household = household

    def coin_carriage_listening(self):
        return nullcontext()

    def state_treasury(self):
        return self._treasury


def society(household_money):
    registry = ActorRegistry(ActorsState(home_country="rome_100ad"))
    treasury = registry.ensure_government("rome_100ad")
    household = registry.add("household", ActorRecord(kind="firm", money=household_money))
    return Society(treasury, household), treasury, household


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
