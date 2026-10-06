"""An exiting producer's dividend, once its lenders are repaid, drops a remainder that is only floating-point
residue: paying it would overdraw the producer by a rounding error and fail the whole year."""

QUICK_TOPIC = True

import unittest

from sim.economy import producer_exit
from sim.economy.types import Transfer


class ExitResidueTests(unittest.TestCase):
    def test_a_remainder_of_rounding_size_is_not_paid(self):
        payout = [Transfer("producer:a", "owner", "denarius", 1.0, "dividend")]
        self.assertEqual(producer_exit._less(payout, 1.0 - 2.0 ** -52), [])

    def test_a_real_remainder_is_paid(self):
        payout = [Transfer("producer:a", "owner", "denarius", 1.0e5, "dividend")]
        left = producer_exit._less(payout, 4.0e4)
        self.assertEqual([transfer.amount for transfer in left], [6.0e4])


if __name__ == "__main__":
    unittest.main()
