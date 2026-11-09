"""The cohort store: a mapping of `Cohort` over columns, written and read back whole, and its block reads and writes."""
import json
import unittest

import numpy as np

from sim.economy.cohort_store import CohortStore, typed_flags
from sim.economy.households_cohort import Cohort

QUICK_TOPIC = True


def _cohorts():
    first = Cohort("household:b:1", "tile:b", 1, 30.0, 12.0, 0.6, expected_inflation=0.02, cash_target=5.0, share_wealth=7.5,
                   unmet_floor_by_need={"hunger": 2.0, "warmth": 0.5}, own_plan_by_need={"hunger": 1.0}, milled_grains=("wheat", "rye"))
    second = Cohort("household:a:0", "tile:a", 0, 10.0, 4.0, 0.4, hired_work_per_person=3.0)
    return first, second


class StoreIsAMappingOfRecords(unittest.TestCase):
    def test_a_record_put_is_the_record_got(self):
        store = CohortStore()
        for each in _cohorts():
            store.put(each)
        for each in _cohorts():
            self.assertEqual(store[each.agent_id], each)

    def test_keys_come_in_the_order_the_cohorts_entered_and_ids_sort_apart(self):
        store = CohortStore({each.agent_id: each for each in _cohorts()})
        self.assertEqual(list(store), ["household:b:1", "household:a:0"])
        self.assertEqual(store.order().tolist(), [1, 0])

    def test_a_cohort_handed_out_is_not_changed_by_a_later_write(self):
        first, _second = _cohorts()
        store = CohortStore({first.agent_id: first})
        held = store[first.agent_id]
        store.set_fields(first.agent_id, people=99.0)
        self.assertEqual(held.people, 30.0)
        self.assertEqual(store[first.agent_id].people, 99.0)

    def test_a_field_that_may_be_none_reads_back_none(self):
        _first, second = _cohorts()
        store = CohortStore({second.agent_id: second})
        self.assertIsNone(store[second.agent_id].share_wealth)
        store.set_fields(second.agent_id, share_wealth=4.0)
        self.assertEqual(store[second.agent_id].share_wealth, 4.0)

    def test_a_numpy_float_reads_back_as_one_and_a_python_float_as_one(self):
        first, _second = _cohorts()
        store = CohortStore({first.agent_id: first})
        store.set_fields(first.agent_id, people=np.float64(5.0), working_people=6.0)
        record = store[first.agent_id]
        self.assertIsInstance(record.people, np.floating)
        self.assertIs(type(record.working_people), float)

    def test_numpy_values_in_the_mappings_stay_numpy(self):
        first, _second = _cohorts()
        store = CohortStore({first.agent_id: first})
        store.set_fields(first.agent_id, unmet_floor_by_need={"hunger": np.float64(2.5), "warmth": 1.0})
        record = store[first.agent_id]
        self.assertIsInstance(record.unmet_floor_by_need["hunger"], np.floating)
        self.assertIs(type(record.unmet_floor_by_need["warmth"]), float)

    def test_the_mappings_and_the_grains_come_back_in_the_order_written(self):
        first, _second = _cohorts()
        store = CohortStore({first.agent_id: first})
        record = store[first.agent_id]
        self.assertEqual(list(record.unmet_floor_by_need), ["hunger", "warmth"])
        self.assertEqual(record.milled_grains, ("wheat", "rye"))

    def test_a_long_mapping_widens_the_columns(self):
        first, _second = _cohorts()
        store = CohortStore({first.agent_id: first})
        wide = {"need%d" % each: float(each) for each in range(9)}
        store.set_fields(first.agent_id, own_plan_by_need=wide)
        self.assertEqual(store[first.agent_id].own_plan_by_need, wide)

    def test_a_deleted_cohort_leaves_the_others_in_place(self):
        first, second = _cohorts()
        store = CohortStore({first.agent_id: first, second.agent_id: second})
        del store[first.agent_id]
        self.assertEqual(list(store), [second.agent_id])
        self.assertEqual(store[second.agent_id], second)

    def test_the_save_is_plain_data_in_id_order_and_reads_back_whole(self):
        store = CohortStore({each.agent_id: each for each in _cohorts()})
        plain = store.to_plain()
        self.assertEqual(list(plain), ["household:a:0", "household:b:1"])
        again = CohortStore.from_plain(json.loads(json.dumps(plain)))
        for each in _cohorts():
            self.assertEqual(again[each.agent_id], each)

    def test_seat_sorted_puts_the_rows_in_id_order(self):
        store = CohortStore({each.agent_id: each for each in _cohorts()})
        store.seat_sorted()
        self.assertEqual(list(store), ["household:a:0", "household:b:1"])
        self.assertEqual(store.order().tolist(), [0, 1])


