"""`loss_memory.blend`: the lenders' rates come back in name order, whatever order the inputs list them in, so a save does
not depend on the process's string hashing."""
QUICK_TOPIC = True

import unittest

from sim.economy import loss_memory


class BlendOrderTest(unittest.TestCase):
    def test_rates_are_in_name_order_and_unchanged_in_value(self):
        remembered = {"zeta_bank": 0.02, "alpha_bank": 0.01, "mu_fund": 0.03}
        lost = {"beta_bank": 5.0, "alpha_bank": 1.0}
        claims = {"alpha_bank": 99.0, "beta_bank": 45.0, "zeta_bank": 10.0, "mu_fund": 30.0}
        rates = loss_memory.blend(remembered, lost, claims, 0.5, claim_life_years=1.0)
        self.assertEqual(list(rates), ["alpha_bank", "beta_bank", "mu_fund", "zeta_bank"])
        self.assertEqual(rates, {"alpha_bank": 0.5 * 0.01 + 0.5 * (1.0 / 100.0), "beta_bank": 0.5 * (5.0 / 50.0),
                                 "mu_fund": 0.5 * 0.03, "zeta_bank": 0.5 * 0.02})


if __name__ == "__main__":
    unittest.main()
