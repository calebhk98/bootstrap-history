"""`Labour.market_supply_split`: the hours of a trade a household can reach, said as the town's share and its own staff's share,
so hiring moves hours from one to the other and never conjures any (a screen that printed the raw total after a hire read as
hiring having drawn more of the trade into town). The `labour` screen lists a trade as hireable by the town's share."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour import Labour
from sim.tests.labour_stand_in import stand_in_world

HOURS = 2000.0


def labour_of(civ_id="rome_100ad"):
    world = stand_in_world(civ_id)
    world.shared_answer = lambda key, inputs, compute, standalone=False: compute()
    world.home_tiles_held_version = lambda: 0
    world.cfg = {"hired_hours_cap_base": 25000}
    world.effect_factor = lambda channel, value, exponent=None: value
    return world, Labour(world)


class MarketSupplySplitTest(unittest.TestCase):
    def test_employing_a_smith_leaves_the_towns_share_and_adds_his_hours_to_the_staffs(self):
        world, labour = labour_of()
        town_before, mine_before = labour.market_supply_split("smith")
        world.workforce.employees["smith"] = 1.0
        town_after, mine_after = labour.market_supply_split("smith")
        self.assertAlmostEqual(town_after, town_before, places=6)
        self.assertAlmostEqual(mine_after - mine_before, HOURS)

    def test_the_two_shares_add_up_to_the_total_supply(self):
        world, labour = labour_of()
        world.workforce.employees["smith"] = 3.0
        town, mine = labour.market_supply_split("smith")
        self.assertAlmostEqual(town + mine, labour.market_supply("smith"), places=6)

    def test_a_trade_with_no_market_at_all_is_all_the_staffs(self):
        world, labour = labour_of()
        world.trades_absent = {"smith"}
        town, mine = labour.market_supply_split("smith")
        self.assertEqual(town, 0.0)
        self.assertEqual(mine, labour.market_supply("smith"))


if __name__ == "__main__":
    unittest.main()
