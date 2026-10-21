"""Complaint 646: figures that were recalled now follow the value in the source that was opened."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.geography.api import soil_nutrients

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Powles et al., BMJ Open 2013;3:e003733, abstract: global mean salt intake in 2010, grams a day
GLOBAL_MEAN_SALT_GRAMS_PER_DAY = 10.06
DAYS_PER_YEAR = 365
# Clay and Carlson, SDSU iGrow Wheat ch. 12: pounds of nitrogen in a 60 pound bushel of wheat at 13.5 percent moisture
WHEAT_NITROGEN_POUNDS_PER_BUSHEL = 1.5
WHEAT_POUNDS_PER_BUSHEL = 60.0


def salt_kilograms_per_year(grams_per_day):
    return grams_per_day * DAYS_PER_YEAR / 1000.0


def nitrogen_fraction_of_grain(nitrogen_pounds, grain_pounds):
    return nitrogen_pounds / grain_pounds


class SaltSatiation(unittest.TestCase):

    def test_the_satiation_is_the_measured_world_mean_intake(self):
        with open(os.path.join(_ROOT, "data", "world", "needs.json"), encoding="utf-8") as handle:
            salt = json.load(handle)["needs"]["salt"]
        self.assertAlmostEqual(salt["satiation_per_capita_per_year"],
                               salt_kilograms_per_year(GLOBAL_MEAN_SALT_GRAMS_PER_DAY), places=2)

    def test_the_arithmetic_of_the_conversion(self):
        self.assertAlmostEqual(salt_kilograms_per_year(10.0), 3.65)


class GrainNitrogen(unittest.TestCase):

    def test_the_grain_fraction_is_nitrogen_per_bushel_over_the_bushel_weight(self):
        self.assertAlmostEqual(soil_nutrients.GRAIN_NITROGEN_FRACTION,
                               nitrogen_fraction_of_grain(WHEAT_NITROGEN_POUNDS_PER_BUSHEL, WHEAT_POUNDS_PER_BUSHEL))