class BlockReadsAndWrites(unittest.TestCase):
    def test_set_rows_writes_a_column_and_drops_the_snapshots_of_those_rows(self):
        first, second = _cohorts()
        store = CohortStore({first.agent_id: first, second.agent_id: second})
        held = store[second.agent_id]
        store.set_rows("planned_spending", np.array([1]), np.array([12.5]))
        self.assertEqual(store[second.agent_id].planned_spending, 12.5)
        self.assertEqual(held.planned_spending, 0.0)
        self.assertEqual(store[first.agent_id].planned_spending, 0.0)

    def test_set_column_skips_an_id_the_table_lacks(self):
        first, _second = _cohorts()
        store = CohortStore({first.agent_id: first})
        store.set_column("cash_target", ["household:b:1", "nobody"], [3.0, 4.0])
        self.assertEqual(store[first.agent_id].cash_target, 3.0)

    def test_write_pairs_gives_each_row_its_own_mapping(self):
        first, second = _cohorts()
        store = CohortStore({first.agent_id: first, second.agent_id: second})
        store.write_pairs("unmet", np.array([0, 1]), [{}, {"hunger": 4.0, "warmth": 1.0}])
        self.assertEqual(store[first.agent_id].unmet_floor_by_need, {})
        self.assertEqual(store[second.agent_id].unmet_floor_by_need, {"hunger": 4.0, "warmth": 1.0})

    def test_write_milled_gives_each_row_its_grains(self):
        first, second = _cohorts()
        store = CohortStore({first.agent_id: first, second.agent_id: second})
        store.write_milled(np.array([0, 1]), [(), ("barley",)])
        self.assertEqual(store[first.agent_id].milled_grains, ())
        self.assertEqual(store[second.agent_id].milled_grains, ("barley",))

    def test_unmet_of_reads_one_need_for_every_row(self):
        store = CohortStore({each.agent_id: each for each in _cohorts()})
        self.assertEqual(store.unmet_of("hunger").tolist(), [2.0, 0.0])
        self.assertEqual(store.unmet_of("nothing").tolist(), [0.0, 0.0])

    def test_exact_total_and_tiles_present_and_ids_on_tiles(self):
        store = CohortStore({each.agent_id: each for each in _cohorts()})
        self.assertEqual(store.exact_total("people"), 40.0)
        self.assertEqual(store.tiles_present(), ["tile:b", "tile:a"])
        self.assertEqual(store.ids_on_tiles(lambda tile: tile == "tile:a"), ["household:a:0"])

    def test_floats_hands_back_a_numpy_float_where_one_was_written(self):
        first, second = _cohorts()
        store = CohortStore({first.agent_id: first, second.agent_id: second})
        store.set_fields(second.agent_id, people=np.float64(2.0))
        values = store.floats("people", np.array([0, 1]))
        self.assertIs(type(values[0]), float)
        self.assertIsInstance(values[1], np.floating)

    def test_typed_flags_mark_only_numpy_floats(self):
        self.assertEqual(typed_flags([1.0, np.float64(2.0), None]).tolist(), [False, True, False])
        self.assertEqual(typed_flags([1.0, 2.0]).tolist(), [False, False])


if __name__ == "__main__":
    unittest.main()
