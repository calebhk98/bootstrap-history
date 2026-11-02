"""demographics: the reachable pool for a trade is the labour core's people of it in the tiles reached. `Labour`
runs on a stand-in world (a real civilisation file and a real `Population`); the `population` report's rows are in test_population_report_rows and the hire refusal in test_cash_gates_wiring."""
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
    world.effect_factor = lambda channel, value, exponent=None: value
    return world, Labour(world)


class ReachablePool(unittest.TestCase):
    def test_a_common_trades_reachable_pool_is_the_core_people_of_it_in_the_tiles_reached(self):
        _world, labour = labour_of()
        labour.core_people_by_tile_and_trade = lambda: {labour.base_tile(): {"smith": 40.0}, "far_tile": {"smith": 900.0}}
        labour.core_people_by_trade = lambda: {"smith": 1000.0}
        self.assertAlmostEqual(labour.market_supply("smith"), 40.0 * HOURS)

    def test_reachable_trade_population_reads_market_supply_as_people_not_hours(self):
        _world, labour = labour_of()
        self.assertAlmostEqual(labour.reachable_trade_population("smith"), labour.market_supply("smith") / HOURS, places=6)

    def test_the_country_holds_more_smiths_than_one_households_own_town_reaches(self):
        _world, labour = labour_of()
        labour.core_people_by_tile_and_trade = lambda: {labour.base_tile(): {"smith": 40.0}}
        labour.core_people_by_trade = lambda: {"smith": 1000.0}
        self.assertGreater(labour.national_trade_population("smith"), labour.reachable_trade_population("smith"))

    def test_a_literate_trades_reachable_figure_matches_the_real_hiring_wall(self):
        _world, labour = labour_of("norse_900ad")
        self.assertEqual(labour.reachable_trade_population("scribe"), labour.literate_capacity("scribe"))


if __name__ == "__main__":
    unittest.main()
