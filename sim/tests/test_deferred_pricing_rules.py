"""A game that loads a save without opening its economy counts the tree's money fields at the figure the save kept
(`opening_money.reprice_tree`, `saved_tree_pricing`), the same tree an opened game reaches; a save that never priced the tree
gives no figure. The load itself raising `EconomyNotOpened` on that is one line in `saveload._apply_blob`."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import opening_money


def tree():
    return {"node": {"rev_hours": 1.0, "up_hours": 2.0, "cap_hours": 5.0, "lab": {"farmer": 3.0}, "_material_hours": 4.0}}


def game(labour_figure):
    schedule = types.SimpleNamespace(money_per_labour_hour=None, wages_per_hour=lambda: {"farmer": 0.5})
    changes = []
    world = types.SimpleNamespace(
        nodes=tree(), start_civ={}, state=types.SimpleNamespace(economy=types.SimpleNamespace(nodes_money_per_labour_hour=None)),
        labour=types.SimpleNamespace(money_per_labour_hour=lambda: labour_figure), changes=changes,
        view=lambda name: (lambda: {}), _done_changed=lambda: changes.append("done"), _operating_changed=lambda: changes.append("operating"))
    return world, schedule


class RepriceTreeTest(unittest.TestCase):
    def reprice(self, world, schedule, figure=None):
        with mock.patch.object(opening_money, "build_schedule", lambda registry, civ: schedule):
            opening_money.reprice_tree(world, figure)

    def test_the_saved_figure_prices_the_tree_and_is_kept(self):
        world, schedule = game(labour_figure=99.0)
        self.reprice(world, schedule, 2.0)
        self.assertEqual(world.nodes["node"]["rev"], 2.0)
        self.assertEqual(world.state.economy.nodes_money_per_labour_hour, 2.0)
        self.assertEqual(world.changes, ["done", "operating"])

    def test_without_a_figure_the_labour_packages_figure_prices_it(self):
        world, schedule = game(labour_figure=3.0)
        self.reprice(world, schedule)
        self.assertEqual(world.nodes["node"]["rev"], 3.0)
        self.assertEqual(world.state.economy.nodes_money_per_labour_hour, 3.0)

    def test_a_game_given_the_saved_figure_reaches_the_tree_a_game_that_opened_reached(self):
        opened, schedule_opened = game(labour_figure=2.5)
        self.reprice(opened, schedule_opened)
        resumed, schedule_resumed = game(labour_figure=99.0)
        self.reprice(resumed, schedule_resumed, opened.state.economy.nodes_money_per_labour_hour)
        self.assertEqual(resumed.nodes, opened.nodes)
        self.assertEqual(resumed.state.economy.nodes_money_per_labour_hour, opened.state.economy.nodes_money_per_labour_hour)


class SavedPricingTest(unittest.TestCase):
    def test_a_priced_save_gives_its_figure(self):
        self.assertEqual(opening_money.saved_tree_pricing(True, 1.5), 1.5)

    def test_a_save_that_never_priced_the_tree_gives_none(self):
        self.assertIsNone(opening_money.saved_tree_pricing(False, 1.5))
        self.assertIsNone(opening_money.saved_tree_pricing(True, None))


if __name__ == "__main__":
    unittest.main()
