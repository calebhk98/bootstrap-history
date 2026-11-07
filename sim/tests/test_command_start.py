"""What a one-command process does to start and leave cheaply: the lazy kernel stand-in, the choice between the plain
route search and the kernel, and the game-process checks of `sim/ui/process_start.py`."""

QUICK_TOPIC = True

import gc
import unittest
from unittest import mock

import numpy

from sim import jit
from sim.geography import routes_search
from sim.ui import process_start


def _total(values):
    total = 0.0
    for index in range(values.shape[0]):
        total += values[index]
    return total


@unittest.skipUnless(jit.ENABLED, "numba is not in use")
class LazyKernelTests(unittest.TestCase):
    def test_a_stand_in_gives_the_plain_functions_answer_and_is_then_backed_by_a_dispatcher(self):
        values = numpy.arange(10.0)
        stand_in = jit.LazyKernel(_total, {})
        jit._LAZY.append(stand_in)
        self.assertIsNone(stand_in.dispatcher)
        self.assertEqual(stand_in(values), _total(values))
        self.assertIsNotNone(stand_in.dispatcher)
        self.assertIs(stand_in.py_func, _total)          # the dispatcher's attributes are reachable through it
        self.assertTrue(jit.numba_loaded())

    def test_a_kernel_made_after_numba_loaded_is_the_dispatcher_itself(self):
        jit.load_numba()
        self.assertNotIsInstance(jit.njit(_total), jit.LazyKernel)


class PlainSearchChoiceTests(unittest.TestCase):
    def test_the_first_searches_of_a_process_are_plain_python_and_later_ones_use_the_kernel(self):
        with mock.patch.object(jit, "numba_loaded", return_value=False), \
                mock.patch.object(routes_search, "_plain_searches", [0]):
            choices = [routes_search._search_in_plain_python(None)
                       for _search in range(routes_search.PLAIN_SEARCHES_BEFORE_KERNEL + 2)]
        self.assertEqual(choices, [True] * routes_search.PLAIN_SEARCHES_BEFORE_KERNEL + [False, False])

    def test_once_numba_is_loaded_every_search_uses_the_kernel(self):
        with mock.patch.object(jit, "numba_loaded", return_value=True), \
                mock.patch.object(routes_search, "_plain_searches", [0]):
            self.assertFalse(routes_search._search_in_plain_python(None))


class ProcessStartTests(unittest.TestCase):
    def test_agent_and_play_are_game_processes(self):
        self.assertTrue(process_start.is_game_process(["simulator.py", "agent", "--session", "x"]))
        self.assertTrue(process_start.is_game_process(["simulator.py", "play"]))

    def test_other_commands_and_a_bare_script_are_not(self):
        self.assertFalse(process_start.is_game_process(["simulator.py", "validate"]))
        self.assertFalse(process_start.is_game_process(["simulator.py"]))

    def test_finishing_a_command_that_is_not_a_game_process_returns(self):
        process_start.finish(["simulator.py", "validate"])      # a game process would end the interpreter here

    def test_loaded_freezes_and_re_enables_a_stopped_collector_and_leaves_a_running_one_alone(self):
        with mock.patch.object(gc, "isenabled", return_value=True), mock.patch.object(gc, "freeze") as freeze:
            process_start.loaded()
        freeze.assert_not_called()
        with mock.patch.object(gc, "isenabled", return_value=False), mock.patch.object(gc, "freeze") as freeze, \
                mock.patch.object(gc, "enable") as enable:
            process_start.loaded()
        freeze.assert_called_once_with()
        enable.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
