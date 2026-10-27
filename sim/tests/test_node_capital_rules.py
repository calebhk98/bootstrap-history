"""A node's capital beyond its labour and materials is what its data states: the plant its entries run
in and the tooling for the staff places it names. Called on nodes written here, with the shipped goods and wages as prices; the
shipped tree is test_node_capital_validation."""
QUICK_TOPIC = True

import unittest

from sim.engine import data, tree_merge, validate_node_money
from sim.production import node_capital, node_revenue, node_revenue_census, node_upkeep
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

class CapitalFromStatedStaffAndPlant(unittest.TestCase):

    def test_tooling_is_a_share_of_a_year_of_each_staff_place(self):
        node = {"sch": 1.0, "art": 3.0}
        expected = 4.0 * node_capital.WORKPLACE_TOOLING_PERSON_YEARS_PER_PLACE * HOURS_PER_PERSON_YEAR
        self.assertAlmostEqual(node_capital.tooling_hours(node), expected)

    def test_a_node_with_no_staff_and_no_plant_needs_no_capital_beyond_its_bill(self):
        self.assertEqual(node_capital.capital_hours({"sch": 0, "art": 0}, plant_build_hours=0.0), 0.0)

    def test_plant_the_entries_state_adds_to_tooling(self):
        node = {"sch": 0, "art": 2.0}
        self.assertAlmostEqual(node_capital.capital_hours(node, plant_build_hours=500.0),
                               500.0 + node_capital.tooling_hours(node))

    def test_a_stated_figure_is_kept_and_labelled_authored(self):
        node = {"sch": 5.0, "art": 5.0, "cap_hours": 123.0}
        self.assertEqual(node_capital.resolve(node, plant_build_hours=9.0), (123.0, "authored"))
        self.assertEqual(node_capital.resolve({"sch": 0, "art": 0}, plant_build_hours=9.0), (9.0, "derived"))


class UpkeepThatIsNotStated(unittest.TestCase):

    def test_a_node_that_states_no_upkeep_keeps_up_what_it_cost_to_build(self):
        node = {"kind": "ENGINEERING"}
        self.assertAlmostEqual(node_upkeep.unstated_upkeep_hours(node, 1000.0),
                               node_upkeep.maintenance_hours(node, 1000.0))
        self.assertEqual(node_upkeep.unstated_upkeep_hours(node, 0.0), 0.0)

    def test_the_merge_gives_a_bare_node_no_capital_or_upkeep_of_its_own(self):
        bare = tree_merge.normalise_v2({"id": "bare", "name": "Bare", "cat": "x", "pre": [], "note": ""})
        self.assertNotIn("cap_hours", bare)
        self.assertNotIn("up_hours", bare)

    def test_a_stated_figure_written_as_text_is_still_read_as_a_number(self):
        node = tree_merge.normalise_v2({"id": "n", "name": "N", "cat": "x", "pre": [], "note": "",
                                        "cap_hours": "200-400", "up_hours": "30"})
        self.assertEqual((node["cap_hours"], node["up_hours"]), (200.0, 30.0))


class AppliedToABareNode(unittest.TestCase):

    def test_a_node_that_states_nothing_gets_a_derived_capital_and_a_default_upkeep(self):
        _tree, _document, _nodes, wages, goods = data.load()
        rate = data.starting_schedule().money_per_labour_hour
        node = {"id": "nothing_gates_this", "kind": "ENGINEERING", "sch": 0.0, "art": 2.0,
                "lab": {"labourer": 100.0}, "mat": {}, "_material_hours": 0.0}
        node_revenue.apply_revenue([node], goods, wages, rate)
        self.assertEqual(node["_capital_basis"], "derived")
        self.assertAlmostEqual(node["cap_hours"], node_capital.tooling_hours(node))
        self.assertEqual(node["_upkeep_basis"], "default")
        node["annual_labour_hours"] = {"labourer": 100.0}
        node_revenue.apply_revenue([node], goods, wages, rate)
        self.assertEqual(node["_upkeep_basis"], "programme")
        self.assertGreater(node["up_hours"], node_upkeep.maintenance_hours(node, 0.0) + 90.0)
        science = dict(node, kind="SCIENCE", sch=2.0, art=0.0)
        science.pop("annual_labour_hours")
        node_revenue.apply_revenue([science], goods, wages, rate)
        self.assertEqual(science["_upkeep_basis"], "staff")
        self.assertAlmostEqual(science["up_hours"], 2.0 * wages["scholar"] * HOURS_PER_PERSON_YEAR / rate)
        self.assertGreater(node["up_hours"], 0.0)
        self.assertEqual(node["rev_hours"], 0.0)


class CensusCountsTheCostBases(unittest.TestCase):

    def test_cost_bases_are_counted(self):
        nodes = {"a": {"_capital_basis": "derived", "_upkeep_basis": "derived", "_revenue_basis": "output"},
                 "b": {"_capital_basis": "authored", "_upkeep_basis": "programme"},
                 "c": {"_capital_basis": "derived", "_upkeep_basis": "default"}}
        capital = node_revenue_census.cost_basis_counts(nodes, "_capital_basis")
        upkeep = node_revenue_census.cost_basis_counts(nodes, "_upkeep_basis")
        self.assertEqual((capital["derived"], capital["authored"]), (2, 1))
        self.assertEqual((upkeep["derived"], upkeep["programme"], upkeep["default"]), (1, 1, 1))
        counts = node_revenue_census.basis_counts(nodes)
        self.assertEqual((counts["output"], counts["no product"]), (1, 2))


class OperatedNodesAreBounded(unittest.TestCase):

    def test_an_operated_node_nothing_bounds_is_an_error(self):
        production = {"made_kg": {"outputs": {"made_kg": 1.0}, "labour_hours": {"labourer": 1.0},
                                  "operated_by": ["maker"]}}
        unbounded = {"maker": {"id": "maker", "sch": 0, "art": 0}}
        self.assertEqual(len(validate_node_money.check_operated_nodes_are_bounded(unbounded, production)), 1)
        staffed = {"maker": {"id": "maker", "sch": 0, "art": 2}}
        self.assertEqual(validate_node_money.check_operated_nodes_are_bounded(staffed, production), [])



if __name__ == "__main__":
    unittest.main()
