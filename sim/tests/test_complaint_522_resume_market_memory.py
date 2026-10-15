"""Complaints/522: a resumed economy holds the market memory the unbroken one holds. A year's flows change the
return-trip emptiness the areas are partitioned for only at the start of the next year; a record saved between
carries the memory keyed by the old areas, so the resume must partition them as the unbroken game had, then
follow them at the next year's start exactly as the unbroken game does."""
QUICK_TOPIC = False

import json
import unittest

from sim.economy import api as economy_api
from sim.economy.economy import Economy
from sim.economy.market_memory import KEY_SEPARATOR
from sim.tests import economy_fixture as fixture

CART_RATE = 0.5


def setup_where_full_returns_join_the_areas():
    """Empty returns split grain into three areas; carriers returning full join them into one."""
    return fixture.small_setup(carriage_rates={"cart": CART_RATE, "pack": 2 * CART_RATE, "sail": CART_RATE / 4},
                               carriage_rates_balanced={"cart": CART_RATE / 4, "pack": CART_RATE / 2,
                                                        "sail": CART_RATE / 16})


def economy_saved_after_a_year_of_two_way_trade():
    setup = setup_where_full_returns_join_the_areas()
    economy = Economy(setup)
    economy.step(fixture.quiet_year(setup))
    # the year's carriers met opposite flows: the record says so, the areas have not yet moved
    economy.record.carried = {fixture.TOWN: {fixture.FARMS: 10.0}, fixture.FARMS: {fixture.TOWN: 10.0}}
    saved = json.loads(json.dumps(economy_api.export_record(economy)))
    return setup, economy, economy_api.economy_from_record(setup, saved)


def memory_of(economy):
    memory = economy.record.memory
    return {name: dict(getattr(memory, name)) for name in ("prices", "usual_prices", "volume_weights")} | {
        "volumes": dict(economy.record.volumes)}


class ResumeTests(unittest.TestCase):

    def test_the_resume_partitions_the_areas_the_unbroken_game_holds(self):
        _setup, unbroken, resumed = economy_saved_after_a_year_of_two_way_trade()
        self.assertGreater(len(unbroken.area_map.areas(fixture.GRAIN)), 1)
        for good in unbroken.area_map.goods():
            self.assertEqual(resumed.area_map.areas(good), unbroken.area_map.areas(good), good)

    def test_every_remembered_market_of_the_resume_names_an_area_it_has(self):
        _setup, _unbroken, resumed = economy_saved_after_a_year_of_two_way_trade()
        for key in resumed.record.memory.prices:
            good, _separator, area_id = key.partition(KEY_SEPARATOR)
            if good in resumed.area_map.goods():
                self.assertIn(area_id, [area.area_id for area in resumed.area_map.areas(good)], key)

    def test_the_next_year_carries_the_same_memory_in_both_games(self):
        setup, unbroken, resumed = economy_saved_after_a_year_of_two_way_trade()
        unbroken_outcome = unbroken.step(fixture.quiet_year(setup))
        resumed_outcome = resumed.step(fixture.quiet_year(setup))
        self.assertEqual(len(unbroken.area_map.areas(fixture.GRAIN)), 1)
        self.assertEqual(memory_of(resumed), memory_of(unbroken))
        self.assertEqual(resumed_outcome.prices, unbroken_outcome.prices)
        self.assertEqual(resumed_outcome.output, unbroken_outcome.output)


if __name__ == "__main__":
    unittest.main()
