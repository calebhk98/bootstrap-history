"""keep <id> staffed: the command's flag, and the hires the yearly pass makes from what the projects module names."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.labour import labour_staff_controls
from sim.labour.labour_staff_controls import StaffControlsMixin
from sim.projects.api import KeepStaffed
from sim.tests import projects_host
from sim.ui.proto.dispatch_staff_controls import _cmd_keep
from sim.tests.ui_stand_in import Game


def keeping(done=("mill",), venture=True):
    module = projects_host.build()
    projects = Game(done=set(done))
    return Game(
        done=set(done), projects=projects, is_venture=lambda node_id: venture, module=module,
        keep_staffed=module.seat.keep_staffed, view=lambda name: module.keep_staffed,
        send=lambda command: module.apply_keep_staffed(command))


class KeepCommand(unittest.TestCase):

    def test_keep_flags_a_concern_you_know_and_off_clears_it(self):
        game = keeping()
        self.assertTrue(_cmd_keep(game, {}, {"id": "mill"}, None)["ok"])
        self.assertEqual(game.keep_staffed, {"mill"})
        self.assertTrue(_cmd_keep(game, {}, {"id": "mill", "staffed": "off"}, None)["ok"])
        self.assertEqual(game.keep_staffed, set())

    def test_bare_keep_lists_what_is_flagged(self):
        game = keeping()
        game.keep_staffed.update({"b", "a"})
        self.assertEqual(_cmd_keep(game, {}, {}, None)["keep_staffed"], ["a", "b"])

    def test_a_concern_you_do_not_know_or_that_is_not_a_concern_is_refused_and_not_flagged(self):
        for game in (keeping(done=()), keeping(venture=False)):
            self.assertFalse(_cmd_keep(game, {}, {"id": "mill"}, None)["ok"])
            self.assertEqual(game.keep_staffed, set())


class Household(StaffControlsMixin):
    def __init__(self, hires):
        self.hired = []
        self._world = Game(keep_staffed_hires=lambda: hires)

    def hire_to_cover(self, trade, count, why, partial=False):
        self.hired.append((trade, count, why))


class FlaggedConcerns(unittest.TestCase):

    def test_nothing_to_hire_hires_nobody(self):
        game = Household({})
        game.keep_flagged_concerns_staffed()
        self.assertEqual(game.hired, [])

    def test_each_resource_the_projects_module_names_is_hired_as_its_trade(self):
        game = Household({"craftsmen": 2})
        with mock.patch.object(labour_staff_controls.trade_data, "staff_resource_trade", lambda registry, resource: "artisan"), \
                mock.patch.object(labour_staff_controls.trade_data, "registry_of", lambda world: {}):
            game.keep_flagged_concerns_staffed()
        self.assertEqual(game.hired, [("artisan", 2, "keep_staffed")])


class ProjectsView(unittest.TestCase):

    def test_a_flagged_running_concern_asks_for_the_craftsmen_its_hands_exceed_the_household_by(self):
        module = projects_host.build(
            tree_nodes={"mill": {"rev": 10.0, "up": 1.0}}, techniques_held=frozenset({"mill"}), operating=frozenset({"mill"}),
            venture_hands={"mill": (0.0, 6.0)}, institution_units={"mill": 1.0}, venture_foreman={"mill": (None, 0.0)},
            venture_garrison=lambda node_id, units: {}, effective_scholars=0.0, reopen_units={"mill": 1.0})
        module.seat.keep_staffed.add("mill")
        hires = module.keep_staffed_hires()
        self.assertEqual(list(hires), ["craftsmen"])
        self.assertGreater(hires["craftsmen"], 0)

    def test_nothing_flagged_asks_for_nobody(self):
        self.assertEqual(projects_host.build().keep_staffed_hires(), {})


if __name__ == "__main__":
    unittest.main()
