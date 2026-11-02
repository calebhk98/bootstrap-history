"""Every enabled partner is a country of the agent economy, and none trades by partner books (there are none). The foreign-trade module reads the
records the test states as a view; no game. The two countries' economy is in test_country_economy."""
import unittest

from sim.foreign_trade.module import ForeignTrade
from sim.tests import module_harness

QUICK_TOPIC = True


def records():
    return tuple({"civilization": name, "enabled": True, "from_year": -1000, "until_year": 3000} for name in ("han", "persia"))


def module(year=100, own="rome", variant_of=None):
    return module_harness.build(ForeignTrade, views={"foreign_economy_records": records(), "year": year,
                                                     "civilisation": {"id": own, "variant_of": variant_of}})


class PartnerSplitTests(unittest.TestCase):
    def test_every_partner_is_in_the_agent_economy(self):
        trade = module()
        self.assertEqual(trade.partners_in_agent_economy(), ["han", "persia"])

    def test_a_game_is_not_its_own_partner(self):
        self.assertEqual(module(own="han").partners_in_agent_economy(), ["persia"])

    def test_a_partner_outside_its_years_is_not_a_partner(self):
        self.assertEqual(module(year=5000).partners(), [])

    def test_a_variant_stands_in_for_its_base(self):
        self.assertEqual(module(own="variant", variant_of="han").partners(), ["persia"])


if __name__ == "__main__":
    unittest.main()
