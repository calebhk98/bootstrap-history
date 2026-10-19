"""Complaint 513, ONE_PRICE_OWNER_PLAN stage 8: the hands kept on the land follow what a farm hour's food is worth
at the economy's staple price against the economy's unskilled wage, as a continuous response."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.labour import farm_intake
from sim.labour import labour_allocation

from .test_farm_surplus_intake import FOOD_TECHNIQUE, _nutrition_ratio
from .test_population_farm_technique import _complete, _rome, _run_years

ELASTICITY = 0.5
YEARS = 12


class HandsAtTheMarginTests(unittest.TestCase):
    def kept(self, ratio, satiation=100.0, land=100.0, current=10.0):
        return farm_intake.kept_farm_workers(current, satiation, land, ratio, ELASTICITY)

    def test_hands_stay_where_the_farm_hour_pays_the_wage_exactly(self):
        self.assertAlmostEqual(self.kept(1.0), 10.0)

    def test_hands_rise_and_fall_continuously_with_the_value_of_a_farm_hour(self):
        ratios = [0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0]
        kept = [self.kept(ratio) for ratio in ratios]
        self.assertEqual(kept, sorted(kept))
        self.assertEqual(len(set(kept)), len(kept))
        for lower, higher in zip(kept, kept[1:]):
            self.assertLess(higher - lower, 0.45 * higher)

    def test_a_farm_hour_worth_less_than_the_wage_lets_hands_go(self):
        self.assertLess(self.kept(0.5), 10.0)

    def test_hands_never_exceed_satiation_or_the_cleared_land(self):
        self.assertAlmostEqual(self.kept(50.0, satiation=14.0), 14.0)
        self.assertAlmostEqual(self.kept(50.0, land=12.0), 12.0)

    def test_no_price_or_wage_keeps_no_surplus_hands(self):
        self.assertEqual(self.kept(None), 0.0)


def _farm_share_after_wage_multiple(multiple):
    game = _rome()
    _complete(game, FOOD_TECHNIQUE)
    world = game.labour._world
    wage = world.economy_unskilled_wage
    world.economy_unskilled_wage = lambda: (wage() or 0.0) * multiple
    _run_years(game, YEARS)
    hours = game.state.economy.society_labour_hours
    return hours[labour_allocation.FARM_TRADE] / sum(hours.values()), _nutrition_ratio(game)


class FarmHoursFollowTheWageTests(unittest.TestCase):
    def test_farm_hours_fall_as_the_wage_elsewhere_rises(self):
        results = [_farm_share_after_wage_multiple(multiple) for multiple in (1.0, 3.0, 5.0, 12.0)]
        shares = [share for share, _nutrition in results]
        nutrition = [value for _share, value in results]
        self.assertEqual(shares, sorted(shares, reverse=True))
        self.assertLess(shares[-1], shares[0])
        self.assertEqual(nutrition, sorted(nutrition, reverse=True))


if __name__ == "__main__":
    unittest.main()
