"""Complaint 648: the hooks a battle and a conquest call add captives to the winner's bonded stratum, log what was taken
with the winner first and the cause, and take nothing from a tile the loser does not hold or a loser with no state.
The shares are the agents' rules (test_bonded_purchase). CaptivesMixin on a stand-in game."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents import api as agents_api
from sim.engine import captives
from sim.engine.captives import CaptivesMixin


class _Game(CaptivesMixin):

    def __init__(self, loser_tiles=("t1", "t2"), loser_has_state=True, population=1000.0):
        self.actors = object()
        self._tiles = list(loser_tiles)
        self._has_state = loser_has_state
        self._population = population

    def tiles_owned_by(self, owner):
        return self._tiles

    def owner_has_state(self, owner):
        return self._has_state

    def owner_world(self, owner):
        return types.SimpleNamespace(population_total=lambda: self._population)


class CaptivesFromABattle(unittest.TestCase):

    def test_the_winner_takes_a_share_of_the_losses_and_the_log_names_both_sides_and_the_cause(self):
        game = _Game()
        with mock.patch.object(captives.agents_api, "add_captives", lambda actors, winner, people: people) as taker, \
                mock.patch.object(captives.world_events, "record") as record:
            taken = game.take_captives_from_battle("rome", "han", 1000.0, "t1")
        self.assertAlmostEqual(taken, agents_api.captives_from_losses(1000.0))
        record.assert_called_once_with(game, "captives", actors=["rome", "han"], tiles=["t1"], cause="battle", people=taken)

    def test_no_losses_take_no_captives_and_log_nothing(self):
        with mock.patch.object(captives.world_events, "record") as record:
            self.assertEqual(_Game().take_captives_from_battle("rome", "han", 0.0, "t1"), 0.0)
        record.assert_not_called()

    def test_a_winner_with_no_bonded_stratum_takes_none_and_logs_nothing(self):
        with mock.patch.object(captives.agents_api, "add_captives", lambda actors, winner, people: 0.0), \
                mock.patch.object(captives.world_events, "record") as record:
            self.assertEqual(_Game().take_captives_from_battle("rome", "han", 1000.0, "t1"), 0.0)
        record.assert_not_called()


class CaptivesFromAConquest(unittest.TestCase):

    def test_a_conquered_tile_gives_a_share_of_the_people_standing_on_it(self):
        game = _Game(population=2000.0)
        with mock.patch.object(captives.settlement, "population_share", lambda owned, tile: 0.25), \
                mock.patch.object(captives.agents_api, "add_captives", lambda actors, winner, people: people), \
                mock.patch.object(captives.world_events, "record") as record:
            taken = game.take_captives_from_conquest("rome", "han", "t1")
        self.assertAlmostEqual(taken, agents_api.captives_from_conquest(500.0))
        self.assertEqual(record.call_args.kwargs["cause"], "conquest")
        self.assertEqual(record.call_args.kwargs["actors"], ["rome", "han"])

    def test_a_tile_the_loser_does_not_hold_gives_nothing(self):
        self.assertEqual(_Game().take_captives_from_conquest("rome", "han", "elsewhere"), 0.0)

    def test_a_loser_with_no_state_gives_nothing(self):
        self.assertEqual(_Game(loser_has_state=False).take_captives_from_conquest("rome", "han", "t1"), 0.0)


if __name__ == "__main__":
    unittest.main()
