"""A node's capital beyond its labour and materials is what its data states: the plant its entries run
in and the tooling for the staff places it names. Nothing reads a typed capital figure from the tree."""
import glob
import json
import os
import unittest

from sim.engine import (data, node_capital, node_revenue, node_revenue_census, node_upkeep, tree_merge,
                        validate_node_money)
from sim.labour.labour_market import production_data
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

BRANCH_DIRECTORY = os.path.join(data.ROOT, "data", "branches")


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


class Validation(unittest.TestCase):

    def test_typed_revenue_is_an_error_and_the_real_tree_has_none(self):
        self.assertEqual(len(validate_node_money.check_no_typed_revenue({"x": {"_rev_hours_authored": 5.0}})), 1)
        _tree, _document, nodes, _wages, _goods = data.load()
        self.assertEqual(validate_node_money.check_node_money(nodes, production_data()), [])

    def test_an_operated_node_nothing_bounds_is_an_error(self):
        production = {"made_kg": {"outputs": {"made_kg": 1.0}, "labour_hours": {"labourer": 1.0},
                                  "operated_by": ["maker"]}}
        unbounded = {"maker": {"id": "maker", "sch": 0, "art": 0}}
        self.assertEqual(len(validate_node_money.check_operated_nodes_are_bounded(unbounded, production)), 1)
        staffed = {"maker": {"id": "maker", "sch": 0, "art": 2}}
        self.assertEqual(validate_node_money.check_operated_nodes_are_bounded(staffed, production), [])


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


class BranchDataStatesNoMoney(unittest.TestCase):

    def test_no_branch_node_types_a_capital_revenue_or_positive_upkeep(self):
        typed = []
        for path in sorted(glob.glob(os.path.join(BRANCH_DIRECTORY, "[0-9]*.json"))):
            with open(path) as handle:
                typed += [node["id"] for node in json.load(handle) if isinstance(node, dict)
                          and ("cap_hours" in node or node.get("rev_hours") or node.get("up_hours"))]
        self.assertEqual(typed, [])


class OutputNodesTypeNoFigure(unittest.TestCase):

    def test_a_node_that_earns_from_output_types_no_revenue_or_upkeep(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        output = {node_id for node_id, node in nodes.items() if node.get("_revenue_basis") == "output"}
        self.assertGreater(len(output), 20)
        for node_id in output:
            self.assertGreater(nodes[node_id]["_upkeep_hours_parts"]["staff"] + nodes[node_id]["rev_hours"], 0.0, node_id)

    def test_each_output_node_is_named_as_an_operator_by_the_entries_it_runs(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        operated = {name for entry in production_data().values() for name in entry.get("operated_by") or []}
        output = {node_id for node_id, node in nodes.items() if node.get("_revenue_basis") == "output"}
        self.assertEqual(sorted(output - operated), [])


class DerivedOnTheLoadedTree(unittest.TestCase):

    def setUp(self):
        _tree, _document, self.nodes, self.wages, self.goods = data.load()
        self.rate = data.starting_schedule().money_per_labour_hour

    def test_every_node_states_how_its_capital_was_found(self):
        for node_id, node in self.nodes.items():
            self.assertIn(node.get("_capital_basis"), ("derived", "authored"), node_id)
            self.assertGreaterEqual(node["cap_hours"], 0.0, node_id)

    def test_a_staffed_plant_node_carries_its_plant_and_tooling(self):
        blast = self.nodes["blast_furnace"]
        plant = blast["_upkeep_hours_parts"]["plant_build_hours"]
        self.assertGreater(plant, 0.0)
        self.assertAlmostEqual(blast["cap_hours"], node_capital.capital_hours(blast, plant),
                               delta=1e-6 * blast["cap_hours"])

    def test_capital_is_priced_in_the_coin_from_the_derived_hours(self):
        for node in self.nodes.values():
            self.assertAlmostEqual(node["cap"], node["cap_hours"] * self.rate, delta=1e-9 * (1 + node["cap"]))

    def test_the_derivation_leaves_a_stated_capital_alone(self):
        node = dict(self.nodes["blast_furnace"])
        for field in node_revenue.DERIVED_FIELDS:
            node.pop(field, None)
        node.pop("_cap_hours_authored", None)
        node["cap_hours"] = 77.0
        node_revenue.apply_revenue([node], self.goods, self.wages, self.rate)
        self.assertEqual((node["cap_hours"], node["_capital_basis"]), (77.0, "authored"))


if __name__ == "__main__":
    unittest.main()
