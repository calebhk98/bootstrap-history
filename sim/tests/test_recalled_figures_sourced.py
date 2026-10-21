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


# WHO plague fact sheet: bubonic case-fatality ratio 30% to 60%; incubation one to seven days
WHO_BUBONIC_FATALITY_RANGE = (0.30, 0.60)
WHO_INCUBATION_DAYS_RANGE = (1.0, 7.0)
# Mordecai et al. 2013 via USGS abstract and Ryan et al. (arXiv 1407.7612): limits and decline, degrees C
MALARIA_TRANSMISSION_LIMITS_C = (17.0, 34.0)
MALARIA_DECLINE_ABOVE_C = 28.0
# CDC smallpox overview: scabs fallen three weeks after rash
SMALLPOX_RASH_TO_SCAB_DAYS = 21.0


def midpoint(low, high):
    return (low + high) / 2.0


def _disease(*parts):
    with open(os.path.join(_ROOT, "data", "disease", *parts), encoding="utf-8") as handle:
        return json.load(handle)


class DiseaseFigures(unittest.TestCase):

    def test_the_midpoint_function(self):
        self.assertAlmostEqual(midpoint(0.2, 0.4), 0.3)

    def test_bubonic_fatality_is_the_midpoint_of_the_who_range(self):
        self.assertAlmostEqual(_disease("bubonic_plague.json")["case_fatality"], midpoint(*WHO_BUBONIC_FATALITY_RANGE))

    def test_bubonic_incubation_is_the_midpoint_of_the_who_range(self):
        stage = _disease("bubonic_plague.json")["stages"][0]
        self.assertAlmostEqual(stage["mean_duration_in_days"], midpoint(*WHO_INCUBATION_DAYS_RANGE))

    def test_smallpox_infectious_stage_is_rash_to_scab(self):
        stage = _disease("smallpox.json")["stages"][1]
        self.assertAlmostEqual(stage["mean_duration_in_days"], SMALLPOX_RASH_TO_SCAB_DAYS)

    def test_malaria_envelope_follows_the_transmission_limits(self):
        envelope = {row["layer"]: row for row in _disease("endemic", "malaria.json")["challenge_envelope"]}
        temperature = envelope["mean_temperature_c"]
        self.assertEqual(tuple(temperature["tolerated"]), MALARIA_TRANSMISSION_LIMITS_C)
        self.assertEqual(temperature["optimal"][1], MALARIA_DECLINE_ABOVE_C)

    def test_no_disease_figure_is_still_tagged_recalled(self):
        for parts in (("bubonic_plague.json",), ("smallpox.json",), ("measles.json",),
                      ("endemic", "malaria.json"), ("endemic", "trypanosomiasis.json")):
            for key, entry in _disease(*parts)["sources"].items():
                self.assertNotEqual(entry["confidence"], "recalled", "%s %s" % (parts[-1], key))


# Naroll, American Antiquity 27(4), 1962, abstract: about one-tenth of the dwelling floor area in square metres is the population
NAROLL_SQUARE_METRES_PER_PERSON = 10.0
# Sphere minimum covered area, square metres a head (the shelter floor, sim/world/climate_needs.py)
SPHERE_FLOOR_SQUARE_METRES_PER_PERSON = 3.5
# Shukurov et al. (arXiv 1505.05121) section 8.1, quoting White 1965 on Columella and Halstead and Jones 1989, person-days a hectare
COLUMELLA_CYCLE_PERSON_DAYS = 44.0
COLUMELLA_REAPING_PERSON_DAYS = 5.7
THRESHING_PERSON_DAYS_AS_MANY_AS_REAPING = 1.0
HOURS_IN_THE_PERSON_DAY = 10.0
# Ellen 1982 via the same paper: hours a hectare to till with hand tools and with a pair of oxen
HAND_TILLING_HOURS = 400.0
OX_TILLING_HOURS = 65.0


def multiple_of_floor(area_per_person, floor_area_per_person):
    return area_per_person / floor_area_per_person


def wheat_cycle_hours(cycle_days, reaping_days, threshing_share_of_reaping, hours_per_day):
    return (cycle_days + reaping_days * (1.0 + threshing_share_of_reaping)) * hours_per_day


def hand_tilled_hours(team_hours, hand_tilling_hours, team_tilling_hours):
    return team_hours + hand_tilling_hours - team_tilling_hours


class PassFiveFigures(unittest.TestCase):

    @staticmethod
    def _load(*parts):
        with open(os.path.join(_ROOT, *parts), encoding="utf-8") as handle:
            return json.load(handle)

    def test_shelter_satiation_multiple_is_naroll_over_the_sphere_floor(self):
        shelter = self._load("data", "world", "needs.json")["needs"]["shelter"]
        self.assertAlmostEqual(shelter["satiation_multiple_of_floor"],
                               multiple_of_floor(NAROLL_SQUARE_METRES_PER_PERSON, SPHERE_FLOOR_SQUARE_METRES_PER_PERSON), places=2)

    def test_the_sourced_wheat_cycle_exceeds_the_labour_the_data_still_carries(self):
        # The data keeps its unsourced figure until the farm-year model that is built on it is re-derived
        # (Complaint 646 pass 5); this records the gap the sourced arithmetic shows.
        wheat = self._load("data", "production", "40_organics.json")["materials"]["wheat_kg"]
        sourced_hours = wheat_cycle_hours(COLUMELLA_CYCLE_PERSON_DAYS, COLUMELLA_REAPING_PERSON_DAYS,
                                          THRESHING_PERSON_DAYS_AS_MANY_AS_REAPING, HOURS_IN_THE_PERSON_DAY)
        self.assertGreater(sourced_hours, wheat["labour_hours"]["farmer"])

    def test_the_arithmetic_of_the_conversions(self):
        self.assertAlmostEqual(wheat_cycle_hours(10.0, 1.0, 1.0, 10.0), 120.0)
        self.assertAlmostEqual(wheat_cycle_hours(COLUMELLA_CYCLE_PERSON_DAYS, COLUMELLA_REAPING_PERSON_DAYS,
                                                 THRESHING_PERSON_DAYS_AS_MANY_AS_REAPING, HOURS_IN_THE_PERSON_DAY), 554.0)
        self.assertAlmostEqual(hand_tilled_hours(100.0, 40.0, 10.0), 130.0)
