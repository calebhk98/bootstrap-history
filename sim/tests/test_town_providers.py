"""A registered town provider sets the size of a tile's town, bounded by the tile's people; None means no opinion.

Complaint 640: the town is read off the settlement mixin over a stand-in world that holds the nation's tiles and people,
so no game is built."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine import mod_code
from sim.engine.data import load_civ
from sim.geography.api import tiles_held
from sim.labour import town_providers
from sim.labour.labour_capacity import CapacityMixin
from sim.labour.labour_population import PopulationMixin
from sim.labour.labour_settlement import SettlementMixin
from sim.tests import harness  # noqa: F401  (isolates the home directory)

NAME = "test_acme_k3f9:towns"
NATION = 20.0e6


class Town(SettlementMixin):
    """The settlement mixin with the constants of the labour classes that surround it in a game."""

    TOWN_POPULATION_REFERENCE = PopulationMixin.TOWN_POPULATION_REFERENCE
    POP_SCALE_FLOOR_SHARE = CapacityMixin.POP_SCALE_FLOOR_SHARE
    POP_SCALE_VARIABLE_SHARE = CapacityMixin.POP_SCALE_VARIABLE_SHARE

    def __init__(self):
        homes = tuple(tiles_held(load_civ("rome_100ad")))
        household = types.SimpleNamespace(base_tile=None)
        self._world = types.SimpleNamespace(
            home_tiles_held=lambda: homes, population=types.SimpleNamespace(total=NATION), pop_scale=1.0,
            people_by_tile=lambda: None, state=types.SimpleNamespace(household=household))


class TownProviderTests(unittest.TestCase):
    def setUp(self):
        self.labour = Town()
        self.addCleanup(town_providers.PROVIDERS.clear)

    def test_no_provider_leaves_the_nominal_town(self):
        tile = self.labour.base_tile()
        nominal = self.labour._nominal_town_population()
        tile_people = self.labour.settlement_tiles()[tile]
        self.assertEqual(self.labour.home_town_population_estimate(),
                         min(nominal, tile_people * self.labour.TOWN_MAX_SHARE_OF_TILE))
        self.assertGreater(self.labour.home_town_population_estimate(), 0.0)

    def test_provider_sets_the_town_and_none_declines(self):
        tile = self.labour.base_tile()
        nominal = self.labour.home_town_population_estimate()
        mod_code.ModCodeApi("test_acme_k3f9").town_provider("towns", lambda labour, where, size: 0.5 * size)
        self.assertEqual(self.labour.home_town_population_estimate(), 0.5 * nominal)
        town_providers.PROVIDERS["test_acme_k3f9:zz_silent"] = lambda labour, where, size: None
        self.assertEqual(self.labour.home_town_population_estimate(), 0.5 * nominal)
        self.assertIn(tile, self.labour.settlement_tiles())

    def test_the_last_provider_in_name_order_that_answers_wins(self):
        town_providers.register_town_provider("a_first", lambda labour, where, size: 1.0)
        town_providers.register_town_provider("b_second", lambda labour, where, size: 2.0)
        self.assertEqual(self.labour.home_town_population_estimate(), 2.0)
        town_providers.register_town_provider("c_silent", lambda labour, where, size: None)
        self.assertEqual(self.labour.home_town_population_estimate(), 2.0)

    def test_provided_town_never_exceeds_the_tile_people(self):
        tile = self.labour.base_tile()
        people = self.labour.settlement_tiles()[tile]
        town_providers.register_town_provider(NAME, lambda labour, where, size: people * 10.0)
        self.assertEqual(self.labour.home_town_population_estimate(), people)

    def test_a_negative_answer_is_a_town_of_none(self):
        town_providers.register_town_provider(NAME, lambda labour, where, size: -5.0)
        self.assertEqual(self.labour.home_town_population_estimate(), 0.0)


if __name__ == "__main__":
    unittest.main()
