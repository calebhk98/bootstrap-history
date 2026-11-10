"""`year_arrays_holdings.share_out` (the producers' worths split over cohorts in one kernel) gives exactly what the producer-by-producer split
`equity.share_out_by_producer` gives, floats and key order, on random cohorts, ownership shares and outside share holders; no game."""

QUICK_TOPIC = True

import dataclasses
import random
import types
import unittest

from sim.economy.equity import share_out_by_producer
from sim.economy.households_cohort import Cohort
from sim.economy.year_arrays_holdings import share_out
from sim.tests.year_close_fixture import TILES, economy_of


def record_of(seed):
    """The fixture economy's record with more cohorts, random ownership shares and some producers with shares held outside."""
    rng = random.Random(seed)
    _setup, record, _view, _ledger, _area_map = economy_of(seed)
    record.cohorts = {}
    for tile in TILES:
        for index in range(rng.randrange(1, 4)):
            cohort = Cohort("household:%s:%d" % (tile, index), tile, index, 100.0, 40.0, 1.0)
            cohort.ownership_share = rng.choice((0.0, rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0)))
            record.cohorts[cohort.agent_id] = cohort
    ids = sorted(record.cohorts)
    outside = {}
    for producer_id in sorted(record.producers):
        if rng.random() < 0.4:
            outside[producer_id] = {holder: rng.uniform(0.0, 0.3) for holder in rng.sample(ids + ["outsider:1", "outsider:2"], rng.randrange(1, 4))}
    record.capital_markets = types.SimpleNamespace(capital=types.SimpleNamespace(share_price_factor=rng.uniform(0.5, 1.5)), shares=outside)
    owners = ids
    for producer_id, producer in list(record.producers.items()):
        record.producers.put(dataclasses.replace(producer, owner=rng.choice(owners)))
    return record


class ShareOut(unittest.TestCase):
    def test_every_agent_gets_the_floats_and_the_order_of_the_producer_by_producer_split(self):
        for seed in range(12):
            record = record_of(seed)
            rng = random.Random(seed)
            worths = {producer_id: rng.uniform(0.0, 500.0) for producer_id in sorted(record.producers) if rng.random() < 0.8}
            new, old = share_out(record, worths), share_out_by_producer(record, worths)
            self.assertEqual(list(new), list(old), seed)
            self.assertEqual(new, old, seed)

    def test_the_outside_holders_are_in_the_answer_and_not_all_zero(self):
        record = record_of(3)
        worths = {producer_id: 100.0 for producer_id in sorted(record.producers)}
        found = share_out(record, worths)
        self.assertTrue({"outsider:1", "outsider:2"} & set(found))
        self.assertTrue(any(value > 0.0 for value in found.values()))

    def test_no_worths_is_no_holdings(self):
        self.assertEqual(share_out(record_of(0), {}), {})


if __name__ == "__main__":
    unittest.main()
