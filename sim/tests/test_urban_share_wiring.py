"""Complaint 603: `urban_people_by_tile` and `urban_fraction` read the civilisation's typed figure once, when the opening shares
are made, and afterwards only the food the towns can draw bounds the share; the shares are in the save. Each is called on the
demography module with the people and the ceilings stood in and the civilisation as a view; the rules are test_urban_share_rules."""
QUICK_TOPIC = True

import unittest

from sim.demography.module import Demography
from sim.demography.state import DemographyWorld
from sim.engine.state import serialize_state
from sim.tests import module_harness

PEOPLE = {"port": 100000.0, "inland": 100000.0}
CEILINGS = {"port": 30000.0, "inland": 10000.0}


class Towns(Demography):
    """The module with the people by tile and the towns' ceilings stood in."""
    ceilings = CEILINGS

    def people_for_urban_share(self):
        return dict(PEOPLE)

    def urban_ceilings(self):
        return self.ceilings


def towns(typed=0.1, ceilings=CEILINGS):
    civilisation = {"urban_fraction": typed}
    module = module_harness.build(Towns, views={"civilisation": civilisation}, world=DemographyWorld(pop_working_age=sum(PEOPLE.values())))
    module.ceilings = ceilings
    module.civilisation = civilisation
    return module


class UrbanSharesTests(unittest.TestCase):
    def test_the_typed_figure_is_read_once_at_the_opening_and_not_again(self):
        module = towns(typed=0.1)
        before = module.urban_fraction()
        module.civilisation["urban_fraction"] = 0.9
        self.assertAlmostEqual(module.urban_fraction(), before)
        self.assertAlmostEqual(before, 0.1)

    def test_the_opening_shares_are_kept_for_every_region(self):
        module = towns()
        module.urban_people_by_tile()
        self.assertEqual(sorted(module.world.urban_share_of_people), ["inland", "port"])

    def test_a_poorer_surplus_shrinks_the_towns_once_the_shares_are_made(self):
        module = towns(typed=0.1)
        before = module.urban_fraction()
        module.ceilings = {tile: 0.2 * people for tile, people in CEILINGS.items()}
        self.assertLess(module.urban_fraction(), before)

    def test_no_town_holds_more_people_than_it_can_feed(self):
        module = towns(typed=0.2, ceilings={"port": 30000.0, "inland": 1000.0})
        urban = module.urban_people_by_tile()
        self.assertLessEqual(urban["inland"], 1000.0 + 1e-6)

    def test_a_nation_with_no_people_has_no_urban_share(self):
        module = towns()
        module.world.pop_working_age = 0.0
        self.assertEqual(module.urban_fraction(), 0.0)


class UrbanShareInSaveTests(unittest.TestCase):
    def test_the_shares_of_each_region_are_written_into_the_world_blob(self):
        world = DemographyWorld(urban_share_of_people={"port": 0.2, "inland": 0.05})
        self.assertEqual(serialize_state(world)["urban_share_of_people"], {"port": 0.2, "inland": 0.05})


if __name__ == "__main__":
    unittest.main()
