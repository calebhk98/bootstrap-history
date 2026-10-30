"""SMOKE: the campaigns module run in a whole game. An army raised through the module's command marches on a tile held by a
rival, finds no defenders and takes it; the stability phase of the same years runs its risings. The rules are tested one
function at a time in test_campaigns_rules and the module's methods on plain views in test_campaigns_module."""
import unittest

from sim.campaigns.api import OrderArmy, RaiseArmy
from sim.land.api import TransferTile
from sim.tests.harness import unopened_sim

RIVAL = "rival_realm"


def neighbour_pair(game, home):
    """(a home tile, a tile within a short march of it that is not home's)."""
    modes = game.view("home_modes")()
    for tile in game.view("tiles_owned_by")[home]:
        near = sorted(game.view("reach_from")(tile, modes, 40.0).items(), key=lambda item: (item[1], item[0]))
        for other, days in near:
            if other != tile and game.view("tile_owner")[other] is None:
                return tile, other
    return None, None


class ACampaignInAWholeGame(unittest.TestCase):

    def setUp(self):
        self.game = unopened_sim(civ="rome_100ad")
        self.home = str(self.game.civ["id"])
        self.base, self.target = neighbour_pair(self.game, self.home)

    def test_an_army_raised_and_ordered_by_command_takes_an_undefended_tile_in_the_campaign_phase(self):
        self.assertIsNotNone(self.target, "the map has no free tile near a home tile")
        self.game.send(TransferTile(self.target, RIVAL, "set up"))
        army = self.game.send(RaiseArmy(self.home, 1000.0, self.base))
        self.assertEqual(army.owner, self.home)
        self.game.send(OrderArmy(self.home, army.army_id, self.target))
        self.game.step()
        self.assertEqual(self.game.view("tile_owner")[self.target], self.home)
        causes = [(event["kind"], event["cause"]) for event in self.game.view("world_events")()]
        self.assertIn(("tile_transfer", "conquest"), causes)
        self.assertIn(self.target, self.game.assembly.modules["campaigns"].world.held_since)


if __name__ == "__main__":
    unittest.main()
