"""An input shortage cuts a recipe's runs by the share it is short, not to zero (Leontief)."""
QUICK_TOPIC = True

import unittest

from sim.economy import producers, tool_fallback
from sim.economy.types import Recipe, ToolFallback

PRESS = Recipe("press", {"oil": 1.0}, {"olive": 4.0, "sack": 2.0}, {"hand": 3.0})
FORGE = Recipe("forge", {"nail": 1.0}, {"iron": 1.0, "hammer": 0.5}, {"smith": 2.0}, tool_wear={"hammer": 0.5},
               tool_fallbacks={"hammer": (ToolFallback("", 0.0, 1.5, ("smith",)),)})


def worker(recipe_id, **changes):
    base = dict(agent_id="p", owner="o", recipe_id=recipe_id, tile="t", capacity_runs=10.0)
    base.update(changes)
    return producers.Producer(**base)


class InputShortageTests(unittest.TestCase):
    def test_one_input_at_half_the_need_gives_half_the_runs(self):
        achieved, _moves = producers.produce(worker("press"), PRESS, {"olive": 20.0, "sack": 20.0}, {"hand": 30.0}, 10.0)
        self.assertAlmostEqual(achieved, 5.0)

    def test_two_inputs_short_take_the_smaller_share(self):
        achieved, _moves = producers.produce(worker("press"), PRESS, {"olive": 20.0, "sack": 8.0}, {"hand": 30.0}, 10.0)
        self.assertAlmostEqual(achieved, 4.0)

    def test_nothing_short_works_the_plan(self):
        achieved, _moves = producers.produce(worker("press"), PRESS, {"olive": 40.0, "sack": 20.0}, {"hand": 30.0}, 10.0)
        self.assertAlmostEqual(achieved, 10.0)

    def test_hours_at_half_the_need_give_half_the_runs(self):
        achieved, _moves = producers.produce(worker("press"), PRESS, {"olive": 40.0, "sack": 20.0}, {"hand": 15.0}, 10.0)
        self.assertAlmostEqual(achieved, 5.0)

    def test_only_what_the_runs_worked_need_is_used_up(self):
        _achieved, moves = producers.produce(worker("press"), PRESS, {"olive": 20.0, "sack": 20.0}, {"hand": 30.0}, 10.0)
        used = {move.good: move.quantity for move in moves if move.good in PRESS.inputs}
        self.assertAlmostEqual(used["olive"], 20.0)
        self.assertAlmostEqual(used["sack"], 10.0)


class ToolFallbackTests(unittest.TestCase):
    def test_a_missing_tool_takes_the_by_hand_hours(self):
        used, extra = tool_fallback.draws(FORGE, {}, 4.0)
        self.assertEqual(used, {})
        self.assertAlmostEqual(extra["smith"], 4.0 * 0.5 * 2.0)

    def test_a_missing_tool_cuts_runs_only_to_what_the_stretched_hours_allow(self):
        achieved, _moves = producers.produce(worker("forge"), FORGE, {"iron": 10.0}, {"smith": 6.0}, 10.0)
        self.assertAlmostEqual(achieved, 6.0 / 3.0)

if __name__ == "__main__":
    unittest.main()
