QUICK_TOPIC = True

import math
import unittest

from sim.economy.accounts import Book, InsufficientFunds
from sim.economy.households_basket import price_ceilings
from sim.economy.types import Transfer


def old_ceilings(shares):
    cost_per_unit = sorted((price / effect, good) for good, price, effect, _share in shares)
    result = []
    for good, price, effect, _share in shares:
        others = [cost for cost, other in cost_per_unit if other != good]
        parity = others[0] * effect if others else math.inf
        result.append(parity if parity >= price else math.inf)
    return tuple(result)


class TestCeilings(unittest.TestCase):
    def test_ceilings_match_sorted_form(self):
        shares = [("a", 2.0, 1.0, 0.5), ("b", 3.0, 2.0, 0.3), ("c", 9.0, 1.0, 0.2)]
        self.assertEqual(price_ceilings(shares), old_ceilings(shares))
        self.assertEqual(price_ceilings(shares[:1]), (math.inf,))

    def test_batch_overdraft_names_the_first_payer_in_order(self):
        book = Book()
        book.transfer(Transfer("edge:issue", "z", "coin", 5.0, "seed"))
        book.transfer(Transfer("edge:issue", "a", "coin", 5.0, "seed"))
        with self.assertRaises(InsufficientFunds) as context:
            book.post([Transfer("z", "m", "coin", 9.0, "x"), Transfer("a", "m", "coin", 9.0, "x")], [])
        self.assertTrue(str(context.exception).startswith("a would hold"))
        self.assertEqual(book.balance("a", "coin"), 5.0)


if __name__ == "__main__":
    unittest.main()
