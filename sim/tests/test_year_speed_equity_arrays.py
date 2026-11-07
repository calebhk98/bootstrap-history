"""Numba port items 0b and 6: the producers' net worths (`year_arrays_worths.worths_from_arrays`), the restake of owners
(`entry_year.restake_owners` over the year arrays) and the arrays carried from one year to the next (`YearArrays.carried`) give what
the plain Python they stand in for gives, on random built economies (no game). The old per-producer worth and the old
producer-by-producer restake are the references; each test calls one function beside its old one.

Tolerance: a relative 1e-9. The kernels add a producer's goods in sorted order where the old code summed in dictionary order or with
math.fsum, so the last digits differ. A restake is a discrete rule (a run pays when its return after recovery beats the rate): an
economy with a producer whose old return is within the tolerance of the rate is left out of the comparison, and most economies must
be compared."""

QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy import entry_year, equity, producer_table, producers as producer_rules, unit_cost
from sim.economy.market_memory import note_written
from sim.economy.rates import own_rate
from sim.economy.replaced import replaced
from sim.economy.types import EDGE_MINT, Transfer
from sim.economy.year_arrays import YearArrays, same_source, source_of
from sim.economy.year_arrays_worths import worths_from_arrays
from sim.tests.test_year_speed_equity import close, old_producer_worths
from sim.tests.year_close_fixture import MONEY, economy_of


def economy(seed, producer_count=60):
    setup, record, view, _ledger, area_map = economy_of(seed, producer_count=producer_count)
    return setup, record, view, area_map


class WorthsFromArrays(unittest.TestCase):
    def test_worths_equal_the_per_producer_reads(self):
        compared = 0
        for seed in range(12):
            setup, record, view, area_map = economy(seed)
            arrays = YearArrays.build(setup, record, area_map, view)
            new, old = worths_from_arrays(setup, record, view, arrays), old_producer_worths(setup, record, view)
            self.assertEqual(sorted(new), sorted(old))
            for producer_id, worth in old.items():
                self.assertTrue(close(new[producer_id], worth), (producer_id, new[producer_id], worth))
                compared += 1
        self.assertGreater(compared, 500)

    def test_worths_follow_a_memory_written_after_the_arrays_were_read(self):
        setup, record, view, area_map = economy(3)
        arrays = YearArrays.build(setup, record, area_map, view)
        for key in list(record.memory.prices)[:6]:
            record.memory.prices[key] *= 1.7
        note_written()
        new, old = worths_from_arrays(setup, record, view, arrays), old_producer_worths(setup, record, view)
        self.assertEqual(sorted(new), sorted(old))
        for producer_id, worth in old.items():
            self.assertTrue(close(new[producer_id], worth), (producer_id, new[producer_id], worth))

    def test_a_producer_whose_owner_is_no_cohort_or_without_capacity_has_no_worth(self):
        setup, record, view, area_map = economy(2)
        arrays = YearArrays.build(setup, record, area_map, view)
        first, second = sorted(record.producers)[:2]
        producer_table.put_producer(record.producers, replaced(record.producers[first], owner="nobody"))
        producer_table.put_producer(record.producers, replaced(record.producers[second], capacity_runs=0.0))
        new = worths_from_arrays(setup, record, view, arrays)
        self.assertNotIn(first, new)
        self.assertNotIn(second, new)
        self.assertEqual(sorted(new), sorted(old_producer_worths(setup, record, view)))

    def test_no_producers_is_no_worth(self):
        setup, record, view, area_map = economy(0)
        arrays = YearArrays.build(setup, record, area_map, view)
        record.producers = {}
        self.assertEqual(worths_from_arrays(setup, record, view, arrays), {})

    def test_equity_builds_the_same_worths_over_the_arrays_and_without(self):
        setup, record, view, area_map = economy(4)
        arrays = YearArrays.build(setup, record, area_map, view)
        over, without = equity.producer_worths(setup, record, view, arrays), equity.producer_worths(setup, record, view)
        self.assertEqual(sorted(over), sorted(without))
        for producer_id, worth in without.items():
            self.assertTrue(close(over[producer_id], worth))


def short_of_cash(seed):
    """An economy whose producers have working-cash targets above their cash, so owners are asked to restake."""
    setup, record, view, area_map = economy(seed, producer_count=80)
    for cohort_id in sorted(record.cohorts):
        record.book.transfer(Transfer(EDGE_MINT, cohort_id, MONEY, 40.0 * (1 + len(cohort_id)), "seed"))
    for index, producer_id in enumerate(sorted(record.producers)):
        producer = record.producers[producer_id]
        target = record.book.balance(producer_id, MONEY) + (30.0 + index if index % 4 else -5.0)
        producer_table.put_producer(record.producers, replaced(producer, cash_target=target))
    return setup, record, view, area_map


def stakes(setup, record, view, arrays):
    """The transfers `restake_owners` makes, in order."""
    made = []
    original = record.book.transfer

    def recording(transfer):
        made.append((transfer.payer, transfer.payee, transfer.amount))
        original(transfer)
    record.book.transfer = recording
    entry_year.restake_owners(setup, record, view, arrays)
    return made


