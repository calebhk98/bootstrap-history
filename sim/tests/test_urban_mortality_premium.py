"""A town's mortality premium reaches deaths through `Population.step` and through the town providers (Complaint 634).

The premium is a share added to the baseline death rate of every band; the providers give it for a town, and the
settlement mixin averages it over the tile's people. Each rule is called with built inputs."""
QUICK_TOPIC = True

import unittest

from sim.engine import mod_code
from sim.labour import town_providers
from sim.tests.test_town_providers import Town
from sim.world.demography import Population

PEOPLE = (30000.0, 60000.0, 10000.0)


FOOD_AT_SUBSISTENCE = 183700000.0   # calories a day that feed these people exactly: nutrition ratio of one
advance_one_year = Population.step   # the function under test, called on a population built here


def one_year(premium=None):
    people = Population(*PEOPLE, seed=1)
    if premium is None:
        return advance_one_year(people, FOOD_AT_SUBSISTENCE)
    return advance_one_year(people, FOOD_AT_SUBSISTENCE, urban_mortality_premium=premium)


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
        self.addCleanup(town_providers.PROVIDERS.clear)
        self.addCleanup(town_providers.PREMIUMS.clear)

    def test_no_provider_gives_no_premium_anywhere(self):
        self.assertEqual(self.labour.town_mortality_premium_by_tile(), {})

    def test_a_town_premium_is_spread_over_the_tiles_people(self):
        tile = self.labour.base_tile()
        town = self.labour.home_town_population_estimate()
        people = self.labour.settlement_tiles()[tile]
        town_providers.register_town_premium("test_acme_k3f9:premium", lambda labour, where, size: 0.5 if where == tile else None)
        found = self.labour.town_mortality_premium_by_tile()
        self.assertEqual(set(found), {tile})
        self.assertAlmostEqual(found[tile], 0.5 * town / people, places=9)

    def test_the_mod_door_registers_both_the_size_and_the_premium(self):
        mod_code.ModCodeApi("test_acme_k3f9").town_provider("towns", lambda labour, where, size: 0.5 * size,
                                                            mortality_premium=lambda labour, where, size: 0.2)
        self.assertIn("test_acme_k3f9:towns", town_providers.PROVIDERS)
        self.assertEqual(town_providers.provided_mortality_premium(self.labour, "x", 10.0), 0.2)

    def test_a_negative_premium_counts_as_none(self):
        town_providers.register_town_premium("test_acme_k3f9:premium", lambda labour, where, size: -1.0)
        self.assertEqual(town_providers.provided_mortality_premium(self.labour, "x", 10.0), 0.0)


if __name__ == "__main__":
    unittest.main()
