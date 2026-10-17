"""Complaint 523: the full-length opening of norse_900ad passes its relationship checks (its own topic: see
test_full_length_opening_checks.py)."""
import unittest

from .full_length_opening_support import opening_check_tests


@opening_check_tests("norse_900ad")
class FullLengthOpeningTests(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
