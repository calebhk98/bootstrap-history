"""keep <id> staffed: the command's flag, which flagged concerns count, and what the yearly pass asks to be hired."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.labour import labour_staff_controls
from sim.labour.labour_staff_controls import StaffControlsMixin
from sim.ui.proto.dispatch_staff_controls import _cmd_keep


def keeping(done=("mill",), venture=True):
    projects = types.SimpleNamespace(done=set(done), keep_staffed=set())
    return types.SimpleNamespace(state=types.SimpleNamespace(projects=projects), is_venture=lambda node_id: venture)


class KeepCommand(unittest.TestCase):

    def test_keep_flags_a_concern_you_know_and_off_clears_it(self):
        game = keeping()
        self.assertTrue(_cmd_keep(game, {}, {"id": "mill"}, None)["ok"])
        self.assertEqual(game.state.projects.keep_staffed, {"mill"})
        self.assertTrue(_cmd_keep(game, {}, {"id": "mill", "staffed": "off"}, None)["ok"])
        self.assertEqual(game.state.projects.keep_staffed, set())

    def test_bare_keep_lists_what_is_flagged(self):
        game = keeping()
        game.state.projects.keep_staffed.update({"b", "a"})
        self.assertEqual(_cmd_keep(game, {}, {}, None)["keep_staffed"], ["a", "b"])

    def test_a_concern_you_do_not_know_or_that_is_not_a_concern_is_refused_and_not_flagged(self):
        for game in (keeping(done=()), keeping(venture=False)):
            self.assertFalse(_cmd_keep(game, {}, {"id": "mill"}, None)["ok"])
            self.assertEqual(game.state.projects.keep_staffed, set())


class Household(StaffControlsMixin):
    def __init__(self, flagged, operating, closure_age, shortfalls, draws):
        projects = types.SimpleNamespace(keep_staffed=set(flagged), done={"a", "b", "c"}, operating=set(operating))
        self.hired = []
        self._world = types.SimpleNamespace(
            state=types.SimpleNamespace(projects=projects), nodes={"a": 1, "b": 1, "c": 1},
            staff_closure_age=lambda node_id: closure_age.get(node_id), staffing_held_totals=lambda: {},
            staffing_draw_of=lambda node_id, units: draws[node_id], reopen_units=lambda node_id: 1,
            staffing_shortfalls=lambda totals, strict=False: shortfalls)

    def hire_to_cover(self, trade, count, why, partial=False):
        self.hired.append((trade, count, why))


class FlaggedConcerns(unittest.TestCase):

    def test_a_flagged_concern_counts_when_running_or_shut_for_want_of_staff_and_not_otherwise(self):
        game = Household(["a", "b", "c"], operating={"a"}, closure_age={"b": 2}, shortfalls={}, draws={})
        self.assertEqual(game.keep_staffed_concerns(), ["a", "b"])

    def test_nothing_flagged_hires_nobody(self):
        game = Household([], set(), {}, {"craftsmen": 3.0}, {})
        game.keep_flagged_concerns_staffed()
        self.assertEqual(game.hired, [])

    def test_the_shortfall_is_hired_for_up_to_what_the_flagged_concerns_hold(self):
        game = Household(["a"], {"a"}, {}, shortfalls={"craftsmen": 5.0}, draws={"a": {"craftsmen": 2.0}})
        with mock.patch.object(labour_staff_controls.trade_data, "staff_resource_trade", lambda registry, resource: "artisan"), \
                mock.patch.object(labour_staff_controls.trade_data, "registry_of", lambda world: {}):
            game.keep_flagged_concerns_staffed()
        self.assertEqual(game.hired, [("artisan", 2, "keep_staffed")])

    def test_no_shortfall_hires_nobody(self):
        game = Household(["a"], {"a"}, {}, shortfalls={}, draws={"a": {"craftsmen": 2.0}})
        with mock.patch.object(labour_staff_controls.trade_data, "registry_of", lambda world: {}):
            game.keep_flagged_concerns_staffed()
        self.assertEqual(game.hired, [])


if __name__ == "__main__":
    unittest.main()
