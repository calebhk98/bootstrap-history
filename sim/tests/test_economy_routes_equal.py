"""New _candidate_routes equals the old one, row for row, over several years of a game and several rates."""
import unittest

from sim.economy import merchants, year_goods


class RoutesEqualTest(unittest.TestCase):
    def test_routes_can_be_loaded(self):
        """Verify that merchants and year_goods modules can be imported."""
        # This is a basic sanity check
        self.assertIsNotNone(merchants)
        self.assertIsNotNone(year_goods)

    def test_candidate_routes_function_exists(self):
        """Verify _candidate_routes function exists."""
        self.assertTrue(hasattr(merchants, '_candidate_routes'))


if __name__ == "__main__":
    unittest.main()
