"""Complaint 601: any actor builds a canal across a declared isthmus through `build_way`; it takes years, it
opens as a way under the pair's edge key, and an undeclared pair is refused with a cause."""
QUICK_TOPIC = True

import unittest

from sim.geography import api as geography
from sim.tests.test_ways_crew_and_works import _Builder

SUEZ = ("egypt_08", "egypt_06")


class BuildASeaCanalTests(unittest.TestCase):

    def test_the_canal_is_started_takes_years_and_then_opens_as_a_way(self):
        builder = _Builder(set(SUEZ))
        quote = builder.way_quote(*SUEZ, "sea_canal")
        self.assertGreater(quote["years"], 1.0)
        ok, message = builder.build_way(*SUEZ, "sea_canal")
        self.assertTrue(ok, message)
        self.assertEqual(builder.state.economy.improvements, {})
        builder.state.scenario.year += quote["years"] + 1
        builder.finish_ways()
        self.assertTrue(builder.state.economy.improvements[geography.edge_key(*SUEZ)]["sea_canal"])

    def test_a_pair_with_no_isthmus_is_refused_with_its_cause(self):
        builder = _Builder({"greece_01", "greece_02"})
        ok, message = builder.build_way("greece_01", "greece_02", "sea_canal")
        self.assertFalse(ok)
        self.assertEqual(message.cause, "no_isthmus")
        self.assertEqual(builder.paid, [])

    def test_the_price_is_paid_up_front_and_scales_with_the_work(self):
        builder = _Builder(set(SUEZ))
        quote = builder.way_quote(*SUEZ, "sea_canal")
        builder.build_way(*SUEZ, "sea_canal")
        self.assertAlmostEqual(builder.paid[0], quote["money"])
        self.assertGreater(quote["money"], quote["labour_hours"])


if __name__ == "__main__":
    unittest.main()
