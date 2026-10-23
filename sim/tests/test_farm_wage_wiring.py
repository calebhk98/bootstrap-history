"""Complaint 513, ONE_PRICE_OWNER_PLAN stage 8: the hands kept on the land follow what a farm hour's food is worth at the
economy's staple price against the economy's unskilled wage. `_farm_hour_value_over_wage` reads the marginal product, the
wage and the staple price from the economy (None while any is missing), and `_kept_farm_workers` passes the ratio to
`farm_intake.kept_farm_workers`, so a dearer wage elsewhere keeps fewer hands. The rule on built inputs is
test_farm_hands_margin_rule and test_farm_satiation. A stand-in world holds only what the methods read."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.labour import labour_allocation
from sim.labour.labour_allocation import LabourAllocationMixin

STAPLE = "wheat_kg"
MARGINAL_PRODUCT = 0.5
PRICE = 2.0
WAGE = 1.0
CURRENT_FTE = 100.0


class World:
    def __init__(self, wage=WAGE, price=PRICE, marginal_product=MARGINAL_PRODUCT, taken=0.0):
        self.civ = {"staple": STAPLE}
        self.state = SimpleNamespace(holdings=SimpleNamespace(farm_last_marginal_product=marginal_product))
        self.farm_land = SimpleNamespace(hectares=1e9)
        self._wage, self._price, self._taken = wage, price, taken
        self.economy = SimpleNamespace(agent_prices=lambda: {STAPLE: self._price} if self._price else {})

    def economy_unskilled_wage(self):
        return self._wage

    def harvest_share_taken(self, material):
        assert material == STAPLE
        return self._taken


class Allocator(LabourAllocationMixin):
    def __init__(self, world):
        self._world = world

    def _share_farm_fte(self, population, technique):
        return CURRENT_FTE

    def _expected_year_farm_need(self, share, population, technique, intake_multiple=1.0):
        return 10.0 * CURRENT_FTE   # satiation above today's hands


TECHNIQUE = labour_allocation.farming_technique.DEFAULT_TECHNIQUE


class ValueOverWageTests(unittest.TestCase):
    def ratio(self, **world):
        return Allocator(World(**world))._farm_hour_value_over_wage(TECHNIQUE)

    def test_it_is_the_food_an_hour_yields_at_the_staple_price_over_the_wage(self):
        self.assertAlmostEqual(self.ratio(), PRICE * MARGINAL_PRODUCT / WAGE)

    def test_a_dearer_wage_elsewhere_lowers_it(self):
        self.assertLess(self.ratio(wage=3.0), self.ratio(wage=1.0))

    def test_the_share_of_the_harvest_the_state_takes_lowers_it(self):
        self.assertAlmostEqual(self.ratio(taken=0.25), 0.75 * self.ratio())

    def test_with_no_wage_no_price_or_no_marginal_product_there_is_no_ratio(self):
        self.assertIsNone(self.ratio(wage=None))
        self.assertIsNone(self.ratio(price=0.0))
        self.assertIsNone(self.ratio(marginal_product=None))


class KeptHandsFollowTheWageTests(unittest.TestCase):
    def kept(self, wage):
        return Allocator(World(wage=wage))._kept_farm_workers(CURRENT_FTE, 1000.0, TECHNIQUE)

    def test_a_wage_that_makes_a_farm_hour_dearer_than_the_wage_keeps_todays_hands(self):
        self.assertAlmostEqual(self.kept(0.5), CURRENT_FTE)

    def test_hands_fall_as_the_wage_elsewhere_rises(self):
        kept = [self.kept(wage) for wage in (1.0, 3.0, 5.0, 12.0)]
        self.assertEqual(kept, sorted(kept, reverse=True))
        self.assertLess(kept[-1], kept[0])

    def test_with_no_ratio_no_surplus_hands_are_kept(self):
        self.assertEqual(Allocator(World(wage=None))._kept_farm_workers(CURRENT_FTE, 1000.0, TECHNIQUE), 0.0)


if __name__ == "__main__":
    unittest.main()
