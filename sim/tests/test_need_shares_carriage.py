"""Carriage labour (sailors on hulls and boats) is part of the labour need of the goods people buy,
costed from the same physical freight inputs the route search uses, with no game built."""
import json
import os
import unittest

from sim.engine.catalog import load_production_catalog
from sim.engine.solve_prices_core import techniques_available_to
from sim.geography import api as geography
from sim.labour import workforce_carriage, workforce_spinup

QUICK_TOPIC = True

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)


def _civ(civ_id):
    with open(os.path.join(_ROOT, "data", "civilizations", civ_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


def _shares(reached, carriage=None):
    return workforce_spinup.need_shares_by_trade(
        _PRODUCTION, set(reached), techniques_available_to, carriage)


class CarriageEntersTheNeedTests(unittest.TestCase):

    def test_a_carriage_rate_gives_its_trade_a_share_and_none_means_none(self):
        reached = _civ("rome_100ad")["starting_techs"]
        self.assertEqual(_shares(reached).get("sailor", 0.0), 0.0)
        with_hulls = _shares(reached, {"sailor": 1.0})
        self.assertGreater(with_hulls["sailor"], 0.0)
        self.assertAlmostEqual(sum(with_hulls.values()), 1.0, places=9)

    def test_dearer_carriage_takes_more_of_the_need(self):
        reached = _civ("rome_100ad")["starting_techs"]
        self.assertGreater(_shares(reached, {"sailor": 2.0})["sailor"],
                           _shares(reached, {"sailor": 1.0})["sailor"])

    def test_carriage_hours_per_tonne_follow_the_modes_a_society_can_use(self):
        rome = workforce_carriage.carriage_hours_per_tonne_by_trade(_civ("rome_100ad")["starting_techs"])
        self.assertGreater(rome.get("sailor", 0.0), 0.0)
        self.assertNotIn("sailor", workforce_carriage.carriage_hours_per_tonne_by_trade([]))

    def test_the_hours_come_from_the_route_modes_physical_rates(self):
        rates = geography.carriage_rates(["sail", "foot"])
        self.assertEqual(rates["sail"]["crew_trade"], "sailor")
        self.assertGreater(rates["sail"]["crew_hours_per_tonne_km"], 0.0)
        self.assertIn("land", rates["foot"]["edge_classes"])

    def test_rome_sailors_get_a_real_share_from_its_known_modes(self):
        reached = _civ("rome_100ad")["starting_techs"]
        carriage = workforce_carriage.carriage_hours_per_tonne_by_trade(reached)
        self.assertGreater(_shares(reached, carriage)["sailor"], 0.001)


if __name__ == "__main__":
    unittest.main()
