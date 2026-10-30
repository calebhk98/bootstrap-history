"""demographics: the labour market was sized for a village; the reachable pool for a trade is a real town's worth. `Labour`
runs on a stand-in world (a real civilisation file and a real `Population`); the `population` report's rows are in test_population_report_rows and the hire refusal in test_cash_gates_wiring."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour import Labour
from sim.tests.labour_stand_in import stand_in_world

HOURS = 2000.0
OLD_VILLAGE_HOURS = 22500.0


def labour_of(civ_id="rome_100ad"):
    world = stand_in_world(civ_id)
    world.shared_answer = lambda key, inputs, compute, standalone=False: compute()
    world.home_tiles_held_version = lambda: 0
    world.cfg = {"hired_hours_cap_base": 25000}
    world.effect_factor = lambda channel, value, exponent=None: value
    return world, Labour(world)


class ReachablePool(unittest.TestCase):
    def test_a_common_trades_reachable_pool_is_a_real_towns_worth_not_the_old_village(self):
        world, labour = labour_of()
        expected = (labour.home_town_population_estimate() * world.population.working_age / world.population.total
                    * labour._non_farm_need_shares()["smith"] * HOURS)
        self.assertAlmostEqual(labour.market_supply("smith") - labour.employed("smith") * HOURS, expected, delta=1.0)

    def test_which_is_at_least_two_orders_of_magnitude_above_the_pre_fix_figure(self):
        _world, labour = labour_of()
        self.assertGreater(labour.market_supply("smith"), OLD_VILLAGE_HOURS * 10)

    def test_reachable_trade_population_reads_market_supply_as_people_not_hours(self):
        _world, labour = labour_of()
        self.assertAlmostEqual(labour.reachable_trade_population("smith"), labour.market_supply("smith") / HOURS, places=6)

    def test_the_country_holds_more_smiths_than_one_households_own_town_reaches(self):
        _world, labour = labour_of()
        self.assertGreater(labour.national_trade_population("smith"), labour.reachable_trade_population("smith"))

    def test_a_literate_trades_reachable_figure_matches_the_real_hiring_wall(self):
        _world, labour = labour_of("norse_900ad")
        self.assertEqual(labour.reachable_trade_population("scribe"), labour.literate_capacity("scribe"))


if __name__ == "__main__":
    unittest.main()