def old_return_is_near_the_rate(setup, record, view, producer_id, tolerance=1e-9):
    producer = record.producers[producer_id]
    recipe = setup.recipes[producer.recipe_id]
    rate = own_rate(view, MONEY)
    earning = unit_cost.return_after_recovery(
        recipe, producer_rules.expected_output_prices(producer, recipe, view) or {},
        producer_rules.live_input_prices(producer, recipe, view), producer_rules.live_wages(producer, recipe, view), rate,
        producer.land_rent_per_run)
    return earning is not None and abs(earning - rate) <= tolerance * max(1.0, abs(rate))


class RestakeOverArrays(unittest.TestCase):
    def test_the_stakes_equal_the_producer_by_producer_stakes(self):
        compared = made_any = 0
        for seed in range(10):
            setup, record, view, area_map = short_of_cash(seed)
            other_setup, other_record, other_view, _map = short_of_cash(seed)
            if any(old_return_is_near_the_rate(setup, record, view, each) for each in record.producers):
                continue          # a discrete rule: a one-ulp nudge of a return at the rate could flip it
            new = stakes(setup, record, view, YearArrays.build(setup, record, area_map, view))
            old = stakes(other_setup, other_record, other_view, None)
            self.assertEqual([each[:2] for each in new], [each[:2] for each in old])
            for (_payer, _payee, amount), (_other_payer, _other_payee, wanted) in zip(new, old):
                self.assertTrue(close(amount, wanted), (amount, wanted))
            compared += 1
            made_any += bool(old)
        self.assertGreaterEqual(compared, 7)
        self.assertGreaterEqual(made_any, 5)

    def test_an_owner_never_stakes_more_than_its_cash(self):
        setup, record, view, area_map = short_of_cash(1)
        made = stakes(setup, record, view, YearArrays.build(setup, record, area_map, view))
        self.assertTrue(made)
        for payer in {each[0] for each in made}:
            self.assertGreaterEqual(record.book.balance(payer, MONEY), 0.0)

    def test_no_producer_short_of_cash_is_no_transfer(self):
        setup, record, view, area_map = economy(5)
        for producer in list(record.producers.values()):
            producer_table.put_producer(record.producers, replaced(producer, cash_target=0.0))
        self.assertEqual(stakes(setup, record, view, YearArrays.build(setup, record, area_map, view)), [])

    def test_no_producers_is_no_transfer(self):
        setup, record, view, area_map = economy(6)
        arrays = YearArrays.build(setup, record, area_map, view)
        record.producers = {}
        self.assertEqual(stakes(setup, record, view, arrays), [])


class ArraysCarriedOverTheYear(unittest.TestCase):
    def test_carried_arrays_equal_arrays_built_now(self):
        for seed in range(5):
            setup, record, view, area_map = economy(seed)
            previous = YearArrays.build(setup, record, area_map, view)
            ids = sorted(record.producers)
            for index, producer_id in enumerate(ids[:15]):
                producer = record.producers[producer_id]
                producer_table.put_producer(record.producers, replaced(producer, capacity_runs=producer.capacity_runs + index,
                                                                       expected_sales=producer.expected_sales + 1.0))
            producer_table.put_producer(record.producers, replaced(record.producers[ids[20]], tile="T2"))
            del record.producers[ids[30]]
            for key in list(record.memory.prices)[:5]:
                record.memory.prices[key] += 0.5
            note_written()
            carried = YearArrays.carried(previous, setup, record, area_map, view)
            built = YearArrays.build(setup, record, area_map, view)
            self.assertIs(carried.matrices, previous.matrices)
            self.assertEqual(carried.producers.ids, built.producers.ids)
            for name in ("recipe_row", "tile_row", "capacity_runs", "expected_sales", "cash_target", "last_runs", "idle_years",
                         "history_count"):
                np.testing.assert_array_equal(getattr(carried.producers, name), getattr(built.producers, name), name)
            np.testing.assert_array_equal(carried.producers.expected_prices, built.producers.expected_prices)
            np.testing.assert_array_equal(carried.memory.price, built.memory.price)
            np.testing.assert_array_equal(carried.memory.wage, built.memory.wage)

    def test_arrays_of_other_recipes_or_another_area_map_are_not_carried(self):
        setup, record, view, area_map = economy(1)
        previous = YearArrays.build(setup, record, area_map, view)
        self.assertIs(YearArrays.carried(previous, setup, record, area_map, view).matrices, previous.matrices)
        self.assertIsNot(YearArrays.carried(previous, setup, record, type(area_map)(), view).matrices, previous.matrices)
        setup.recipes = dict(setup.recipes)
        setup.recipes["recipe0"] = replaced(setup.recipes["recipe0"], plant_life_years=99.0)
        self.assertIsNot(YearArrays.carried(previous, setup, record, area_map, view).matrices, previous.matrices)
        self.assertIsNot(YearArrays.carried(None, setup, record, area_map, view), None)

    def test_the_same_source_is_the_same_records_under_the_same_names(self):
        setup, _record, _view, _area_map = economy(0)
        first = source_of(setup)
        self.assertTrue(same_source(first, source_of(setup)))
        setup.specs = dict(setup.specs)
        self.assertTrue(same_source(first, source_of(setup)))      # a copied dict of the same specs
        setup.specs["good0"] = replaced(setup.specs["good0"], service_life_years=7.0)
        self.assertFalse(same_source(first, source_of(setup)))
        setup.specs.pop("good0")
        self.assertFalse(same_source(first, source_of(setup)))


if __name__ == "__main__":
    unittest.main()
