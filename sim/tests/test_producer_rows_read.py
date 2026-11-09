"""`producer_rows_read.fields_of` gives, for each row, the fields of the `Producer` the store builds for it, with the same types."""
import dataclasses
import unittest

import numpy as np

from sim.economy import producer_rows_read, producers
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.economy.types import Recipe
from sim.tests.economy_view_defaults import ViewDefaults

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


class _View(ViewDefaults):
    year = 3

    def price(self, good, area):
        return {"grain": 2.0, "seed": 1.0}.get(good)

    def wage(self, trade, area):
        return 1.0

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return 0.0


class OffersTakeTheRowFields(unittest.TestCase):
    def test_offers_from_the_fields_equal_offers_from_the_record(self):
        recipe = Recipe("farm", {"grain": 10.0, "straw": 1.0}, {"seed": 2.0}, {"hand": 5.0})
        store = ProducerStore({"f1": Producer("f1", "lord", "farm", "t", 100.0, expected_prices={"grain": 2.0}, last_runs=4.0,
                                              expected_sales=4.0, cash_target=700.0, land_rent_per_run=0.5)})
        record, fields = store["f1"], producer_rows_read.fields_of(store, [0])[0]
        for shortfall in (0.0, 300.0):
            made = producers.offers(fields, recipe, _View(), {"grain": 50.0, "straw": 3.0}, shortfall, 0.05, {})
            self.assertEqual(made, producers.offers(record, recipe, _View(), {"grain": 50.0, "straw": 3.0}, shortfall, 0.05, {}))
            self.assertTrue(made)


if __name__ == "__main__":
    unittest.main()
