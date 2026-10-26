"""Complaints/62: a technology's direct literacy effect respects the same ceiling schooling does.

The clamp is `literacy_after_effect`; the schooling path is `CountryLiteracy.school`. Both are called on values built
here. (`CountryLiteracy.set` clamping to its ceiling is held by test_country_literacy_totals.)"""
QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CountryLiteracy
from sim.diffusion.literacy_rules import literacy_after_effect

CEILING = 0.99


def literacy_of_one_class(literacy, property_share=0.3):
    registry = ActorRegistry(ActorsState(home_country="home"))
    stratum = registry.add("stratum:home:readers", ActorRecord(
        kind="stratum", country=None, stratum="readers", members=100, literacy=literacy,
        plan={"property_share": property_share}))
    return stratum, CountryLiteracy(registry.of_kind("stratum"))


class TechnologyEffectTests(unittest.TestCase):
    def test_an_effect_that_would_pass_the_ceiling_stops_at_it(self):
        self.assertEqual(literacy_after_effect(0.95, 0.2, CEILING), CEILING)

    def test_several_effects_in_a_row_still_stop_at_the_ceiling(self):
        share = 0.4
        for delta in (0.2, 0.3, 0.4):
            share = literacy_after_effect(share, delta, CEILING)
        self.assertEqual(share, CEILING)

    def test_an_effect_below_the_ceiling_adds_its_whole_delta(self):
        self.assertAlmostEqual(literacy_after_effect(0.4, 0.2, CEILING), 0.6)

    def test_a_share_already_above_the_ceiling_is_not_pulled_down_by_a_gain(self):
        self.assertEqual(literacy_after_effect(0.995, 0.1, CEILING), 0.995)

    def test_a_loss_lowers_the_share_but_never_below_nothing(self):
        self.assertAlmostEqual(literacy_after_effect(0.5, -0.2, CEILING), 0.3)
        self.assertEqual(literacy_after_effect(0.1, -0.5, CEILING), 0.0)

    def test_the_result_is_a_share_even_with_a_ceiling_of_one(self):
        self.assertEqual(literacy_after_effect(0.99, 0.5, 1.0), 1.0)


class SchoolingPathTests(unittest.TestCase):
    def test_a_school_closes_the_asked_fraction_of_the_gap(self):
        stratum, literacy = literacy_of_one_class(0.5)
        literacy.school("literacy_elite", 0.25, CEILING)
        self.assertAlmostEqual(stratum.record.literacy, 0.5 + 0.25 * (CEILING - 0.5))

    def test_a_school_never_takes_a_class_past_the_ceiling(self):
        stratum, literacy = literacy_of_one_class(0.95)
        literacy.school("literacy_elite", 1.0, CEILING)
        self.assertLessEqual(stratum.record.literacy, CEILING + 1e-12)
        self.assertAlmostEqual(stratum.record.literacy, CEILING)

    def test_a_class_above_the_ceiling_is_left_alone(self):
        stratum, literacy = literacy_of_one_class(0.995)
        literacy.school("literacy_elite", 0.5, CEILING)
        self.assertEqual(stratum.record.literacy, 0.995)


if __name__ == "__main__":
    unittest.main()
