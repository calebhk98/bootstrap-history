"""sim/engine/data.py and prices.py against the real tree, one call each: `data.load` prices goods from the solver alone with no
price book behind it (the solver is a recorder), every material a node asks for is one the production data makes, and a real
civilisation's starting techs give a solved and a gated split in `goods_provenance` and positive prices from
`calculated_goods_prices`. The cache keying, the conversion and the solver's rules on synthetic entries are
test_engine_prices_rule."""
QUICK_TOPIC = True

import json
import os
import unittest
from unittest import mock

from sim.engine import data, prices as engine_prices

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def starting_techs(civilization_id):
    with open(os.path.join(ROOT, "data", "civilizations", civilization_id + ".json"), encoding="utf-8") as source:
        return json.load(source)["starting_techs"]


class LoadPricesFromTheSolverTests(unittest.TestCase):
    """`load()` with no arguments prices goods from the solver alone."""

    def load(self):
        with mock.patch.object(engine_prices, "priced_goods_table", return_value=({"sentinel_kg": 2.5}, {})) as solver:
            result = data.load()
        return result, solver

    def test_the_goods_are_the_solvers_table(self):
        (_tree, _document, _nodes, _wages, goods), _solver = self.load()
        self.assertEqual(goods, {"sentinel_kg": 2.5})

    def test_the_solver_prices_the_reference_civilisations_starting_techs_against_the_wage_document(self):
        (_tree, document, _nodes, _wages, _goods), solver = self.load()
        self.assertEqual(list(solver.call_args.args[0]), starting_techs(data.default_civilisation_id()))
        self.assertIs(solver.call_args.args[1], document)

    def test_the_wage_document_states_what_an_hour_of_labour_is_worth(self):
        (_tree, document, _nodes, _wages, _goods), _solver = self.load()
        self.assertGreater(document["money_per_labour_hour"], 0.0)


class MaterialsTheTreeAsksForTests(unittest.TestCase):
    def test_every_material_a_node_requires_is_one_the_production_data_makes(self):
        required = {material for node in data.load_base_tree()["nodes"] for material in node["mat"]}
        production = data.load_production_catalog(data.ROOT, data.MODDIR)
        made = {material for entry in production.values() for material in entry["outputs"]}
        self.assertEqual(sorted(required - made), [])


class RealCivilisationTests(unittest.TestCase):
    """One light check each against the committed data/production/ and data/civilizations/."""

    def setUp(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)

    def test_a_real_civilisations_starting_techs_give_both_solved_and_gated_goods(self):
        provenance = data.goods_provenance(starting_techs("rome_100ad"))
        solved = sum(1 for source in provenance.values() if source == "solved")
        gated = sum(1 for source in provenance.values() if source == "gated")
        self.assertGreater(gated, 0)
        self.assertGreater(solved, 0)
        self.assertEqual(solved + gated, len(provenance))

    def test_the_runtime_price_provider_prices_every_good_above_nothing(self):
        calculated = data.calculated_goods_prices(starting_techs("rome_100ad"), civilization_id="rome_100ad")
        self.assertTrue(calculated)
        self.assertEqual([material for material, price in sorted(calculated.items()) if not price > 0.0], [])


if __name__ == "__main__":
    unittest.main()
