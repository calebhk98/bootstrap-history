"""Complaint 147: the part of a material bill beyond a year's market supply is priced at the market quote
(bought over the following years), and one year of the founder's own output is not counted by two projects."""
import unittest

from .harness import sim

_FIRST, _SECOND, _MATERIAL = "case_hardening", "arc_light_lamp", "charcoal_kg"
_BEYOND_A_YEAR = ("gunpowder", "nitre_kg")


def _row_beyond_a_year(game):
    return next(row for row in game.project_material_bill(_BEYOND_A_YEAR[0])["rows"] if row["material"] == _BEYOND_A_YEAR[1])


class InstalmentTests(unittest.TestCase):
    def test_part_beyond_a_years_supply_costs_the_market_quote(self):
        game = sim(capital=5e7)
        row = _row_beyond_a_year(game)
        self.assertGreater(row["missing_tonnes"], row["deliverable_now_tonnes"])
        spot = game.material_purchase_cost(row["material"], 0.0)[1]
        beyond = row["missing_tonnes"] - row["deliverable_now_tonnes"]
        self.assertAlmostEqual(row["cost_of_missing"] - row["cost_of_deliverable"], beyond * spot,
                               delta=1e-6 * row["cost_of_missing"])
        whole_order = game.material_purchase_cost(row["material"], row["missing_tonnes"])[0]
        self.assertLess(row["cost_of_missing"], whole_order)

    def test_up_front_money_is_the_deliverable_part_only(self):
        game = sim(capital=5e7)
        row = _row_beyond_a_year(game)
        self.assertLess(row["cost_of_deliverable"], row["cost_of_missing"])


class SharedOutputTests(unittest.TestCase):
    def _own_held(self, game, node_id):
        return sum(row["held_from_own_output_tonnes"] for row in game.project_material_bill(node_id)["rows"]
                   if row["material"] == _MATERIAL)

    def test_second_project_counts_only_the_output_left(self):
        game = sim(capital=5e7)
        game.state.holdings.forest_ha += 4
        alone = self._own_held(game, _SECOND)
        self.assertGreater(alone, 0)
        game.initialize_project(_FIRST)
        claimed = self._own_held(game, _FIRST)
        after = self._own_held(game, _SECOND)
        self.assertLess(after, alone)
        span = max(1.0, float(game.nodes[_SECOND].get("build_yrs") or game.nodes[_SECOND].get("yrs") or 1.0))
        supply = game._own_material_supply(game._material_tag(_MATERIAL)[1])
        self.assertLessEqual(after, max(0.0, supply - game.state.projects.active[_FIRST]["own_output_claim"].get(
            game._material_tag(_MATERIAL)[1], 0.0)) * span + 1e-6)
        self.assertGreater(claimed, 0)


if __name__ == "__main__":
    unittest.main()
