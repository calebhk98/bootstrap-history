"""sim/engine/prices.py against the real tree: the engine's default (`sim.engine.data.load()` with no arguments)
prices every material from the solver with no price book behind it, and a real civilisation's starting techs give a
solved and a gated split. The cache keying, the conversion and the solver's rules on synthetic entries are
test_engine_prices_rule."""
import json
import os
import unittest

from sim.engine import data, prices as engine_prices


class EngineDefaultIsSolvedTests(unittest.TestCase):
    """`load()` with no arguments prices goods from the solver alone."""

    def test_default_goods_are_the_solved_table(self):
        _tree, document, nodes, _wages, goods = data.load()
        rate = data.starting_schedule().money_per_labour_hour
        reference_techs = data.load_civ()["starting_techs"]
        solved, _provenance = engine_prices.priced_goods_table(reference_techs, document)
        for material, price in solved.items():
            self.assertAlmostEqual(goods[material], price, msg=material)
        self.assertAlmostEqual(document["money_per_labour_hour"], rate)
        required = {material for node in nodes.values() for material in node["mat"]}
        # a material whose every technique needs a heat the society cannot reach has no price (it cannot be bought),
        # but it must be one the production data makes, not a misspelt name
        made = {material for entry in engine_prices._default_production_entries().values() for material in entry["outputs"]}
        self.assertEqual(sorted(required - set(goods) - made), [])


class RealDataIntegrationTests(unittest.TestCase):
    """One light check against the committed data/production/ and
    data/civilizations/, so the wiring is proven against the real tree and
    not only synthetic examples. Kept to a single gated solve (the
    expensive part), consistent with solve_prices.py's own measurement of a
    few tenths of a second per solve."""

    def test_a_real_civilizations_starting_techs_produce_a_measurable_split(self):
        engine_prices.reset_caches_for_tests()
        self.addCleanup(engine_prices.reset_caches_for_tests)
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "data", "civilizations",
                "rome_100ad.json")) as source:
            starting_techs = json.load(source)["starting_techs"]

        provenance = data.goods_provenance(starting_techs)
        solved_count = sum(1 for source in provenance.values() if source == "solved")
        gated_count = sum(1 for source in provenance.values() if source == "gated")
        self.assertGreater(gated_count, 0,
                           "nothing came back 'gated', so era gating is not "
                           "reaching this table at all")
        self.assertGreater(solved_count, 0,
                           "the solver resolved nothing under Rome's own "
                           "starting technologies - the gate or the wiring "
                           "is broken, not merely incomplete")
        self.assertEqual(solved_count + gated_count, len(provenance))

    def test_runtime_price_provider_uses_the_calculator_result(self):
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "data", "civilizations",
                "rome_100ad.json")) as source:
            starting_techs = json.load(source)["starting_techs"]

        calculated = data.calculated_goods_prices(
            starting_techs, civilization_id="rome_100ad")
        provenance = data.goods_provenance(
            starting_techs, civilization_id="rome_100ad")
        gated = next(material for material, source in sorted(provenance.items())
                     if source == "gated")
        solved = next(material for material, source in sorted(provenance.items())
                      if source == "solved")
        self.assertGreater(calculated[solved], 0.0)
        self.assertGreater(calculated[gated], 0.0)


if __name__ == "__main__":
    unittest.main()
