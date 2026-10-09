"""A node's capital beyond its labour and materials is what its data states: the plant its entries run
in and the tooling for the staff places it names. Nothing reads a typed capital figure from the tree."""
import glob
import json
import os
import unittest

from sim.engine import data, node_capital, node_revenue, node_revenue_census, node_upkeep, tree_merge
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
        self.assertGreater(node["up_hours"], 0.0)
        self.assertEqual(node["rev_hours"], 0.0)


class CensusCountsTheCostBases(unittest.TestCase):

    def test_cost_bases_and_the_files_that_still_type_figures(self):
        nodes = {"a": {"_capital_basis": "derived", "_upkeep_basis": "derived"},
                 "b": {"_capital_basis": "authored", "_upkeep_basis": "authored", "_src": "f.json"},
                 "c": {"_capital_basis": "derived", "_upkeep_basis": "default"}}
        capital = node_revenue_census.cost_basis_counts(nodes, "_capital_basis")
        upkeep = node_revenue_census.cost_basis_counts(nodes, "_upkeep_basis")
        self.assertEqual((capital["derived"], capital["authored"]), (2, 1))
        self.assertEqual((upkeep["derived"], upkeep["default"], upkeep["authored"]), (1, 1, 1))
        self.assertEqual(dict(node_revenue_census.typed_figures_by_file(nodes)["f.json"]), {"up_hours": 1, "cap_hours": 1})
        self.assertTrue(node_revenue_census.format_file_lines(node_revenue_census.typed_figures_by_file(nodes)))


class BranchDataStatesNoCapital(unittest.TestCase):

    def test_capital_is_typed_only_where_a_typed_revenue_still_depends_on_it(self):
        """Capital and revenue convert together: a typed revenue over derived capital would repay in days."""
        typed = []
        for path in sorted(glob.glob(os.path.join(BRANCH_DIRECTORY, "[0-9]*.json"))):
            with open(path) as handle:
                typed += [node["id"] for node in json.load(handle)
                          if isinstance(node, dict) and "cap_hours" in node and not node.get("rev_hours")]
        self.assertEqual(typed, [])


class OutputNodesTypeNoFigure(unittest.TestCase):

    def test_a_node_that_earns_from_output_types_no_revenue_or_upkeep(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        output = {node_id for node_id, node in nodes.items() if node.get("_revenue_basis") == "output"}
        self.assertGreater(len(output), 20)
        typed = []
        for path in sorted(glob.glob(os.path.join(BRANCH_DIRECTORY, "[0-9]*.json"))):
            with open(path) as handle:
                typed += [node["id"] for node in json.load(handle)
                          if isinstance(node, dict) and node["id"] in output
                          and ("rev_hours" in node or "up_hours" in node)]
        self.assertEqual(typed, [])

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
