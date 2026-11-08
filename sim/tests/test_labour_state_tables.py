"""The labour core's state held as tables answers as the nested dicts it replaced: the same entries in the same order after any
mix of writes, copies and a round trip through plain data."""

QUICK_TOPIC = True

import copy
import random
import unittest

from sim.labour.market.market_state import MarketState
from sim.labour.market.state_ids import EmployerIds, SortedIds

AREAS = ["north", "east", "south", "west"]
TRADES = ["smith", "digger", "carver", "baker"]
EMPLOYERS = ["e1", "e2", "e3", "e4", "e5"]
BANDS = 3


def model_of(state_plain):
    return copy.deepcopy(state_plain)


class SortedIdsTests(unittest.TestCase):
    def test_a_number_is_the_place_in_sorted_order_and_a_new_name_renumbers(self):
        ids = SortedIds("area", ["b", "d"])
        self.assertIsNone(ids.admit(["b"]))
        old_to_new = ids.admit(["c", "a"])
        self.assertEqual((ids.names, old_to_new.tolist()), (["a", "b", "c", "d"], [1, 3]))

    def test_employer_ranks_follow_names_whatever_the_arrival_order(self):
        employers = EmployerIds()
        employers.admit(["m", "c"])
        employers.admit(["a", "z"])
        self.assertEqual([employers.rank[employers.table.number(name)] for name in ("a", "c", "m", "z")], [0, 1, 2, 3])


class StateViewsMatchDicts(unittest.TestCase):
    def test_random_writes_leave_views_equal_to_the_dicts_written(self):
        rng = random.Random(5)
        for _case in range(30):
            state = MarketState(workers={"north": {"smith": [1.0] * BANDS}})
            model = {"workers": {"north": {"smith": [1.0] * BANDS}}, "trainees": {}, "wages": {}, "asks": {}, "hired_hours": {}}
            for _step in range(40):
                area, trade, employer = rng.choice(AREAS), rng.choice(TRADES), rng.choice(EMPLOYERS)
                kind = rng.choice(["workers", "wages", "asks", "hired", "cohort", "delete_trade", "add_to_bands", "delete_area"])
                if kind == "workers":
                    bands = [rng.uniform(0, 9) for _ in range(BANDS)]
                    state.workers.setdefault(area, {})[trade] = bands
                    model["workers"].setdefault(area, {})[trade] = list(bands)
                elif kind in ("wages", "asks"):
                    value = rng.uniform(0.5, 3)
                    getattr(state, kind).setdefault(area, {})[trade] = value
                    model[kind].setdefault(area, {})[trade] = value
                elif kind == "hired":
                    hours = rng.uniform(1, 50)
                    state.hired_hours.setdefault(area, {}).setdefault(trade, {})[employer] = hours
                    model["hired_hours"].setdefault(area, {}).setdefault(trade, {})[employer] = hours
                elif kind == "cohort":
                    cohort = [float(rng.randint(1, 4)), [rng.uniform(0, 5) for _ in range(BANDS)], rng.choice([0.0, 0.5])]
                    state.trainees.setdefault(area, {}).setdefault(trade, []).append(list(cohort))
                    model["trainees"].setdefault(area, {}).setdefault(trade, []).append(copy.deepcopy(cohort))
                elif kind == "delete_trade" and trade in model["workers"].get(area, {}):
                    del state.workers[area][trade]
                    del model["workers"][area][trade]
                elif kind == "add_to_bands" and trade in model["workers"].get(area, {}):
                    state.workers[area][trade][1] += 2.5
                    model["workers"][area][trade][1] += 2.5
                elif kind == "delete_area" and area in model["wages"]:
                    del state.wages[area]
                    del model["wages"][area]
                self.assertEqual(state.to_plain(), model)
                for name in model:
                    self.assertEqual(list(getattr(state, name)), list(model[name]), "areas are listed in the order they were named")
                    for each_area in model[name]:
                        self.assertEqual(list(getattr(state, name)[each_area]), list(model[name][each_area]))

    def test_a_copy_is_independent_and_a_plain_round_trip_keeps_the_order(self):
        state = MarketState(workers={"b": {"y": [1.0, 2.0], "x": [3.0, 4.0]}, "a": {"z": [5.0, 6.0]}},
                            wages={"b": {"y": 1.5}}, hired_hours={"b": {"y": {"q": 2.0, "p": 1.0}}})
        other = state.copy()
        other.workers["b"]["y"][:] = [9.0, 9.0]
        self.assertEqual(state.workers["b"]["y"], [1.0, 2.0])
        again = MarketState(**state.to_plain())
        self.assertEqual((list(again.workers), list(again.workers["b"]), list(again.hired_hours["b"]["y"])), (["b", "a"], ["y", "x"], ["q", "p"]))

    def test_band_lists_keep_their_length(self):
        state = MarketState(workers={"a": {"x": [1.0, 2.0]}})
        with self.assertRaises(ValueError):
            state.workers["a"]["x"][:] = [1.0]

    def test_the_hired_hours_can_be_replaced_whole(self):
        state = MarketState(hired_hours={"a": {"x": {"e": 1.0}}})
        state.hired_hours = {"b": {"y": {"f": 2.0}}}
        self.assertEqual(state.to_plain()["hired_hours"], {"b": {"y": {"f": 2.0}}})

    def test_a_view_taken_before_a_new_area_is_numbered_still_writes_the_right_pair(self):
        state = MarketState(workers={"b": {"x": [10.0, 10.0]}})
        held = state.workers["b"]["x"]
        state.workers.setdefault("a", {}).setdefault("x", [0.0, 0.0])      # "a" sorts first, so every grid row moves
        held[0] -= 4.0
        self.assertEqual((state.workers["b"]["x"], state.workers["a"]["x"]), ([6.0, 10.0], [0.0, 0.0]))

    def test_the_sum_of_a_band_view_is_the_sum_of_the_list(self):
        values = [0.1, 0.2, 0.3, 0.4, 0.7]
        state = MarketState(workers={"a": {"x": list(values)}})
        self.assertEqual(sum(state.workers["a"]["x"]), sum(values))


if __name__ == "__main__":
    unittest.main()
