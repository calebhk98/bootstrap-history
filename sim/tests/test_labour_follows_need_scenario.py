"""Scenario (Complaint 640; the rules are in test_labour_follows_need): the wage schedule a game builds prices
training at the civilisation's own interest rate."""
import random
import unittest

from sim.engine.data import load_civ
from sim.tests.harness import S, NODES, ORDER, build_unopened
from sim.labour import wages


class TrainingPremiumUsesCivilisationRateTests(unittest.TestCase):

    def test_the_schedule_prices_training_at_the_civilisations_rate(self):
        civ = load_civ("rome_100ad")
        engine = build_unopened(lambda: S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ))
        schedule = engine.labour.wage_schedule()
        years = schedule.training_years["smith"]
        self.assertAlmostEqual(schedule.premium("smith"),
                               wages.training_premium(years, civ["starting_interest_rate"]))


if __name__ == "__main__":
    unittest.main()
