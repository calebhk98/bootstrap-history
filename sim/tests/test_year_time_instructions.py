"""`year-time --count-instructions`: the pure parts, on written-out inputs. Valgrind is never run here."""
QUICK_TOPIC = True

import unittest

from sim.ui import year_time_instructions as counting


class TotalInstructions(unittest.TestCase):
    def test_reads_the_summary_line(self):
        text = "desc: I1 cache:\ncmd: python3\nevents: Ir\nfl=a.py\n1 5\nsummary: 123456789\n"
        self.assertEqual(123456789, counting.total_instructions(text))

    def test_no_summary_line_is_none_not_zero(self):
        self.assertIsNone(counting.total_instructions("events: Ir\n"))


class PerYearInstructions(unittest.TestCase):
    def test_differences_of_runs_are_the_years(self):
        self.assertEqual((100, [40, 30]), counting.per_year_instructions([100, 140, 170]))

    def test_first_year_is_split_from_warm_years(self):
        self.assertEqual((40, [30, 31]), counting.split_first_and_warm([40, 30, 31]))


class ValgrindRefusal(unittest.TestCase):
    def test_missing_valgrind_refuses_with_a_cause(self):
        self.assertEqual("valgrind_missing", counting.valgrind_refusal(None).cause)

    def test_found_valgrind_does_not_refuse(self):
        self.assertIsNone(counting.valgrind_refusal("/usr/bin/valgrind"))


if __name__ == "__main__":
    unittest.main()
