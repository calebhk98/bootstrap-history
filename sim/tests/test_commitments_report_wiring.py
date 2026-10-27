"""Complaint 268: the `commitments` report lists the goals the player watches as its secondary goals, and says the formal goal
is still the one the score uses. `commitments_report` is called on a stand-in game with the watched rows replaced; what is
watched and how it is saved are test_ui_goals_watch and test_interface_slot_in_save."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.ui.proto import screen_commitments


def game():
    return types.SimpleNamespace(
        fog=False, goal="formal", goal_year=None, nodes={"formal": {"name": "The formal goal"}}, done=set(),
        view=lambda name: (lambda: {"reserve_craftsmen": 2, "reserve_scholars": 1}),
        policy={}, literacy=lambda metric: 0.1, literacy_ceiling_general=lambda: 0.4, literacy_ceiling_elite=lambda: 0.8)


def report(rows):
    with mock.patch.object(screen_commitments, "watched_rows", lambda sim: rows):
        return screen_commitments.commitments_report(game())


class CommitmentsReportTests(unittest.TestCase):
    def test_the_watched_goals_are_the_secondary_goals(self):
        rows = [{"id": "steam_engine", "name": "Steam engine"}]
        self.assertEqual(report(rows)["secondary_goals"], rows)

    def test_no_watched_goal_gives_an_empty_list(self):
        self.assertEqual(report([])["secondary_goals"], [])

    def test_the_formal_goal_and_the_reserve_are_read_from_the_game(self):
        reply = report([])
        self.assertEqual((reply["goal"]["id"], reply["goal"]["name"]), ("formal", "The formal goal"))
        self.assertEqual((reply["reserve"]["craftsmen"], reply["reserve"]["scholars"]), (2, 1))


if __name__ == "__main__":
    unittest.main()
