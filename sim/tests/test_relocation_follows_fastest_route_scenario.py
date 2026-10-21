"""Complaints/416 through a game on the real map: the days of a relocation quote are the fastest route over the modes
the household holds, and a travel tradition does not shorten them. The rule is test_relocation_follows_fastest_route."""
import random
import unittest

from sim import simulator
from sim.engine.core import Sim
from sim.geography import api as geography

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim(civ="rome_100ad"):
    return Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ(civ))


class RelocationFollowsFastestRouteInAGame(unittest.TestCase):

    def test_days_are_the_fastest_route_over_held_modes_and_tradition_does_not_shorten_them(self):
        sim = _fresh_sim()
        labour = sim.labour
        base = labour.base_tile()
        far = max((tile for tile in labour.settlement_tiles() if tile != base),
                  key=lambda tile: labour.distance_to_tile_km(tile))
        held = labour.held_technologies()
        expected = geography.route([base], [far], geography.usable_modes([held]), held_nodes=held,
                                   fastest=True)
        days, _hours, _money = labour.relocation_quote(far)
        self.assertAlmostEqual(days, expected["days"], places=6)
        sim.civ = dict(sim.civ, base_reach=6)
        self.assertAlmostEqual(labour.relocation_quote(far)[0], days, places=9)


if __name__ == "__main__":
    unittest.main()
