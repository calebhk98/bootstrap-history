"""Complaint 111: scrap, unit labour, plant repair and input supply come from the tenure stock, the plant's
stated service lives and the producers the economy runs; none is authored per technology."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine import industry_concern, industry_learning as learning
from sim.engine.industry_concern import IndustryConcernMixin as Concern
from sim.engine.node_output import Baskets

FURNACE = {"good": "furnace", "build_labour_hours": {"mason": 300.0, "smith": 100.0}, "service_life_years": 10}


class ExperienceCurve(unittest.TestCase):

    def test_a_first_of_its_kind_concern_wastes_more_and_works_longer_than_an_established_one(self):
        first = learning.learning_multiplier(2.0, 2.0, 10.0)
        established = learning.learning_multiplier(10.0, 2.0, 10.0)
        self.assertGreater(first, 1.0)
        self.assertEqual(established, 1.0)
        self.assertEqual(learning.learning_multiplier(500.0, 2.0, 10.0), 1.0)

    def test_each_doubling_of_experience_takes_the_progress_ratio_off_the_multiplier(self):
        once = learning.learning_multiplier(2.0, 1.0, 100.0)
        doubled = learning.learning_multiplier(4.0, 1.0, 100.0)
        self.assertAlmostEqual(doubled / once, learning.LEARNING_PROGRESS_RATIO)

    def test_extra_scrap_and_hours_come_off_net_sales(self):
        self.assertEqual(learning.learning_value_ratio(100.0, 40.0, 20.0, 1.0), 1.0)
        worse = learning.learning_value_ratio(100.0, 40.0, 20.0, 1.2)
        self.assertAlmostEqual(worse, 1.0 - 0.2 * 60.0 / 100.0)
        self.assertEqual(learning.learning_value_ratio(100.0, 400.0, 20.0, 3.0), 0.0)
        self.assertEqual(learning.learning_value_ratio(0.0, 40.0, 20.0, 2.0), 1.0)


class PlantRepair(unittest.TestCase):

    def test_repair_labour_is_the_build_labour_over_the_service_life_by_the_share_in_use(self):
        hours = learning.repair_hours_by_trade([(FURNACE, 0.5)])
        self.assertEqual(hours, {"mason": 15.0, "smith": 5.0})

    def test_a_plant_with_no_stated_life_asks_for_no_repair(self):
        self.assertEqual(learning.repair_hours_by_trade([({"build_labour_hours": {"mason": 9.0}}, 1.0)]), {})

    def test_a_concern_with_tenured_repairers_loses_no_running_time(self):
        run, repair = {"smith": 800.0}, {"mason": 100.0}
        work = learning.work_hours_by_trade(run, repair)
        tenure = {trade: hours for trade, hours in work.items()}
        self.assertEqual(learning.running_availability(run, repair, tenure), 1.0)

    def test_without_tenured_repairers_the_concern_stands_in_proportion_to_the_repairs_left_undone(self):
        run, repair = {"smith": 800.0}, {"mason": 100.0}
        none = learning.running_availability(run, repair, {"smith": 5.0})
        half = learning.running_availability(run, repair, {"smith": 5.0, "mason": 0.5 * 100.0 / 900.0 * 5.5})
        self.assertAlmostEqual(none, 800.0 / 900.0)
        self.assertGreater(half, none)
        self.assertLess(half, 1.0)

    def test_a_concern_with_no_plant_never_waits_on_repairs(self):
        self.assertEqual(learning.running_availability({"smith": 800.0}, {}, {}), 1.0)


class InputSupply(unittest.TestCase):

    def test_a_far_off_shallow_supplier_costs_running_time_and_a_deep_near_one_costs_none(self):
        value = {"ore": 60.0, "coal": 40.0}
        near_deep = learning.input_availability(value, {"ore": 1.0, "coal": 1.0}, {"ore": 0.2, "coal": 0.2})
        near_shallow = learning.input_availability(value, {"ore": 0.0, "coal": 0.0}, {"ore": 0.0, "coal": 0.0})
        far_shallow = learning.input_availability(value, {"ore": 0.0, "coal": 0.0}, {"ore": 0.5, "coal": 0.5})
        self.assertEqual(near_deep, 1.0)
        self.assertEqual(near_shallow, 1.0)
        self.assertAlmostEqual(far_shallow, 0.5)

    def test_an_input_nobody_makes_is_not_counted(self):
        self.assertEqual(learning.input_availability({"ore": 10.0}, {}, {"ore": None}), 1.0)
        self.assertEqual(learning.input_availability({}, {}, {}), 1.0)


def concern_world(producers, days, depths=None):
    """A stand-in Sim for the input supply: `producers` {good: [(tile, recipe)]}, `days` to the base."""
    stub = types.SimpleNamespace(
        economy=types.SimpleNamespace(agent=types.SimpleNamespace(producers_by_good=lambda: producers)),
        state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=10)))
    stub._done_memo = lambda name, key, compute: compute()
    stub.industry_depth = lambda node_id: (depths or {}).get(node_id, 0.0)
    stub.days_from_producers = lambda found: days
    return stub


class ConcernInputs(unittest.TestCase):

    def setUp(self):
        industry_concern.default_production_entries = lambda: {"mine_ore": {"requires_node": "mining"}, "grow": {"requires_node": None}}

    def test_the_depth_of_the_supplying_industry_and_the_haul_set_the_loss(self):
        shallow = concern_world({"ore": [("hills", "mine_ore")]}, 365.0 / 2.0)
        deep = concern_world({"ore": [("hills", "mine_ore")]}, 365.0 / 2.0, {"mining": 1.0})
        self.assertAlmostEqual(Concern.concern_input_availability(shallow, "smelt", {"ore": 10.0}), 0.5, places=6)
        self.assertEqual(Concern.concern_input_availability(deep, "smelt", {"ore": 10.0}), 1.0)

    def test_a_technique_that_needs_no_technology_counts_as_established(self):
        stub = concern_world({"grain": [("farms", "grow")]}, 365.0)
        self.assertEqual(Concern.concern_input_availability(stub, "bake", {"grain": 5.0}), 1.0)

    def test_without_an_agent_economy_inputs_are_not_counted(self):
        stub = concern_world({}, 10.0)
        stub.economy.agent = None
        self.assertEqual(Concern.concern_input_availability(stub, "smelt", {"ore": 10.0}), 1.0)

    def test_an_unreachable_producer_is_not_counted(self):
        stub = concern_world({"ore": [("hills", "mine_ore")]}, None)
        self.assertEqual(Concern.concern_input_availability(stub, "smelt", {"ore": 10.0}), 1.0)


class PortListing(unittest.TestCase):

    def test_the_port_lists_each_good_with_the_tiles_and_recipes_that_make_it(self):
        from sim.engine.economy_port_year import AgentEconomy
        from sim.tests import economy_fixture
        economy, _outcomes = economy_fixture.run(years=1)
        listing = AgentEconomy.producers_by_good(types.SimpleNamespace(economy=lambda: economy))
        self.assertTrue(listing)
        for good, found in listing.items():
            for tile, recipe_id in found:
                self.assertIn(good, economy.setup.recipes[recipe_id].outputs)
                self.assertIn(tile, economy.setup.tiles)
        self.assertIn(economy_fixture.METAL, listing)


class HaulDays(unittest.TestCase):

    def stub(self, base):
        return types.SimpleNamespace(
            labour=types.SimpleNamespace(base_tile=lambda: base, held_technologies=lambda: set()),
            state=types.SimpleNamespace(economy=types.SimpleNamespace(improvements={})))

    def test_the_days_come_from_geography_between_the_nearest_producer_tile_and_the_base(self):
        from sim.geography import api as geography
        base, near = "afghanistan_01", "afghanistan_02"
        far = geography.tile_facts(near)["neighbours"][-1]
        stub = self.stub(base)
        self.assertEqual(Concern.days_from_producers(stub, [(base, "mine_ore")]), 0.0)
        nearest = Concern.days_from_producers(stub, [(near, "mine_ore"), (far, "mine_ore")])
        farther = Concern.days_from_producers(stub, [(far, "mine_ore")])
        self.assertGreater(nearest, 0.0)
        self.assertLessEqual(nearest, farther)


class WholeRatio(unittest.TestCase):

    def stub(self, experience, tenure):
        baskets = Baskets({"metal": 10.0}, {"ore": 10.0}, {}, {}, {"smith": 800.0}, [(FURNACE, 1.0)])
        stub = types.SimpleNamespace(concern_baskets_now=lambda node_id: baskets)
        stub.techniques_in_use = lambda: frozenset()
        stub._done_memo = lambda name, key, compute: compute()
        stub._concern_prices_in_hours = lambda held: {"metal": 20.0, "ore": 5.0}
        stub.founding_worker_years = lambda node_id: 2.0
        stub.industry_experience = lambda node_id: experience
        stub.industry_tenure_by_trade = lambda node_id: tenure
        stub.concern_input_availability = lambda node_id, purchases: 1.0
        return stub

    def test_an_established_concern_with_its_repairers_makes_its_stated_takings(self):
        stub = self.stub(50.0, {"smith": 810.0, "mason": 30.0})
        self.assertAlmostEqual(Concern.concern_learning_ratio(stub, "smelt"), 1.0)

    def test_a_young_industry_makes_less_than_its_stated_takings(self):
        young = self.stub(2.0, {"smith": 2.0, "mason": 0.25})
        self.assertLess(Concern.concern_learning_ratio(young, "smelt"), 1.0)

    def test_a_node_without_baskets_is_untouched(self):
        stub = self.stub(0.0, {})
        stub.concern_baskets_now = lambda node_id: None
        self.assertEqual(Concern.concern_learning_ratio(stub, "smelt"), 1.0)


if __name__ == "__main__":
    unittest.main()
