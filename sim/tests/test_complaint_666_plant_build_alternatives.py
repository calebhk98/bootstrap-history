"""Complaint 666: a plant is built from what the society has. A capital part names `build_alternatives` after
its preferred bill; the solver treats the part as buildable when any build is and prices it from the first the
society can make, and the opening keeps a good whose plant has a buildable alternative. Each test calls the rule
on built inputs."""
QUICK_TOPIC = True

import unittest

from sim.economy.plant_builds import buildable, with_plant_from
from sim.economy.recipes import recipe_from_entry
from sim.engine import solve_prices_core as core
from sim.engine.economy_port_closure import makeable_prices
from sim.engine.validate_production import check_build_alternatives


def capital(alternatives=True):
    part = {"good": "hearth", "build_materials": {"iron": 10.0}, "build_labour_hours": {"smith": 100.0},
            "service_life_years": 20, "annual_output_at_basis": 100.0}
    if alternatives:
        part["build_alternatives"] = [
            {"build_materials": {"stone": 50.0}, "build_labour_hours": {"smith": 150.0}, "service_life_years": 10},
            {"build_materials": {"wood": 40.0}, "build_labour_hours": {"smith": 120.0}}]
    return part


def entry(alternatives=True):
    return {"outputs": {"charcoal": 100.0}, "inputs": {"wood": 400.0}, "labour_hours": {"burner": 30.0},
            "capital": [capital(alternatives)]}


class SolverTests(unittest.TestCase):
    def test_a_part_with_an_alternative_needs_only_the_materials_of_one_build(self):
        self.assertEqual(core._dependency_materials(entry(), {"wood", "stone"}), {"wood", "stone"})
        self.assertEqual(core._dependency_materials(entry(), {"wood", "iron", "stone"}), {"wood", "iron"})

    def test_a_part_with_no_alternative_still_needs_its_own_materials(self):
        self.assertEqual(core._dependency_materials(entry(False), {"wood", "stone"}), {"wood", "iron"})

    def test_the_plant_is_priced_from_the_first_build_the_society_can_make(self):
        wages = {"smith": 1.0}
        with_iron = core._capital_cost_hours_per_unit([capital()], {"iron": 2.0, "stone": 1.0, "wood": 1.0}, wages)
        self.assertAlmostEqual(with_iron, (10.0 * 2.0 + 100.0) / 20 / 100.0)
        without_iron = core._capital_cost_hours_per_unit([capital()], {"stone": 1.0, "wood": 1.0}, wages)
        self.assertAlmostEqual(without_iron, (50.0 * 1.0 + 150.0) / 10 / 100.0)
        wood_only = core._capital_cost_hours_per_unit([capital()], {"wood": 1.0}, wages)
        self.assertAlmostEqual(wood_only, (40.0 + 120.0) / 20 / 100.0)     # a build keeps the part's life unless it states one

    def test_a_plant_none_of_whose_builds_is_possible_has_no_cost(self):
        self.assertIsNone(core._capital_cost_hours_per_unit([capital()], {"clay": 1.0}, {"smith": 1.0}))

    def test_a_good_resolves_when_an_alternative_build_is_makeable(self):
        producers = {"wood": ["wood"], "charcoal": ["charcoal"]}
        production = {"wood": {"outputs": {"wood": 1.0}, "labour_hours": {"burner": 1.0}}, "charcoal": entry()}
        self.assertIn("charcoal", core.compute_resolvable_materials(production, producers))
        production["charcoal"] = entry(False)
        self.assertNotIn("charcoal", core.compute_resolvable_materials(production, producers))


class EconomyTests(unittest.TestCase):
    def test_makeable_prices_keeps_a_good_whose_plant_has_a_buildable_alternative(self):
        production = {"charcoal": entry()}
        recipes = {"charcoal": recipe_from_entry("charcoal", entry())}
        kept = makeable_prices({"charcoal": 1.0, "wood": 1.0, "stone": 1.0}, production, recipes)
        self.assertIn("charcoal", kept)

    def test_makeable_prices_drops_a_good_whose_plant_cannot_be_built_any_way(self):
        production = {"charcoal": entry()}
        recipes = {"charcoal": recipe_from_entry("charcoal", entry())}
        self.assertNotIn("charcoal", makeable_prices({"charcoal": 1.0, "clay": 1.0}, production, recipes))

    def test_the_plant_is_folded_from_the_first_buildable_alternative(self):
        recipe = recipe_from_entry("charcoal", entry())
        self.assertEqual(dict(recipe.plant_goods), {"iron": 10.0})
        stone = with_plant_from(recipe, {"stone", "wood"})
        self.assertEqual(dict(stone.plant_goods), {"stone": 50.0})
        self.assertEqual(stone.plant_life_years, 10.0)
        self.assertTrue(buildable(recipe, {"wood"}))
        self.assertFalse(buildable(recipe, {"clay"}))


class ValidatorTests(unittest.TestCase):
    def test_an_alternative_needs_a_basis_and_a_retire_when_a_heuristic(self):
        part = capital()
        known = {"iron", "stone", "wood"}
        self.assertEqual(len(check_build_alternatives("x", part, known, {"smith"})), 2)    # no basis
        for alternative in part["build_alternatives"]:
            alternative.update(alternative_basis="b" * 60, conf="D")
        self.assertEqual(len(check_build_alternatives("x", part, known, {"smith"})), 2)    # heuristic without retire
        for alternative in part["build_alternatives"]:
            alternative["retire"] = "Complaint 666"
        self.assertEqual(check_build_alternatives("x", part, known, {"smith"}), [])


if __name__ == "__main__":
    unittest.main()
