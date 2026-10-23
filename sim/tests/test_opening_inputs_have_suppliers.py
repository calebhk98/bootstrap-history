"""SCENARIO (Complaint 640): Complaint 570: at the opening every input the sized producers take is made, in the quantity they take, by the
producers sized beside them. A fuel made from timber is held to the timber, and so is every processor that burns it."""
import unittest

from sim.economy import opening
from sim.engine.economy_port_setup import build_setup
from sim.tests import harness

TOLERANCE = 1e-6      # share of the demand the float sums may miss by


def flows(setup, record):
    """({good: output of the producers at their expected sales}, {good: inputs they take at those sales})."""
    made, taken = {}, {}
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        for good, quantity in recipe.outputs.items():
            made[good] = made.get(good, 0.0) + quantity * producer.expected_sales * producer.yield_factor
        for good, quantity in recipe.inputs.items():
            taken[good] = taken.get(good, 0.0) + quantity * producer.expected_sales
    return made, taken


class OpeningInputsHaveSuppliersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = build_setup(harness.unopened_sim(civ="rome_100ad"))
        cls.record, cls.area_map, _carriage = opening.open_economy(cls.setup)

    def test_every_input_is_made_in_the_quantity_the_producers_take(self):
        made, taken = flows(self.setup, self.record)
        short = {good: (made.get(good, 0.0), wanted) for good, wanted in taken.items()
                 if made.get(good, 0.0) < wanted * (1.0 - TOLERANCE)}
        self.assertEqual(short, {})

    def test_charcoal_is_made_where_the_smelters_take_it(self):
        made, taken = flows(self.setup, self.record)
        self.assertGreater(taken["charcoal_kg"], 0.0)
        self.assertGreaterEqual(made["charcoal_kg"], taken["charcoal_kg"] * (1.0 - TOLERANCE))


if __name__ == "__main__":
    unittest.main()
