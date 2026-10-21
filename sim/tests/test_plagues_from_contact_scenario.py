"""Scenario (Complaint 490): in an opened Rome game an epidemic year cuts the founder's staff by the working-age share the model
killed, and a quiet year takes nothing. The share itself (`working_age_death_share`) is in test_sixth_step_pure_functions."""
import unittest

from .harness import unopened_sim


class SeatsFeelTheModelsDeathsTest(unittest.TestCase):
    def test_an_epidemic_year_cuts_the_founders_staff_by_the_share_of_working_age_people_killed(self):
        game = unopened_sim(civ="rome_100ad", capital=1e6)
        game.scholars, game.artisans = 5000.0, 5000.0
        before = game.scholars
        share = game.epidemic_hits_seats({"working_age": game.population.working_age * 0.25}, game.year)
        self.assertAlmostEqual(share, 0.2, places=6)
        self.assertLess(game.scholars, before * 0.85)
        self.assertGreater(game.scholars, before * 0.7)

    def test_a_quiet_year_takes_nothing(self):
        game = unopened_sim(civ="rome_100ad", capital=1e6)
        game.scholars = 5000.0
        self.assertEqual(game.epidemic_hits_seats({}, game.year), 0.0)
        self.assertEqual(game.scholars, 5000.0)


if __name__ == "__main__":
    unittest.main()
