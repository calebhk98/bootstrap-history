"""Complaint 640: the cost breakdown `why` gives is the factors `project_cost` multiplies in. `_explain_cost` reports each factor
from the game (the labour and capital as authored, the civilisation, price-level, geography and opposition factors) and the
total as the game bills it; `project_cost_without_materials` is labour and capital times the price-level, civilisation and
rebuild factors. Each is called on a stand-in game with the factors written out; nothing is multiplied by the test. The
breakdown names the rebuild factor too, so while a lost node is rebuilt its factors still multiply out to its total."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests import materials_stand_in
from sim.ui.proto.techtree import _explain_cost

NODE = {"_labour_cost": 60.0, "cap": 10.0, "_material_cost": 30.0, "_total_cost": 100.0}


class Game:
    """The factors a project's cost is made of."""

    def __init__(self, rebuild=1.0):
        self.nodes = {"clock": NODE}
        self.rebuild = rebuild
        self.year = 100
        self.done, self.active, self.paid_towards = set(), {}, {}
        self.money_real = 1.0
        self.geography = types.SimpleNamespace(material_cost_factor=lambda node_id: 1.25)
        self.project_cost_without_materials = materials_stand_in.build(
            tree_nodes={"clock": NODE}, cost_money_factor=1.5, civ_cost_factor=lambda node_id: 0.8,
            rebuild_work_factor=lambda node_id: rebuild).project_cost_without_materials

    def cost_money_factor(self):
        return 1.5

    def civ_cost_factor(self, node_id):
        return 0.8

    def rebuild_work_factor(self, node_id):
        return self.rebuild

    def opposition_factor(self, node_id):
        return 1.1

    def project_material_bill(self, node_id):
        return {"cost_of_missing": 20.0, "rows": []}

    def project_cost(self, node_id):
        return 123.4


class ProjectCostWithoutMaterialsTests(unittest.TestCase):
    def test_labour_and_capital_are_scaled_by_the_price_level_and_the_civilisations_factor(self):
        self.assertAlmostEqual(Game().project_cost_without_materials("clock"), (100.0 - 30.0) * 1.5 * 0.8)

    def test_a_rebuild_scales_it_by_the_share_left_to_do(self):
        self.assertAlmostEqual(Game(rebuild=0.4).project_cost_without_materials("clock"), (100.0 - 30.0) * 1.5 * 0.8 * 0.4)


class ExplainCostTests(unittest.TestCase):
    def explained(self, rebuild=1.0):
        return _explain_cost(Game(rebuild=rebuild), {}, "clock", NODE)

    def test_the_authored_parts_and_the_missing_materials_are_reported(self):
        cost = self.explained()
        self.assertEqual((cost["labour"], cost["capital"], cost["materials"], cost["base_total"]), (60.0, 10.0, 20.0, 90.0))

    def test_the_factors_the_breakdown_names_are_the_games(self):
        cost = self.explained()
        self.assertEqual((cost["civ_domain_factor"], cost["price_index"], cost["material_distance_factor"],
                          cost["opposition_factor"]), (0.8, 1.5, 1.25, 1.1))

    def test_a_rebuild_names_the_share_left_to_do(self):
        self.assertEqual(self.explained(rebuild=0.4)["rebuild_factor"], 0.4)

    def test_the_total_is_what_the_game_bills(self):
        self.assertEqual(self.explained()["total"], 123.4)


if __name__ == "__main__":
    unittest.main()
