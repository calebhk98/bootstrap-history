"""SCENARIO: a game's foreign route is the one haul function applied to the partner's tiles, the same function the
domestic haul uses. The leg-by-leg pricing rule over given rates is in `test_material_haul_legs` (Complaint 568),
and the carried-provisions rule in `test_freight_provisions`."""

QUICK_TOPIC = False

import unittest

from sim.engine import action_results
from sim.engine.data import load_civ
from sim.geography.api import tiles_held
from sim.tests import harness


class MaterialHaulLegs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.game = harness.unopened_sim()
        cls.imbalance = cls.game._domestic_flow_imbalance()
        cls.rates = cls.game._freight_mode_costs(cls.imbalance)

    def test_domestic_and_foreign_hauls_share_the_one_function(self):
        game = self.game
        partner = load_civ("han_china_100ad")
        foreign = game._foreign_route("han_china_100ad", 1.0)
        direct = game._haul_route(tiles_held(partner, game.world_map), 1.0, "goods",
                                  partner_techs=action_results.expand(game.nodes, frozenset(partner.get("starting_techs") or ())))
        self.assertEqual(foreign.legs, direct.legs)


if __name__ == "__main__":
    unittest.main()
