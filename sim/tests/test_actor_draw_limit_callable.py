"""The callable the purses draw through: `Credit.limit(account, amount)` is the borrower's own `draw_limit`, and the whole
draw for an account no borrower stands behind (an edge, a seat's household)."""
QUICK_TOPIC = True

import types
import unittest

from sim.actors.world_credit import Credit


class Limit(unittest.TestCase):
    def credit(self):
        borrower = types.SimpleNamespace(draw_limit=lambda world, amount: min(amount, 5.0))
        return Credit(types.SimpleNamespace(registry=types.SimpleNamespace(actors={"firm:1": borrower})))

    def test_a_borrowers_account_is_limited_by_its_own_draw_limit(self):
        self.assertEqual(self.credit().limit("firm:1", 9.0), 5.0)

    def test_an_account_no_borrower_stands_behind_is_not_limited(self):
        self.assertEqual(self.credit().limit("edge:savers", 9.0), 9.0)


if __name__ == "__main__":
    unittest.main()
