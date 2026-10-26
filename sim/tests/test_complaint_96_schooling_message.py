"""Complaints/96: the census line says 'a generation of schooling' only once the school has run for a generation.
The rule is `census_phrase`, called here with the years built in the test."""
# presentation: the subject is the wording of one log line's opening phrase
QUICK_TOPIC = True

import unittest

from sim.diffusion.literacy_rules import census_phrase

GENERATION = 25


class CensusPhraseTests(unittest.TestCase):
    def test_a_school_opened_this_year_does_not_claim_a_generation(self):
        self.assertNotIn("generation", census_phrase(100, 100, GENERATION))

    def test_a_school_one_year_short_of_a_generation_does_not_claim_one(self):
        self.assertNotIn("generation", census_phrase(124, 100, GENERATION))

    def test_a_school_open_a_generation_claims_it(self):
        self.assertIn("a generation of schooling", census_phrase(125, 100, GENERATION))

    def test_an_old_school_claims_it(self):
        self.assertIn("a generation of schooling", census_phrase(130, 100, GENERATION))

    def test_no_recorded_school_start_does_not_claim_a_generation(self):
        self.assertNotIn("generation", census_phrase(500, None, GENERATION))


if __name__ == "__main__":
    unittest.main()
