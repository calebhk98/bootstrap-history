"""The spin-up's workforce trim also cuts the trainee pipeline of a glutted trade (Complaint 467): trainees
already enrolled would graduate into the trade the trim just thinned and bring it back to a glut."""
QUICK_TOPIC = True

import unittest

from sim.economy import workforce_settle
from sim.labour.market.records import MarketState

HOURS_PER_YEAR = 100.0


def _state(workers, trainees):
    state = MarketState()
    state.workers = {"area": workers}
    state.trainees = {"area": trainees}
    return state


def _people(state, trade):
    return sum(state.workers["area"].get(trade, [0.0]))


def _in_training(state, trade):
    return sum(sum(cohort[1]) for cohort in state.trainees["area"].get(trade, []))


class TraineeTrimTests(unittest.TestCase):
    def test_trainees_beyond_the_hours_wanted_join_the_fallback_trade(self):
        state = _state({"smith": [10.0, 10.0], "labourer": [100.0, 100.0]},
                       {"smith": [[2.0, [10.0, 10.0]], [1.0, [5.0, 5.0]]]})
        wanted = {("area", "smith"): 25 * HOURS_PER_YEAR}   # room for 25 people in all
        before = _people(state, "smith") + _in_training(state, "smith") + _people(state, "labourer")
        workforce_settle.trim_people(state, wanted, "labourer", HOURS_PER_YEAR)
        self.assertLessEqual(_people(state, "smith") + _in_training(state, "smith"), 25.0 + 1e-9)
        after = _people(state, "smith") + _in_training(state, "smith") + _people(state, "labourer")
        self.assertAlmostEqual(before, after)

    def test_a_trade_short_of_people_keeps_all_its_trainees(self):
        state = _state({"smith": [5.0, 5.0], "labourer": [100.0, 100.0]}, {"smith": [[2.0, [3.0, 3.0]]]})
        workforce_settle.trim_people(state, {("area", "smith"): 50 * HOURS_PER_YEAR}, "labourer", HOURS_PER_YEAR)
        self.assertAlmostEqual(_in_training(state, "smith"), 6.0)
        self.assertAlmostEqual(_people(state, "smith"), 10.0)


if __name__ == "__main__":
    unittest.main()
