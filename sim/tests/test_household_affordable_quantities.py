"""What quantity of each affordable good of a need one household bids per need unit
(sim/economy/households_ability.py `quantity_per_need_unit`)."""

QUICK_TOPIC = True

import unittest

from sim.economy.households_ability import quantity_per_need_unit

# (good, price, need units one unit gives, share of spending)
WEAK = ("block", 34.0, 0.05, 0.1)       # 680 money a need unit
STRONG = ("brick", 80.0, 1.4, 0.9)      # about 57 money a need unit


class QuantityPerNeedUnitTest(unittest.TestCase):

    def test_everything_affordable_keeps_the_mixed_quantities(self):
        mix_index = 1.0 / (0.9 * 1.4 / 80.0 + 0.1 * 0.05 / 34.0)
        quantities = quantity_per_need_unit((WEAK, STRONG), mix_index, {"block": True, "brick": True})
        self.assertAlmostEqual(quantities["brick"], 0.9 * mix_index / 80.0)
        self.assertAlmostEqual(quantities["block"], 0.1 * mix_index / 34.0)

    def test_a_lone_good_cheaper_per_need_unit_than_the_mix_is_bought_only_to_meet_the_unit(self):
        quantities = quantity_per_need_unit((WEAK, STRONG), 100.0, {"block": False, "brick": True})
        self.assertAlmostEqual(quantities["brick"], 1.0 / 1.4)
        self.assertNotIn("block", quantities)

    def test_a_lone_good_dearer_per_need_unit_than_the_mix_is_limited_to_the_need_budget(self):
        quantities = quantity_per_need_unit((WEAK, STRONG), 100.0, {"block": True, "brick": False})
        self.assertAlmostEqual(quantities["block"], 100.0 / 34.0)

    def test_a_good_never_buys_more_need_units_than_the_unit_asked_for(self):
        quantities = quantity_per_need_unit((WEAK, STRONG), 1000.0, {"block": True, "brick": False})
        self.assertAlmostEqual(quantities["block"] * 0.05, 1.0)


if __name__ == "__main__":
    unittest.main()
