"""A partner whose record puts it in the agent economy is listed there and no longer trades by the partner books; one that does not
stays on the books. The foreign-trade module reads the records the test states as a view; no game. The two countries' economy is in
test_country_economy."""
import unittest

from sim.foreign_trade.module import ForeignTrade
from sim.tests import module_harness

QUICK_TOPIC = True


def records(*inside):
    return tuple({"civilization": name, "enabled": True, "from_year": -1000, "until_year": 3000, "agent_economy": name in inside}
                 for name in ("han", "persia"))


def module(*inside, year=100, own="rome", variant_of=None):
    return module_harness.build(ForeignTrade, views={"foreign_economy_records": records(*inside), "year": year,
                                                     "civilisation": {"id": own, "variant_of": variant_of}})


class PartnerSplitTests(unittest.TestCase):
    def test_a_partner_in_the_agent_economy_is_no_longer_traded_with_by_the_partner_books(self):
        trade = module("han")
        self.assertEqual(trade.partners_in_agent_economy(), ["han"])
        self.assertEqual(trade.foreign_economies(), ["persia"])
        self.assertEqual(trade.partners(), ["han", "persia"])

    def test_with_no_partner_in_the_agent_economy_every_partner_trades_by_the_books(self):
        trade = module()
        self.assertEqual(trade.partners_in_agent_economy(), [])
        self.assertEqual(trade.foreign_economies(), ["han", "persia"])

    def test_a_game_is_not_its_own_partner(self):
        self.assertEqual(module("han", own="han").partners_in_agent_economy(), [])

    def test_a_partner_outside_its_years_is_not_a_partner(self):
        self.assertEqual(module("han", year=5000).partners(), [])

    def test_a_variant_stands_in_for_its_base(self):
        self.assertEqual(module(own="variant", variant_of="han").partners(), ["persia"])


if __name__ == "__main__":
    unittest.main()
