"""Complaint 549: demography is fed what the agent economy's households ate, not the engine's own harvest.

Population is one national record, so the hunger is national; a tile's own hunger waits on a population tracked
by tile (Complaint 603). The economy half is built from structured accounts, here with no game; demography reading them is test_demography_eats_households_food."""
QUICK_TOPIC = True
import unittest

from sim.economy import year_accounts
from sim.demography.api import rules as food_eaten
from sim.economy.year_accounts import CohortAccount, YearAccounts


def _accounts(eaten_per_head_by_tile):
    """Accounts with one cohort per tile of 1000 people needing 100 units a head."""
    cohorts = [CohortAccount(cohort="cohort:" + tile, tile=tile, income_class=0, people=1000.0, need_per_head=100.0,
                             eaten_per_head=eaten, bought_per_head=eaten, own_plot_per_head=0.0,
                             real_income_per_head=1.0) for tile, eaten in eaten_per_head_by_tile.items()]
    return YearAccounts(year=1, cohorts=cohorts, tiles=year_accounts._tiles(cohorts))


class NationalFoodEatenTests(unittest.TestCase):
    """The economy's book: one tile's food cut (its imports removed) lowers that tile's figure and the nation's,
    and leaves the other tiles' figures as they were."""

    def test_removing_a_tiles_food_lowers_its_nutrition_and_the_nations_and_no_other_tile(self):
        fed = _accounts({"town": 100.0, "farms": 100.0, "hills": 100.0})
        cut = _accounts({"town": 40.0, "farms": 100.0, "hills": 100.0})
        by_tile = lambda accounts: {tile.tile: tile.eaten_over_need for tile in accounts.tiles}
        self.assertLess(by_tile(cut)["town"], by_tile(fed)["town"])
        self.assertEqual(by_tile(cut)["farms"], by_tile(fed)["farms"])
        self.assertEqual(by_tile(cut)["hills"], by_tile(fed)["hills"])
        self.assertLess(food_eaten.national_eaten_over_need(cut), food_eaten.national_eaten_over_need(fed))

    def test_the_national_figure_is_the_people_weighted_eaten_over_need(self):
        accounts = _accounts({"town": 40.0, "farms": 100.0, "hills": 100.0})
        self.assertAlmostEqual(food_eaten.national_eaten_over_need(accounts), 240.0 / 300.0, places=9)

    def test_no_cohort_means_no_figure(self):
        self.assertIsNone(food_eaten.national_eaten_over_need(YearAccounts(year=0)))


if __name__ == "__main__":
    unittest.main()
