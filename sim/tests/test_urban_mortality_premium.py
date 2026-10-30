"""A town's mortality premium reaches deaths through `Population.step` and through the town providers (Complaint 634).

The premium is a share added to the baseline death rate of every band; the providers give it for a town, and the
settlement mixin averages it over the tile's people. Each rule is called with built inputs."""
QUICK_TOPIC = True

import unittest

from sim.assembly.api import NeedsAccess
from sim.engine import mod_code
from sim.tests.test_town_providers import Town
from sim.workforce.provided import last_answer
from sim.world.demography import Population

PEOPLE = (30000.0, 60000.0, 10000.0)


FOOD_AT_SUBSISTENCE = 183700000.0   # calories a day that feed these people exactly: nutrition ratio of one


def one_year(premium=None):
    people = Population(*PEOPLE, seed=1)
    if premium is None:
        return people.step(FOOD_AT_SUBSISTENCE)
    return people.step(FOOD_AT_SUBSISTENCE, urban_mortality_premium=premium)


class PopulationStep(unittest.TestCase):
    def test_no_premium_is_the_unchanged_step(self):
        self.assertEqual(one_year(0.0), one_year())

    def test_the_premium_raises_baseline_deaths_in_every_band_by_that_share(self):
        plain, urban = one_year(), one_year(0.25)
        for band in ("deaths_children", "deaths_working_age", "deaths_elderly"):
            self.assertAlmostEqual(getattr(urban, band), getattr(plain, band) * 1.25, places=6, msg=band)

    def test_deaths_never_exceed_the_band(self):
        flows = one_year(1.0e9)
        self.assertLessEqual(flows.deaths_children, PEOPLE[0])
        self.assertLessEqual(flows.deaths_working_age, PEOPLE[1])
        self.assertLessEqual(flows.deaths_elderly, PEOPLE[2])

    def test_accounting_still_closes(self):
        flows = one_year(0.5)
        self.assertAlmostEqual(flows.start_total + flows.births - flows.deaths, flows.end_total, places=6)


class TownPremium(unittest.TestCase):
    def setUp(self):
        self.labour = Town()

    def test_no_provider_gives_no_premium_anywhere(self):
        self.assertEqual(self.labour.town_mortality_premium_by_tile(), {})

    def test_a_town_premium_is_spread_over_the_tiles_people(self):
        tile = self.labour.base_tile()
        town = self.labour.home_town_population_estimate()
        people = self.labour.settlement_tiles()[tile]
        self.labour.premiums.append(lambda where, size: 0.5 if where == tile else None)
        found = self.labour.town_mortality_premium_by_tile()
        self.assertEqual(set(found), {tile})
        self.assertAlmostEqual(found[tile], 0.5 * town / people, places=9)

    def test_the_mod_door_records_both_the_size_and_the_premium(self):
        api = mod_code.ModCodeApi("test_acme_k3f9")
        size, premium = (lambda where, size: 0.5 * size), (lambda where, size: 0.2)
        api.town_provider("towns", size, mortality_premium=premium)
        self.assertEqual((api.operations.provided["town_population"], api.operations.provided["town_mortality_premium"]),
                         ((NeedsAccess(size),), (NeedsAccess(premium),)))

    def test_a_negative_premium_counts_as_none(self):
        self.assertEqual(last_answer([-1.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
