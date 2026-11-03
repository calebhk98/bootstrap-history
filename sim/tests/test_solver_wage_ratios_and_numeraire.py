"""solver_wage_ratios refuses a registry trade the wage document leaves out; numeraire_trade reads a live registry."""
QUICK_TOPIC = True

import unittest

from sim.prices import prices, solve_prices_core


ENTRIES = {"forge": {"labour_hours": {"labourer": 1.0}, "capital": [{"build_labour_hours": {"smith": 2.0}}]}}


class SolverWageRatios(unittest.TestCase):

    def test_a_registry_trade_with_no_document_wage_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            prices.solver_wage_ratios(ENTRIES, {"labourer": 1.0})
        self.assertIn("smith", str(caught.exception))

    def test_a_complete_document_is_returned_as_it_is(self):
        self.assertEqual(prices.solver_wage_ratios(ENTRIES, {"labourer": 1.0, "smith": 2.0}),
                         {"labourer": 1.0, "smith": 2.0})


class NumeraireTrade(unittest.TestCase):

    def test_the_unskilled_trade_of_a_given_registry_is_the_numeraire(self):
        registry = {"hand": {"family": "labour", "training_years": 0.0},
                    "smith": {"family": "craft", "training_years": 5.0}}
        self.assertEqual(solve_prices_core.numeraire_trade(registry=registry), "hand")


if __name__ == "__main__":
    unittest.main()
