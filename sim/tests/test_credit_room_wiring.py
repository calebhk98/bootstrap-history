"""Complaint 640: the credit room is the agent economy's answer, and None until the economy answers or while the
lenders have not met. The economy's own credit_room rule is tested in test_economy_agent_credit."""
QUICK_TOPIC = True

import unittest

from sim.finance.module import Finance
from sim.tests import module_harness


def room_of(answered, room, asked=None):
    module = module_harness.build(Finance, views={"agent_credit_room": lambda actor_id: (asked.append(actor_id) if asked is not None else None) or (answered, room)})
    return module.credit_room("founder")


class CreditRoom(unittest.TestCase):
    def test_an_answering_economy_gives_its_room_for_that_borrower(self):
        asked = []
        self.assertEqual(room_of(True, 250.0, asked), 250.0)
        self.assertEqual(asked, ["founder"])

    def test_lenders_who_have_not_met_give_none_not_zero(self):
        self.assertIsNone(room_of(True, None))

    def test_an_economy_still_opening_gives_none(self):
        self.assertIsNone(room_of(False, None))

    def test_a_room_of_nothing_stays_nothing(self):
        self.assertEqual(room_of(True, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
