"""SMOKE: a stepped fixture economy whose households hold no land and grow a crop that needs a tool. Every plot is held
by a landlord with no hands; each cohort leases what its floor needs (land_lease_year) and grows its food on the leased
land, by hand since nobody holds a hoe (plot_means). The rules are tested one function at a time in
test_economy_land_lease_year, test_economy_land_tenancy and test_economy_plot_means."""
import unittest

from sim.economy import titles_worked
from sim.economy.fixture_setups import GRAIN, plot_tool_setup
from sim.tests.economy_fixture import Economy, quiet_year

LANDLORD = "firm:landlord"
YEARS = 3


def step_landless_economy():
    setup = plot_tool_setup()
    economy = Economy(setup)
    for tile in list(economy.record.land.titles):
        economy.record.land.titles[tile] = {LANDLORD: 1.0}        # no cohort holds any land
    outcomes = [economy.step(quiet_year(setup)) for _year in range(YEARS)]
    return economy, outcomes


class LandlessCohortsInAStepFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.economy, cls.outcomes = step_landless_economy()

    def test_every_cohort_holds_a_tenancy_from_the_landlord(self):
        record = self.economy.record
        for cohort_id in sorted(record.cohorts):
            tile = record.cohorts[cohort_id].tile
            self.assertGreater(titles_worked.worked_share(record, tile, cohort_id), 0.0, cohort_id)
            self.assertIn((cohort_id, LANDLORD), [(row["tenant"], row["lessor"]) for row in record.land.tenancies[tile]])

    def test_each_cohort_works_hectares_it_was_never_given(self):
        held = self.economy.hectares_held()
        self.assertEqual(sorted(held), sorted(self.economy.record.cohorts))
        self.assertTrue(all(hectares > 0.0 for hectares in held.values()))

    def test_the_leased_plots_grow_the_food(self):
        accounts = self.outcomes[-1].accounts
        self.assertGreater(accounts.goods[GRAIN].production_grown, 0.0)
        for cohort in accounts.cohorts:
            self.assertAlmostEqual(cohort.own_plot_per_head, cohort.need_per_head, msg=cohort.cohort)

    def test_the_landlord_holds_less_than_the_whole_tile_once_it_has_let_land(self):
        record = self.economy.record
        for tile in sorted(record.land.titles):
            let = sum(row["share"] for row in record.land.tenancies[tile])
            self.assertGreater(let, 0.0, tile)
            self.assertLess(let, 1.0, tile)


if __name__ == "__main__":
    unittest.main()
