"""Rush filters: a bulk start can be limited by subject, per-project cost, founder hours and a list of ids. The filter parser,
the filter test and the exposure sum are called on nodes and a stand-in game the test builds; the loop that applies them is
test_rush_loop."""
import unittest
from types import SimpleNamespace

from sim.refusal import Refusal
from sim.ui.proto.rush_filters import parse_rush_filters, passes_rush_filters, rush_exposure

QUICK_TOPIC = True

NODES = {
    "cheap_textile": {"cat": "Textiles", "ph": 0, "risk": 0.1},
    "dear_textile": {"cat": "textiles", "ph": 40, "risk": 0.25},
    "metal": {"cat": "metallurgy", "ph": 10, "risk": 0.05},
}
COSTS = {"cheap_textile": 100.0, "dear_textile": 900.0, "metal": 400.0}
GAME = SimpleNamespace(project_cost=COSTS.get)


def passing(filters):
    return [node_id for node_id in NODES if passes_rush_filters(GAME, NODES, node_id, filters)]


class ParseTests(unittest.TestCase):
    def test_no_options_give_no_filters(self):
        self.assertEqual(parse_rush_filters({}, NODES), ({}, None))

    def test_a_category_is_kept_in_lower_case(self):
        self.assertEqual(parse_rush_filters({"category": " Textiles "}, NODES)[0], {"category": "textiles"})

    def test_cost_and_hours_ceilings_are_numbers(self):
        self.assertEqual(parse_rush_filters({"max_cost": "500", "max_hours": 0}, NODES)[0], {"max_cost": 500.0, "max_hours": 0.0})

    def test_a_non_numeric_or_negative_ceiling_is_refused(self):
        for bad in ("lots", -1, float("nan")):
            filters, error = parse_rush_filters({"max_cost": bad}, NODES)
            self.assertIsNone(filters)
            self.assertTrue(error)

    def test_ids_are_split_from_text_and_each_must_exist(self):
        self.assertEqual(parse_rush_filters({"ids": "metal, cheap_textile"}, NODES)[0], {"ids": ["metal", "cheap_textile"]})
        filters, error = parse_rush_filters({"ids": "metal,no_such_node"}, NODES)
        self.assertIsNone(filters)
        self.assertIsInstance(error, Refusal)
        self.assertEqual(error.cause, "unknown_node_ids")


class PassTests(unittest.TestCase):
    def test_no_filter_passes_everything(self):
        self.assertEqual(passing({}), list(NODES))

    def test_a_subject_keeps_only_that_category_whatever_its_case(self):
        self.assertEqual(passing({"category": "textiles"}), ["cheap_textile", "dear_textile"])

    def test_a_cost_ceiling_drops_the_dearer_projects(self):
        self.assertEqual(passing({"max_cost": 400.0}), ["cheap_textile", "metal"])

    def test_zero_hours_keeps_only_projects_needing_none(self):
        self.assertEqual(passing({"max_hours": 0.0}), ["cheap_textile"])

    def test_ids_keep_only_those_named(self):
        self.assertEqual(passing({"ids": ["metal"]}), ["metal"])

    def test_filters_combine(self):
        self.assertEqual(passing({"category": "textiles", "max_cost": 400.0}), ["cheap_textile"])


class ExposureTests(unittest.TestCase):
    def game(self, demand):
        return SimpleNamespace(trade_demand_vs_supply=lambda: demand)

    def test_expected_failures_are_the_sum_of_the_started_projects_own_risk(self):
        _bottlenecks, exposure = rush_exposure(self.game({}), NODES, [{"id": "cheap_textile"}, {"id": "dear_textile"}])
        self.assertAlmostEqual(exposure["expected_failures"], 0.35)
        self.assertEqual(exposure["riskiest"], "dear_textile")

    def test_nothing_started_has_no_riskiest(self):
        self.assertEqual(rush_exposure(self.game({}), NODES, [])[1], {"expected_failures": 0.0, "riskiest": None})

    def test_only_oversubscribed_trades_are_bottlenecks(self):
        demand = {"smith": {"demand_hours_this_year": 9.0, "supply_hours_this_year": 3.0, "oversubscribed": True},
                  "weaver": {"demand_hours_this_year": 1.0, "supply_hours_this_year": 3.0, "oversubscribed": False}}
        bottlenecks, _exposure = rush_exposure(self.game(demand), NODES, [])
        self.assertEqual(bottlenecks, [{"trade": "smith", "demand_hours_this_year": 9.0, "supply_hours_this_year": 3.0}])


if __name__ == "__main__":
    unittest.main()
