"""ActorWorld.copy_cost prices a project inside the view's table of shared answers, the same table for every ask of
that view, and leaves the game's own pricing outside any scope afterwards. The table's rules are
test_complaint_321_shared_project_bills."""
QUICK_TOPIC = True

import types
import unittest

from sim.actors.world import ActorWorld
from sim.engine import bridge_actors
from sim.engine.view_share import ViewShareMixin
from sim.tests.world_stand_in import fake_needs


class _Game(ViewShareMixin):
    """The parts of a Sim that pricing a project through a view touches."""

    def __init__(self):
        self.scopes_seen = []
        self.economy = types.SimpleNamespace(project_cost=self._project_cost)

    def _project_cost(self, node_id):
        self.scopes_seen.append(self._view_scope)
        if node_id == "broken":
            raise ValueError(node_id)
        return 12.5


def SimWorld(game):
    """The actors' world over the engine's own shared-answers scope (the bridge's view) and the game's project cost."""
    needs = fake_needs(shared_answers=lambda table: bridge_actors.shared_answers(game, table), project_cost=game.economy.project_cost)
    return ActorWorld(types.SimpleNamespace(needs=needs))


class CopyCostScopeTests(unittest.TestCase):
    def test_the_cost_is_the_games_project_cost(self):
        self.assertEqual(SimWorld(_Game()).copy_cost("iron_works"), 12.5)

    def test_the_cost_is_asked_inside_an_open_scope(self):
        game = _Game()
        SimWorld(game).copy_cost("iron_works")
        self.assertIsNotNone(game.scopes_seen[0])

    def test_every_ask_of_one_view_shares_one_table(self):
        game = _Game()
        world = SimWorld(game)
        world.copy_cost("iron_works")
        world.copy_cost("loom")
        self.assertIs(game.scopes_seen[0], game.scopes_seen[1])

    def test_two_views_do_not_share_a_table(self):
        game = _Game()
        SimWorld(game).copy_cost("iron_works")
        SimWorld(game).copy_cost("iron_works")
        self.assertIsNot(game.scopes_seen[0], game.scopes_seen[1])

    def test_no_scope_is_left_open_on_the_game_afterwards(self):
        game = _Game()
        SimWorld(game).copy_cost("iron_works")
        self.assertIsNone(game._view_scope)

    def test_no_scope_is_left_open_when_the_pricing_fails(self):
        game = _Game()
        with self.assertRaises(ValueError):
            SimWorld(game).copy_cost("broken")
        self.assertIsNone(game._view_scope)


if __name__ == "__main__":
    unittest.main()
