"""Complaint 603: `urban_people_by_tile` and `urban_fraction` read the civilisation's typed figure once, when the opening shares
are made, and afterwards only the food the towns can draw bounds the share; the shares are in the save. Each method is called on
a stand-in `self` carrying the people, the ceilings and the population; the rules are test_urban_share_rules."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.state import PopulationState, serialize_state
from sim.engine.urban_share import UrbanShareMixin

PEOPLE = {"port": 100000.0, "inland": 100000.0}
CEILINGS = {"port": 30000.0, "inland": 10000.0}


class Towns(UrbanShareMixin):
    """The parts of a Sim that the towns' people are read from."""

    def __init__(self, typed=0.1, ceilings=CEILINGS):
        self.civ = {"urban_fraction": typed}
        self.ceilings = ceilings
        self.population = types.SimpleNamespace(total=sum(PEOPLE.values()))
        self.state = types.SimpleNamespace(population=types.SimpleNamespace(urban_share_of_people={}))

    def _people_for_urban_share(self):
        return dict(PEOPLE)

    def urban_ceilings(self):
        return self.ceilings


class UrbanSharesTests(unittest.TestCase):
    def test_the_typed_figure_is_read_once_at_the_opening_and_not_again(self):
        game = Towns(typed=0.1)
        before = game.urban_fraction()
        game.civ["urban_fraction"] = 0.9
        self.assertAlmostEqual(game.urban_fraction(), before)
        self.assertAlmostEqual(before, 0.1)

    def test_the_opening_shares_are_kept_for_every_region(self):
        game = Towns()
        game.urban_people_by_tile()
        self.assertEqual(sorted(game.state.population.urban_share_of_people), ["inland", "port"])

    def test_a_poorer_surplus_shrinks_the_towns_once_the_shares_are_made(self):
        game = Towns(typed=0.1)
        before = game.urban_fraction()
        game.ceilings = {tile: 0.2 * people for tile, people in CEILINGS.items()}
        self.assertLess(game.urban_fraction(), before)

    def test_no_town_holds_more_people_than_it_can_feed(self):
        game = Towns(typed=0.2, ceilings={"port": 30000.0, "inland": 1000.0})
        urban = game.urban_people_by_tile()
        self.assertLessEqual(urban["inland"], 1000.0 + 1e-6)

    def test_a_nation_with_no_people_has_no_urban_share(self):
        game = Towns()
        game.population.total = 0.0
        self.assertEqual(game.urban_fraction(), 0.0)


class UrbanShareInSaveTests(unittest.TestCase):
    def test_the_shares_of_each_region_are_written_into_the_population_blob(self):
        population = PopulationState(urban_share_of_people={"port": 0.2, "inland": 0.05})
        self.assertEqual(serialize_state(population)["urban_share_of_people"], {"port": 0.2, "inland": 0.05})


if __name__ == "__main__":
    unittest.main()
