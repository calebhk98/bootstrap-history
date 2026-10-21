"""Scenario: in an opened Rome game the mining opex of a metal is its deposits' extraction labour at the miner's wage, under the
running techniques' effects. The hours-to-coin rules are in test_physical_money_constants."""
import random
import unittest

from sim.engine import data
from sim.engine.core import Sim
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import deposits


def build_opened(civ_name):
    from sim.tests import harness
    sim = Sim(harness.NODES, harness.ORDER, random.Random(1), events=False, manual=True, civ=data.load_civ(civ_name))
    sim.goal, sim.done_year = harness.GOAL, {}
    return sim


class MiningOpexInAGame(unittest.TestCase):

    def test_mining_opex_is_the_deposits_extraction_labour_at_the_miner_wage(self):
        sim = build_opened("rome_100ad")
        effects = sim.mine_works_effects()   # the running techniques change the works
        for metal in ("lead", "silver", "copper"):
            hours = sum(weight * KILOGRAMS_PER_TONNE
                        * deposits.extraction_cost_labour_hours_per_kg(deposit, effects)
                        for deposit, weight in sim._mine_reference_deposits(metal))
            self.assertAlmostEqual(sim._mine_opex(metal), hours * sim.labour.wage_per_hour("miner"),
                                   delta=1e-6, msg=metal)


if __name__ == "__main__":
    unittest.main()
