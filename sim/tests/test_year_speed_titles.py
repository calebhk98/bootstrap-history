"""Numba port item 7, land leases: `titles.free_share` given `titles.pledges_by_title` (one pass over the loans) equals the
share it works out by scanning every loan for each title. Random loans and titles, exact. No game."""

QUICK_TOPIC = True

import random
import types
import unittest

from sim.economy import titles
from sim.economy.types import Loan

TILES = ("T0", "T1", "T2")
HOLDERS = ("a", "b", "c", "d")


class PledgesByTitleAreTheScan(unittest.TestCase):

    def test_free_share_with_and_without_the_index(self):
        rng = random.Random(4)
        for _round in range(40):
            loans = []
            for index in range(rng.randrange(0, 30)):
                loan = Loan("loan:%d" % index, "bank", rng.choice(HOLDERS), "coin", 10.0, 0.05, 2.0, 0.0)
                loan.collateral_tile = rng.choice(TILES + ("",))
                loan.collateral_share = rng.uniform(0.0, 0.4)
                loans.append(loan)
            record = types.SimpleNamespace(
                credit=types.SimpleNamespace(loans=loans),
                land=types.SimpleNamespace(titles={tile: {holder: rng.uniform(0.0, 0.5) for holder in HOLDERS} for tile in TILES}))
            pledges = titles.pledges_by_title(record.credit)
            for tile in TILES:
                for holder in HOLDERS + ("nobody",):
                    self.assertEqual(titles.free_share(record, holder, tile, pledges), titles.free_share(record, holder, tile))


if __name__ == "__main__":
    unittest.main()
