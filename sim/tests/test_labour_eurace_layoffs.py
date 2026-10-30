"""Layoffs and vacancies of one employer, one function each (Complaint 608; Eurace Firm_set_labour_market_actions)."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing, layoffs


class Retain(unittest.TestCase):
    def test_an_employer_that_wants_fewer_hours_than_it_held_keeps_only_those_it_wants(self):
        kept = clearing.retain({"mill": 60.0}, {"mill": 100.0}, offered=1000.0)
        self.assertEqual(kept, {"mill": 60.0})

    def test_an_employer_that_wants_more_hours_than_it_held_keeps_all_it_held(self):
        kept = clearing.retain({"mill": 150.0}, {"mill": 100.0}, offered=1000.0)
        self.assertEqual(kept, {"mill": 100.0})


class LaidOffAndVacant(unittest.TestCase):
    def test_hours_held_beyond_those_needed_are_laid_off(self):
        self.assertEqual(layoffs.hours_to_lay_off(held=100.0, needed=60.0), 40.0)

    def test_nothing_is_laid_off_when_the_hours_needed_are_more(self):
        self.assertEqual(layoffs.hours_to_lay_off(held=100.0, needed=150.0), 0.0)

    def test_hours_needed_beyond_those_held_are_vacant(self):
        self.assertEqual(layoffs.hours_vacant(held=100.0, needed=150.0), 50.0)

    def test_no_hours_are_vacant_when_the_hours_held_are_more(self):
        self.assertEqual(layoffs.hours_vacant(held=100.0, needed=60.0), 0.0)


if __name__ == "__main__":
    unittest.main()
