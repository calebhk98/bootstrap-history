"""Complaint 640: the engine's credit room is the agent economy's answer, and None until the economy answers or while the
lenders have not met. The economy's own credit_room rule is tested in test_economy_agent_credit."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.economy_capital_market import CapitalMarketMixin


class Game(CapitalMarketMixin):
    def __init__(self, answered, room):
        self.asked = []
        self.economy = types.SimpleNamespace(agent_credit_room=lambda actor_id: self.asked.append(actor_id) or (answered, room))


class MarketCreditRoom(unittest.TestCase):
    def test_an_answering_economy_gives_its_room_for_that_borrower(self):
        game = Game(True, 250.0)
        self.assertEqual(game.market_credit_room("founder"), 250.0)
        self.assertEqual(game.asked, ["founder"])

    def test_lenders_who_have_not_met_give_none_not_zero(self):
        self.assertIsNone(Game(True, None).market_credit_room("founder"))

    def test_an_economy_still_opening_gives_none(self):
        self.assertIsNone(Game(False, None).market_credit_room("founder"))

    def test_a_room_of_nothing_stays_nothing(self):
        self.assertEqual(Game(True, 0.0).market_credit_room("founder"), 0.0)


if __name__ == "__main__":
    unittest.main()
