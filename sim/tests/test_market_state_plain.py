"""`MarketState.to_plain` (read a column at a time) gives what the dict views give, pair by pair."""

QUICK_TOPIC = True

import json
import random
import unittest

from sim.labour.market.market_state import MarketState
from sim.tests.market_plain_reference import plain_state


def _written_out_state():
    return MarketState(
        workers={"vale": {"digger": [5.0, 3.0, 1.0], "reaper": [2.0, 0.0, 0.0]}, "ash": {"smith": [1.5, 2.5, 0.5]}},
        trainees={"vale": {"digger": [[2.0, [1.0, 2.0, 0.0], 0.1], [1.0, [0.5, 0.5, 0.5], 0.0]]}},
        wages={"vale": {"reaper": 3.25, "digger": 4.5}}, asks={"ash": {"smith": 1.2}},
        hired_hours={"vale": {"digger": {"zed": 10.0, "abe": 5.5}, "reaper": {}}, "ash": {}})


def _random_state(generator):
    areas = ["area%d" % number for number in range(generator.randint(1, 5))]
    trades = ["trade%d" % number for number in range(generator.randint(1, 5))]
    employers = ["emp%d" % number for number in range(6)]
    state = MarketState(workers={areas[0]: {trades[0]: [1.0, 2.0, 3.0]}})
    for _ in range(generator.randint(5, 40)):
        area, trade = generator.choice(areas), generator.choice(trades)
        kind = generator.choice(["workers", "trainees", "wages", "asks", "hired_hours", "drop"])
        view = getattr(state, kind if kind != "drop" else "wages")
        if kind == "drop":
            if area in view and trade in view[area]:
                del view[area][trade]
            continue
        value = {"workers": lambda: [generator.random() for _ in range(3)],
                 "trainees": lambda: [[generator.random(), [generator.random() for _ in range(3)], generator.random()]
                                      for _ in range(generator.randint(1, 3))],
                 "wages": generator.random, "asks": generator.random,
                 "hired_hours": lambda: {name: generator.random() * 100 for name in generator.sample(employers, generator.randint(0, 4))}}[kind]()
        view.setdefault(area, {})[trade] = value
    return state


class PlainStateTests(unittest.TestCase):
    def test_written_out_state(self):
        state = _written_out_state()
        plain = state.to_plain()
        self.assertEqual(plain, plain_state(state))
        self.assertEqual(json.dumps(plain), json.dumps(plain_state(state)))
        self.assertEqual(plain["hired_hours"]["vale"]["digger"], {"zed": 10.0, "abe": 5.5})

    def test_empty_state(self):
        state = MarketState()
        self.assertEqual(json.dumps(state.to_plain()), json.dumps(plain_state(state)))

    def test_random_states_keep_values_and_key_order(self):
        for seed in range(60):
            state = _random_state(random.Random(seed))
            self.assertEqual(json.dumps(state.to_plain()), json.dumps(plain_state(state)), seed)

    def test_result_does_not_share_lists_with_the_tables(self):
        state = _written_out_state()
        state.to_plain()["workers"]["vale"]["digger"][0] = 99.0
        self.assertEqual(state.to_plain()["workers"]["vale"]["digger"][0], 5.0)


if __name__ == "__main__":
    unittest.main()
