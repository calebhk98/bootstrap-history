"""`AgentEconomy.rename_agent`: a seat handed to another id is renamed in every note the port keeps per seat, the trades its log has
named as missing included."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.markets.agent_economy import AgentEconomy


class RenameAgentNotes(unittest.TestCase):
	def test_the_trades_a_seat_has_named_as_missing_follow_the_seat_to_its_new_id(self):
		port = AgentEconomy(SimpleNamespace())
		stored = {"trades_lacking_logged": {"seat_a": ["smith"]}, "seat_takings": {"seat_a": 3.0}}
		with mock.patch.object(AgentEconomy, "stored", new_callable=mock.PropertyMock, return_value=stored), \
				mock.patch.object(AgentEconomy, "opened", lambda self: False):
			port.rename_agent("seat_a", "seat_b")
		self.assertEqual(stored["trades_lacking_logged"], {"seat_b": ["smith"]})
		self.assertEqual(stored["seat_takings"], {"seat_b": 3.0})


if __name__ == "__main__":
	unittest.main()
