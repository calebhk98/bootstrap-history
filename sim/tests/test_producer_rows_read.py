"""`producer_rows_read.fields_of` gives, for each row, the fields of the `Producer` the store builds for it, with the same types."""
import dataclasses
import unittest

import numpy as np

from sim.economy import producer_rows_read
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer

QUICK_TOPIC = True


def _store():
    return ProducerStore({
        "producer:b": Producer("producer:b", "owner:1", "baker", "tile:1", np.float64(3.0), expected_prices={"wheat": 2.0, "flour": 3.5},
                               net_earnings_history=(1.0, 2.0), revenue_history=(5.0,), crew_runs={"smith": 4.0, "baker": 1.5},
                               staffed_runs=np.float64(2.0), years_of_loss=2, idle_years=1, land_run_cap=7.5),
        "producer:a": Producer("producer:a", "owner:2", "miller", "tile:2", 1.5, workshops=3, last_runs=0.25, cash_target=9.0),
        "producer:c": Producer("producer:c", "owner:1", "miller", "tile:1", 2.5, yield_factor=np.float64(0.8),
                               net_earnings_history=(3.0, 4.0, 5.0), expected_prices={"flour": 1.25}),
    })


class FieldsOf(unittest.TestCase):
    def test_every_field_equals_the_built_record_and_has_its_type(self):
        store = _store()
        rows = [2, 0, 1]
        for fields, row in zip(producer_rows_read.fields_of(store, rows), rows):
            record = store.at(row)
            for field in dataclasses.fields(Producer):
                mine, theirs = getattr(fields, field.name), getattr(record, field.name)
                self.assertEqual(mine, theirs, field.name)
                self.assertIs(type(mine), type(theirs), field.name)

    def test_the_names_are_those_of_a_producer(self):
        self.assertEqual(producer_rows_read.ProducerFields._fields, tuple(field.name for field in dataclasses.fields(Producer)))

    def test_no_rows_is_an_empty_answer(self):
        self.assertEqual(producer_rows_read.fields_of(_store(), []), [])


if __name__ == "__main__":
    unittest.main()
