"""Complaints/416: moving the household's base takes the days of the fastest route over the modes
its people hold, not a straight-line pace."""
import random
import unittest

from sim import simulator
from sim.engine.core import Sim
from sim.geography import api as geography

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim(civ="rome_100ad"):
    return Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ(civ))


class RelocationFollowsFastestRouteTests(unittest.TestCase):

    def test_days_are_the_fastest_route_over_held_modes(self):
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

    def test_travel_tradition_does_not_shorten_the_journey(self):
        sim = _fresh_sim()
        target = max((tile for tile in sim.labour.settlement_tiles() if tile != sim.labour.base_tile()),
                     key=lambda tile: sim.labour.distance_to_tile_km(tile))
        before = sim.labour.relocation_quote(target)[0]
        sim.civ = dict(sim.civ, base_reach=6)
        self.assertAlmostEqual(sim.labour.relocation_quote(target)[0], before, places=9)

    def test_fastest_route_is_no_slower_than_the_cheapest(self):
        sim = _fresh_sim()
        base = sim.labour.base_tile()
        far = max((tile for tile in sim.labour.settlement_tiles() if tile != base),
                  key=lambda tile: sim.labour.distance_to_tile_km(tile))
        held = sim.labour.held_technologies()
        modes = geography.usable_modes([held])
        cheapest = geography.route([base], [far], modes, held_nodes=held)
        fastest = geography.route([base], [far], modes, held_nodes=held, fastest=True)
        self.assertLessEqual(fastest["days"], cheapest["days"] + 1e-9)


if __name__ == "__main__":
    unittest.main()
