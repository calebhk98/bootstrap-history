"""`land_market._write_land_figures` leaves the producer table as `set_fields` on each producer does, numpy-float types included."""
import unittest

import numpy as np

from sim.economy import land_market, producer_table
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer

QUICK_TOPIC = True


def _store():
    return ProducerStore({each: Producer(each, "o", "farm", "t", 1.0, land_run_cap=5.0 if each == "p2" else None)
                          for each in ("p1", "p2", "p3")})


class WriteLandFigures(unittest.TestCase):
    def test_equal_to_set_fields_producer_by_producer(self):
        rents = [np.float64(0.5), 0.75, np.float64(1.25)]
        caps = [None, np.float64(2.0), 3.5]
        block, one_by_one = _store(), _store()
        land_market._write_land_figures(block, np.array([2, 0, 1], dtype=np.int64), rents, caps)
        for row, rent, cap in zip([2, 0, 1], rents, caps):
            producer_table.set_fields(one_by_one, one_by_one.ids[row], land_rent_per_run=rent, land_run_cap=cap)
        for each in ("p1", "p2", "p3"):
            made, expected = block[each], one_by_one[each]
            self.assertEqual(made, expected)
            self.assertIs(type(made.land_rent_per_run), type(expected.land_rent_per_run))
            self.assertIs(type(made.land_run_cap), type(expected.land_run_cap))

    def test_a_cap_taken_away_is_none_again(self):
        store = _store()
        land_market._write_land_figures(store, np.array([1], dtype=np.int64), [0.1], [None])
        self.assertIsNone(store["p2"].land_run_cap)


if __name__ == "__main__":
    unittest.main()
