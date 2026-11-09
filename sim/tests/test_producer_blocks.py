"""Block reads of the producer table against the one-at-a-time reads they replace."""
import unittest

import numpy as np

from sim.economy import producer_blocks, producers
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.economy.types import Recipe

QUICK_TOPIC = True


def _store():
    return ProducerStore({
        "producer:b": Producer("producer:b", "owner:1", "baker", "tile:1", 3.0, expected_prices={"wheat": 2.0, "flour": 3.5},
                               yield_factor=np.float64(0.9)),
        "producer:a": Producer("producer:a", "owner:2", "miller", "tile:2", 1.5, workshops=3),
        "producer:c": Producer("producer:c", "owner:1", "miller", "tile:1", 2.5, expected_prices={"flour": 1.25}),
    })


class NameReads(unittest.TestCase):
    def test_tiles_of_matches_tile_of_and_gives_none_for_a_stranger(self):
        store = _store()
        ids = ["producer:c", "stranger", "producer:a", "producer:b"]
        self.assertEqual(producer_blocks.tiles_of(store, ids), [store.tile_of(each) for each in ids])
        self.assertIsNone(producer_blocks.tiles_of(store, ["stranger"])[0])

    def test_recipes_of_matches_recipe_id_of(self):
        store = _store()
        ids = ["producer:b", "stranger", "producer:c"]
        self.assertEqual(producer_blocks.recipes_of(store, ids), [store.recipe_id_of(each) for each in ids])

    def test_no_ids_is_an_empty_answer(self):
        self.assertEqual(producer_blocks.tiles_of(_store(), []), [])

    def test_owners_at_matches_owner_at(self):
        store = _store()
        rows = np.array([2, 0, 1], dtype=np.int64)
        self.assertEqual(producer_blocks.owners_at(store, rows), [store.owner_at(row) for row in rows.tolist()])


class FigureReads(unittest.TestCase):
    def test_crews_of_matches_crew_of_and_is_empty_for_no_crew(self):
        store = _store()
        store.write_crew(store.row_of["producer:b"], {"smith": 4.0, "baker": 1.5})
        store.write_crew(store.row_of["producer:c"], {"miller": 0.5})
        rows = [2, 1, 0]
        self.assertEqual(producer_blocks.crews_of(store, rows), [store.crew_of(row) for row in rows])
        self.assertEqual(producer_blocks.crews_of(store, rows)[1], {})
        self.assertEqual(list(producer_blocks.crews_of(store, [0])[0]), ["smith", "baker"])

    def test_expected_prices_of_matches_the_records_in_written_order(self):
        store = _store()
        ids = ("producer:c", "producer:a", "producer:b")
        answer = producer_blocks.expected_prices_of(store, [store.row_of[each] for each in ids])
        self.assertEqual(answer, [store[each].expected_prices for each in ids])
        self.assertEqual(list(answer[2]), ["wheat", "flour"])

    def test_figures_of_keeps_the_numpy_type_of_a_field_written_as_one(self):
        store = _store()
        rows = [store.row_of["producer:b"], store.row_of["producer:a"]]
        figures = producer_blocks.figures_of(store, "yield_factor", rows)
        self.assertIsInstance(figures[0], np.float64)
        self.assertIs(type(figures[1]), float)
        self.assertEqual(figures, [store["producer:b"].yield_factor, store["producer:a"].yield_factor])


class RowFiguresTests(unittest.TestCase):
    def test_row_figures_match_the_record_of_each_row(self):
        store = _store()
        rows = [2, 0, 1]
        for figures, row in zip(producer_blocks.row_figures(store, rows), rows):
            record = store.at(row)
            self.assertEqual(figures, producer_blocks.RowFigures(record.agent_id, record.tile, record.recipe_id, record.yield_factor,
                                                                 record.expected_prices))

    def test_figures_by_id_leaves_out_a_stranger_and_keeps_the_order_given(self):
        found = producer_blocks.figures_by_id(_store(), ["producer:c", "stranger", "producer:a"])
        self.assertEqual(list(found), ["producer:c", "producer:a"])
        self.assertEqual(found["producer:a"].tile, "tile:2")


class _OfferedView:
    def offered_prices_for(self, tile, goods):
        return {good: {"flour": 4.0}.get(good) for good in goods}


class ExpectedOutputPricesAt(unittest.TestCase):
    def test_equal_to_the_producer_form(self):
        recipe = Recipe("baker", {"flour": 1.0, "bread": 2.0, "bran": 1.0}, {}, {})
        producer = Producer("p", "o", "baker", "tile:1", 1.0, expected_prices={"bread": 7.0})
        view = _OfferedView()
        self.assertEqual(producers.expected_output_prices_at(producer.expected_prices, producer.tile, recipe, view),
                         producers.expected_output_prices(producer, recipe, view))
        self.assertEqual(producers.expected_output_prices_at({"bread": 7.0}, "tile:1", recipe, view), {"flour": 4.0, "bread": 7.0})


if __name__ == "__main__":
    unittest.main()
