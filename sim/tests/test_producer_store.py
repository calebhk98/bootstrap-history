"""The producer store: a mapping of `Producer` over columns, written and read back whole."""
import json
import unittest

from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer

QUICK_TOPIC = True


def _producers():
    first = Producer("producer:b", "owner:1", "baker", "tile:1", 3.0, expected_prices={"wheat": 2.0, "flour": 3.5},
                     net_earnings_history=(1.0, 2.0), revenue_history=(5.0,), crew_runs={"smith": 4.0, "baker": 1.5},
                     staffed_runs=2.0, years_of_loss=2, idle_years=1)
    second = Producer("producer:a", "owner:2", "miller", "tile:2", 1.5, workshops=3, land_run_cap=7.0)
    return first, second


class StoreIsAMappingOfRecords(unittest.TestCase):
    def test_a_record_put_is_the_record_got(self):
        store = ProducerStore()
        for each in _producers():
            store.put(each)
        for each in _producers():
            self.assertEqual(store[each.agent_id], each)

    def test_keys_come_in_the_order_the_producers_entered(self):
        store = ProducerStore()
        for each in _producers():
            store[each.agent_id] = each
        self.assertEqual(list(store), ["producer:b", "producer:a"])

    def test_a_replaced_record_keeps_its_place_and_a_deleted_one_leaves(self):
        first, second = _producers()
        store = ProducerStore({first.agent_id: first, second.agent_id: second})
        store.put(Producer("producer:b", "owner:1", "baker", "tile:1", 9.0))
        self.assertEqual(list(store), ["producer:b", "producer:a"])
        self.assertEqual(store["producer:b"].capacity_runs, 9.0)
        self.assertEqual(store["producer:b"].expected_prices, {})
        del store["producer:b"]
        self.assertEqual(list(store), ["producer:a"])
        self.assertNotIn("producer:b", store)
        store.compact()
        self.assertEqual(store.order().tolist(), [0])
        self.assertEqual(store["producer:a"], second)

    def test_a_producer_handed_out_is_not_changed_by_a_later_write(self):
        first, _second = _producers()
        store = ProducerStore({first.agent_id: first})
        held = store[first.agent_id]
        store.put(Producer("producer:b", "owner:1", "baker", "tile:1", 8.0))
        self.assertEqual(held.capacity_runs, 3.0)
        self.assertEqual(store[first.agent_id].capacity_runs, 8.0)

    def test_the_rows_in_sorted_id_order(self):
        store = ProducerStore({each.agent_id: each for each in _producers()})
        self.assertEqual(store.order().tolist(), [1, 0])

    def test_a_long_history_widens_the_columns(self):
        store = ProducerStore()
        store.put(Producer("p", "o", "r", "t", 1.0, net_earnings_history=tuple(float(each) for each in range(9)),
                           expected_prices={name: 1.0 + position for position, name in enumerate("abcdefg")}))
        self.assertEqual(store["p"].net_earnings_history, tuple(float(each) for each in range(9)))
        self.assertEqual(len(store["p"].expected_prices), 7)


class StoreRoundTripsThroughThePlainSave(unittest.TestCase):
    def test_saved_fields_are_the_records_fields_in_id_order(self):
        store = ProducerStore({each.agent_id: each for each in _producers()})
        saved = store.to_plain()
        self.assertEqual(list(saved), ["producer:a", "producer:b"])
        self.assertEqual(list(saved["producer:b"]["net_earnings_history"]), [1.0, 2.0])
        self.assertEqual(saved["producer:a"]["land_run_cap"], 7.0)
        self.assertIsNone(saved["producer:a"]["staffed_runs"])
        self.assertEqual(json.dumps(json.loads(json.dumps(saved))), json.dumps(saved))     # it is plain JSON data

    def test_a_loaded_store_equals_the_saved_one(self):
        store = ProducerStore({each.agent_id: each for each in _producers()})
        loaded = ProducerStore.from_plain(json.loads(json.dumps(store.to_plain())))
        self.assertEqual(loaded, store)
        self.assertEqual(list(loaded), ["producer:a", "producer:b"])


class StoreWritesAndBlockReads(unittest.TestCase):
    def test_enter_makes_the_row_a_producer_starts_with(self):
        store = ProducerStore()
        store.enter("producer:n", "owner:1", "baker", "tile:1", 2.0, 5.0, 0.9, 2, {"baker": 3.0})
        self.assertEqual(store["producer:n"], Producer("producer:n", "owner:1", "baker", "tile:1", 2.0, yield_factor=0.9,
                                                       expected_sales=5.0, workshops=2, crew_runs={"baker": 3.0}))

    def test_set_fields_and_set_column_change_only_the_named_fields(self):
        first, second = _producers()
        store = ProducerStore({first.agent_id: first, second.agent_id: second})
        store.set_fields("producer:b", capacity_runs=9.0, land_run_cap=None)
        store.set_column("yield_factor", ["producer:a", "producer:gone"], [0.5, 0.7])
        self.assertEqual(store["producer:b"].capacity_runs, 9.0)
        self.assertIsNone(store["producer:b"].land_run_cap)
        self.assertEqual(store["producer:b"].expected_prices, first.expected_prices)
        self.assertEqual(store["producer:a"].yield_factor, 0.5)

    def test_crews_are_grouped_by_recipe_in_id_order_or_entry_order(self):
        first, second = _producers()
        store = ProducerStore({first.agent_id: first, second.agent_id: second})
        store.put(Producer("producer:c", "o", "baker", "t", 1.0, crew_runs={"smith": 1.0}))
        by_id = store.crews_by_recipe()
        self.assertEqual(by_id["baker"], [first.crew_runs, {"smith": 1.0}])
        del store["producer:b"]
        self.assertEqual(store.crews_by_recipe(in_id_order=False), {"miller": [{}], "baker": [{"smith": 1.0}]})

    def test_a_reseat_puts_the_rows_in_id_order_and_a_clear_keeps_the_counters_going(self):
        first, second = _producers()
        store = ProducerStore({first.agent_id: first, second.agent_id: second})
        store.seat_sorted()
        self.assertEqual(list(store), ["producer:a", "producer:b"])
        self.assertEqual(store["producer:b"], first)
        before = store.version
        store.clear()
        self.assertGreater(store.version, before)
        self.assertEqual(len(store), 0)

    def test_the_exact_total_and_the_tiles_leave_out_a_producer_that_exited(self):
        first, second = _producers()
        store = ProducerStore({first.agent_id: first, second.agent_id: second})
        del store["producer:a"]
        self.assertEqual(store.exact_total("capacity_runs"), 3.0)
        self.assertEqual(store.tiles_in_use(), ["tile:1"])
        self.assertEqual(store.ids_on_tiles(lambda tile: tile == "tile:1"), ["producer:b"])


class NumpyFloatsComeBackAsNumpyFloats(unittest.TestCase):
    def test_a_field_written_as_a_numpy_float_is_handed_back_as_one_and_a_python_float_as_a_python_float(self):
        import numpy as np
        store = ProducerStore({"p": Producer("p", "o", "r", "t", np.float64(3.0), expected_sales=2.0)})
        self.assertIsInstance(store["p"].capacity_runs, np.float64)
        self.assertIs(type(store["p"].expected_sales), float)
        store.set_fields("p", capacity_runs=4.0, expected_sales=np.float64(5.0))
        self.assertIs(type(store["p"].capacity_runs), float)
        self.assertIsInstance(store["p"].expected_sales, np.float64)
        self.assertIsInstance(store.value(0, "expected_sales"), np.float64)


if __name__ == "__main__":
    unittest.main()
