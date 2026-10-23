"""A partner whose record puts it in the agent economy is listed there and no longer trades by the partner books; one that does not
stays on the books. Called on a stand-in game with the records the test states; no game. The two countries' economy is in
test_country_economy."""
import types
import unittest
from unittest import mock

from sim.engine import foreign_economies
from sim.engine.foreign_economies import ForeignEconomiesMixin

QUICK_TOPIC = True


def records(*inside):
    return tuple({"civilization": name, "enabled": True, "from_year": -1000, "until_year": 3000, "agent_economy": name in inside}
                 for name in ("han", "persia"))


def game(year=100, own="rome", variant_of=None):
    stand_in = types.SimpleNamespace(state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=year)),
                                     civ={"id": own, "variant_of": variant_of})
    stand_in.partner_countries = lambda: ForeignEconomiesMixin.partner_countries(stand_in)
    stand_in.partners_in_agent_economy = lambda: ForeignEconomiesMixin.partners_in_agent_economy(stand_in)
    return stand_in


class PartnerSplitTests(unittest.TestCase):
    def with_records(self, *inside):
        patcher = mock.patch.object(foreign_economies, "foreign_economy_records", lambda: records(*inside))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_partner_in_the_agent_economy_is_no_longer_traded_with_by_the_partner_books(self):
        self.with_records("han")
        stand_in = game()
        self.assertEqual(stand_in.partners_in_agent_economy(), ["han"])
        self.assertEqual(ForeignEconomiesMixin.foreign_economies(stand_in), ["persia"])
        self.assertEqual(stand_in.partner_countries(), ["han", "persia"])

    def test_with_no_partner_in_the_agent_economy_every_partner_trades_by_the_books(self):
        self.with_records()
        stand_in = game()
        self.assertEqual(stand_in.partners_in_agent_economy(), [])
        self.assertEqual(ForeignEconomiesMixin.foreign_economies(stand_in), ["han", "persia"])

    def test_a_game_is_not_its_own_partner(self):
        self.with_records("han")
        self.assertEqual(game(own="han").partners_in_agent_economy(), [])

    def test_a_partner_outside_its_years_is_not_a_partner(self):
        self.with_records("han")
        self.assertEqual(game(year=5000).partner_countries(), [])


if __name__ == "__main__":
    unittest.main()
