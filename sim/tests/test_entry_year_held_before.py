"""`entry_year._owner_and_crew_held` names, for the plans' producers the table holds, what `owner_at` and `crew_of` give; `ProducerStore.value`
is the figure `floats` gives."""
import unittest

import numpy as np

from sim.economy import entry_year
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.economy.setup import recipe_tile_key

QUICK_TOPIC = True


def _store():
    return ProducerStore({
        "producer:" + recipe_tile_key("farm", "t1"): Producer("producer:" + recipe_tile_key("farm", "t1"), "cohort:1", "farm", "t1", np.float64(4.0),
                                                              crew_runs={"hand": 2.0}),
        "producer:" + recipe_tile_key("mill", "t2"): Producer("producer:" + recipe_tile_key("mill", "t2"), "cohort:2", "mill", "t2", 1.5, workshops=3),
    })


class OwnerAndCrewHeld(unittest.TestCase):
    def test_a_producer_the_table_holds_is_listed_once_with_its_owner_and_crew(self):
        store = _store()
        plans = [("farm", "t1", 1.0, 0.1), ("mill", "t2", 2.0, 0.2), ("farm", "t1", 3.0, 0.3), ("farm", "t9", 1.0, 0.1)]
        held = entry_year._owner_and_crew_held(store, plans)
        self.assertEqual(list(held), ["producer:" + recipe_tile_key("farm", "t1"), "producer:" + recipe_tile_key("mill", "t2")])
        for producer_id, (owner, crew) in held.items():
            row = store.row_of[producer_id]
            self.assertEqual((owner, crew), (store.owner_at(row), store.crew_of(row)))

    def test_no_plans_is_an_empty_answer(self):
        self.assertEqual(entry_year._owner_and_crew_held(_store(), []), {})


class ValueIsTheFloatsFigure(unittest.TestCase):
    def test_value_equals_floats(self):
        store = _store()
        for row in (0, 1):
            for name in ("capacity_runs", "yield_factor", "workshops", "last_runs"):
                made, expected = store.value(row, name), store.floats(name, np.array([row]))[0] if name != "workshops" else store.table.workshops[row].item()
                self.assertEqual(made, expected)
                self.assertIs(type(made), type(expected))


if __name__ == "__main__":
    unittest.main()
