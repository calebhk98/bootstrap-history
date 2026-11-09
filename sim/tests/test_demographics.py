"""demographics: the reachable pool for a trade is the labour core's people of it in the tiles reached. `Labour`
runs on a stand-in world (a real civilisation file and a real `Population`); the `population` report's rows are in test_population_report_rows and the hire refusal in test_cash_gates_wiring."""
QUICK_TOPIC = True

import unittest

from sim.labour.labour import Labour
from sim.tests.labour_stand_in import stand_in_world

HOURS = 2000.0


def labour_of(civ_id="rome_100ad"):
    world = stand_in_world(civ_id)
    world.people.home_tiles_held_version = lambda: 0
    world.knowledge.effect_factor = lambda channel, value, exponent=None: value
    return world, Labour(world)


class ReachablePool(unittest.TestCase):
    def test_a_common_trades_reachable_pool_is_the_core_people_of_it_in_the_tiles_reached(self):
        _world, labour = labour_of()
        _world.economy.agent_hours_offered_at = lambda trade, tile: 40.0 * HOURS if tile == labour.settlement.base_tile() else 900.0 * HOURS
        _world.economy.agent_people_by_tile_and_trade = lambda: {labour.settlement.base_tile(): {"smith": 40.0}}
        labour.book.core_people_by_trade = lambda: {"smith": 1000.0}
        self.assertAlmostEqual(labour.supply.market_supply("smith"), 40.0 * HOURS)

    def test_reachable_trade_population_reads_market_supply_as_people_not_hours(self):
        _world, labour = labour_of()
        self.assertAlmostEqual(labour.supply.reachable_trade_population("smith"), labour.supply.market_supply("smith") / HOURS, places=6)

    def test_the_country_holds_more_smiths_than_one_households_own_town_reaches(self):
        _world, labour = labour_of()
        _world.economy.agent_hours_offered_at = lambda trade, tile: 40.0 * HOURS
        _world.economy.agent_people_by_tile_and_trade = lambda: {labour.settlement.base_tile(): {"smith": 40.0}}
        labour.book.core_people_by_trade = lambda: {"smith": 1000.0}
        self.assertGreater(labour.supply.national_trade_population("smith"), labour.supply.reachable_trade_population("smith"))

    def test_the_block_form_gives_each_trades_figures_as_the_one_at_a_time_methods_do(self):
        world, labour = labour_of("norse_900ad")
        base = labour.settlement.base_tile()
        world.trades.trades_absent = {"mason"}
        world.economy.agent_people_by_tile_and_trade = lambda: {base: {"smith": 40.0, "weaver": 0.0, "scribe": 3.0}}
        world.economy.agent_hours_offered_at = lambda trade, tile: {"smith": 40.0 * HOURS, "weaver": 0.0}.get(trade)
        world.actors.actor_staff_fte = lambda trade: 5.0 if trade == "smith" else 0.0
        trades = sorted(world.trades.wages)
        self.assertTrue({"smith", "weaver", "scribe", "mason", "soldier"} <= set(trades))
        reachable, existing = labour.supply.reach_block(trades)
        self.assertEqual(reachable.tolist(), [labour.supply.reachable_trade_population(trade) for trade in trades])
        self.assertEqual(existing.tolist(), [labour.supply.people_who_exist(trade) for trade in trades])

    def test_a_literate_trades_reachable_figure_matches_the_real_hiring_wall(self):
        _world, labour = labour_of("norse_900ad")
        self.assertEqual(labour.supply.reachable_trade_population("scribe"), labour.supply.literate_capacity("scribe"))


if __name__ == "__main__":
    unittest.main()
