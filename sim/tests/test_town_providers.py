"""A provided town size sets the size of a tile's town, bounded by the tile's people; None means no opinion.

Complaint 640: the town is read off the settlement mixin over a stand-in world that holds the nation's tiles and people and
answers with the providers' answers, so no game is built. Which answer wins is `last_answer`, a plain function."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.assembly.api import NeedsAccess
from sim.engine import mod_code
from sim.engine.data import load_civ
from sim.geography.api import tiles_held
from sim.labour.labour_capacity import CapacityMixin
from sim.labour.labour_population import PopulationMixin
from sim.labour.labour_settlement import SettlementMixin
from sim.tests import harness  # noqa: F401  (isolates the home directory)
from sim.workforce.provided import last_answer

NATION = 20.0e6


class Town(SettlementMixin):
    """The settlement mixin with the constants of the labour classes that surround it in a game."""

    TOWN_POPULATION_REFERENCE = PopulationMixin.TOWN_POPULATION_REFERENCE
    POP_SCALE_FLOOR_SHARE = CapacityMixin.POP_SCALE_FLOOR_SHARE
    POP_SCALE_VARIABLE_SHARE = CapacityMixin.POP_SCALE_VARIABLE_SHARE

    def __init__(self):
        homes = tuple(tiles_held(load_civ("rome_100ad")))
        household = types.SimpleNamespace(base_tile=None)
        self.providers, self.premiums = [], []   # the functions the game's providers gave to the two points
        self._world = types.SimpleNamespace(
            provided_town_population=lambda tile, nominal: last_answer([function(tile, nominal) for function in self.providers]),
            has_town_premiums=lambda: bool(self.premiums),
            provided_mortality_premium=lambda tile, town: last_answer([function(tile, town) for function in self.premiums]),
            home_tiles_held=lambda: homes, population=types.SimpleNamespace(total=NATION), pop_scale=1.0,
            people_by_tile=lambda: None, workforce=household, view=workforce_stand_in.view_of(household))


class TownProviderTests(unittest.TestCase):
    def setUp(self):
        self.labour = Town()

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
        self.labour.providers.append(lambda where, size: 0.5 * size)
        self.assertEqual(self.labour.home_town_population_estimate(), 0.5 * nominal)
        self.labour.providers.append(lambda where, size: None)
        self.assertEqual(self.labour.home_town_population_estimate(), 0.5 * nominal)
        self.assertIn(tile, self.labour.settlement_tiles())

    def test_the_last_answer_that_is_not_none_wins(self):
        self.assertEqual(last_answer([1.0, 2.0, None]), 2.0)
        self.assertIsNone(last_answer([None, None]))
        self.assertIsNone(last_answer([]))

    def test_the_mod_door_records_the_function_as_an_answer_to_the_point(self):
        api = mod_code.ModCodeApi("test_acme_k3f9")
        function = lambda where, size: 0.5 * size
        api.town_provider("towns", function)
        self.assertEqual(api.operations.provided["town_population"], (NeedsAccess(function),))
        self.assertNotIn("town_mortality_premium", api.operations.provided)

    def test_provided_town_never_exceeds_the_tile_people(self):
        tile = self.labour.base_tile()
        people = self.labour.settlement_tiles()[tile]
        self.labour.providers.append(lambda where, size: people * 10.0)
        self.assertEqual(self.labour.home_town_population_estimate(), people)

    def test_a_negative_answer_is_a_town_of_none(self):
        self.labour.providers.append(lambda where, size: -5.0)
        self.assertEqual(self.labour.home_town_population_estimate(), 0.0)


if __name__ == "__main__":
    unittest.main()
